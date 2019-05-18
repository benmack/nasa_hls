from bs4 import BeautifulSoup
import datetime
import fnmatch
import numpy as np
import pandas as pd
import rasterio
import requests
from subprocess import Popen, PIPE
from tqdm import tqdm
import urllib
import warnings

BAND_NAMES = {'S30': {'Coastal_Aerosol': 'B01',
                      'Blue': 'B02',
                      'Green': 'B03',
                      'Red': 'B04',
                      'Red_Edge1': 'B05',
                      'Red_Edge3': 'B07',
                      'NIR_Broad': 'B08',
                      'NIR_Narrow': 'B8A',
                      'Cirrus': 'B10',
                      'SWIR1': 'B11',
                      'SWIR2': 'B12',
                      'QA': 'QA'},
              'L30': {'Coastal_Aerosol': 'band01',
                      'Blue': 'band02',
                      'Green': 'band03',
                      'Red': 'band04',
                      'NIR': 'band05',
                      'SWIR1': 'band06',
                      'SWIR2': 'band07',
                      'Cirrus': 'band09',
                      'TIRS1': 'band10',
                      'TIRS2': 'band11',
                      'QA': 'QA'}}

QA_ATTRIBUTES_SHORT = ['a_clima',
                       'a_low',
                       'a_avg',
                       'a_high',
                       'water',
                       'snow',
                       'cloud_shadow',
                       'adj_cloud',
                       'cloud',
                       'cirrus',
                       'no_water',
                       'no_snow',
                       'no_cloud_shadow',
                       'no_adj_cloud',
                       'no_cloud',
                       'no_cirrus']

QA_ATTRIBUTES_SHORT = ['Aerosol Quality Climatology',
                      'Aerosol Quality Low',
                      'Aerosol Quality Average',
                      'Aerosol Quality  High',
                      'Water',
                      'Snow/ice',
                      'Cloud shadow',
                      'Adjacent cloud',
                      'Cloud',
                      'Cirrus',
                      'No water',
                      "No snow/ice",
                      "No cloud shadow",
                      "No adjacent cloud",
                      "No cloud",
                      "No cirrus"]


def get_qa_look_up_table():
    """Get a dataframe with all QA values, binary strings and to which QA attributes they resolve."""
    def bit_num_to_str_idx(bit_number, n_total_bits=8):
        """Get the index of bit(s) in a binary string given the bit number."""
        string_indices = list(range(n_total_bits-1, -1, -1))
        if isinstance(bit_number, list):
            str_idx = [string_indices[bn] for bn in bit_number]
        else:
            str_idx = string_indices[bit_number]
        return str_idx

    lut_qa = pd.DataFrame({"qa_value": list(range(256)),
                       "binary_string": ["{0:08b}".format(i) for i in range(256)]})

    # # define a LUT dictionary for each bit combination
    # 1) the 2-bit combinations and the '1' cases of the single cases 
    lut_bits = {"a_clima": {"bit_combination":"00",
                            "bit_number": [7, 6]},
                "a_low": {"bit_combination":"01",
                          "bit_number": [7, 6]},
                "a_avg": {"bit_combination":"10",
                          "bit_number": [7, 6]},
                "a_high": {"bit_combination":"11",
                           "bit_number": [7, 6]},
                "water": {"bit_combination":"1",
                          "bit_number": 5},
                "snow": {"bit_combination":"1",
                         "bit_number": 4},
                "cloud_shadow": {"bit_combination":"1",
                                 "bit_number": 3},
                "adj_cloud": {"bit_combination":"1",
                              "bit_number": 2},
                "cloud": {"bit_combination":"1",
                          "bit_number": 1},
                "cirrus": {"bit_combination":"1",
                           "bit_number": 0},
                }
    # 2 a) get the string indices 
    # bit number -> string indices, e.g. [7, 6] -> [0, 1])
    #                                    0 -> 7
    # 2 b) get definition of the '0' cases of single bit combinations
    # the 2-bit combinations and the true cases of the single cases 
    for key in list(lut_bits.keys()):
        lut_bits[key]["string_index"] = bit_num_to_str_idx(lut_bits[key]["bit_number"], n_total_bits=8)
        if not isinstance(lut_bits[key]["bit_number"], list):
            key_opposite = "no_" + key
            lut_bits[key_opposite] = lut_bits[key].copy()
            lut_bits[key_opposite]["bit_combination"] = "0"

    # now we can create a column for each possible QA attribute
    for key in lut_bits.keys():
        if isinstance(lut_bits[key]["string_index"], list):
            tmp_col = lut_qa.binary_string.str[lut_bits[key]["string_index"][0] : lut_bits[key]["string_index"][1]+1]
            new_col = tmp_col == lut_bits[key]["bit_combination"]
            del tmp_col
        else:
            new_col = lut_qa.binary_string.str[lut_bits[key]["string_index"]] == lut_bits[key]["bit_combination"]
        lut_qa.loc[:, key] = new_col
        del new_col
    return lut_qa

def hls_qa_layer_to_mask(qa_path, 
                         qa_valid,
                         keep_255=True,
                         mask_path=None, 
                         overwrite=False):
    """Derive a mask from a binary encoded QA raster.
    
    Arguments:
        qa_path {str} -- Path to the single band HLS QA layer GeoTiFF.
        qa_valid {str} -- QA values to be considered valid in the QA layer. 
            they will be 1 in the output array/GeoTiFF. Other values will be 0.
    
    Keyword Arguments:
        keep_255 {bool} -- If ``True`` the 255 value 
            (i.e. the not sensed or off-footprint pixels) from the input raster is 
            still 255 in the result. (default: {True})
        mask_path {str} -- Path for writing the mask to a GeoTiFF. 
            If ``None`` nothing will be written to a file.
            An array will be returned instead. (default: {None})
        overwrite {bool} -- Overwrite the ``mask_path`` in case it exists?
            Else the processing is skipped.
            Only applies if ``mask_path`` is not ``None``. (default: {False})
    
    Returns:
        array or 0 -- Array if ``mask_path`` is given, else an array. 
    """
    if mask_path is not None:
        if mask_path.exists() and not overwrite:
            print("Processing skipped. File exists.")
            return 0
    
    with rasterio.open(qa_path) as qa:
        meta = qa.meta
        qa_array = qa.read()

    clear_array = np.zeros_like(qa_array)
    for num in qa_valid:
        clear_array[qa_array == num] = 1
    if keep_255:
        clear_array[qa_array == 255] = 255
    
    if mask_path is not None:
        meta.update(compress="lzw")
        with rasterio.open(mask_path, "w", **meta) as dst:
            dst.write(clear_array)
        return 0
    else:
        return clear_array[0, :, :]

def get_metadata_from_hdf(src, fields=["cloud_cover", "spatial_coverage"]):
    """Get metadata from a nasa-hls hdf file. See HLS user guide for valid fields.
    
    HLS User Guide - see Section 6.6: 
    
    https://hls.gsfc.nasa.gov/wp-content/uploads/2019/01/HLS.v1.4.UserGuide_draft_ver3.1.pdf
    """
    band="QA"
    cmd = f"gdalinfo HDF4_EOS:EOS_GRID:'{src}':Grid:{band}"
    p = Popen(cmd, stdout=PIPE, shell=True)
    output, err = p.communicate()
    output = str(output)[2:-1].replace("\\n", "\n")
    rc = p.returncode
    metadata = {}
    for line in output.split("\n"):
        for field in fields:
            if field in line:
                metadata[field] = line.split("=")[1].strip()
                try:
                    metadata[field] = float(metadata[field])
                except:
                    pass
    for field in fields:
        if field not in metadata.keys():
            warnings.warn(f"Could not find metadata for field '{field}'.")
    return metadata

def get_cloud_coverage_from_hdf(src):
    """Get the cloud coverage from the metadata of a nasa-hls hdf file.
    """
    band="QA"
    cmd = f"gdalinfo HDF4_EOS:EOS_GRID:'{src}':Grid:{band}"
    p = Popen(cmd, stdout=PIPE, shell=True)
    output, err = p.communicate()
    output = str(output)[2:-1].replace("\\n", "\n")
    rc = p.returncode
    cloud_coverage = None
    for line in output.split("\n"):
        if "cloud_coverage" in line:
            cloud_coverage = float(line.split("=")[1].strip())
    if cloud_coverage is None:
        raise Exception("Could not derive cloud cover.")
    return cloud_coverage

def get_available_tiles_from_url(
        url_tiles="https://hls.gsfc.nasa.gov/wp-content/uploads/2018/10/HLS_Sentinel2_Granule.csv"):
    txt = urllib.request.urlopen(url_tiles).read()
    tiles = str(txt)[2:-5].split("\\r\\n")
    return tiles

def parse_url(date,
              tile="33UUU",
              product="S30",
              version="v1.4"):
    """Download a HLS dataset from https://hls.gsfc.nasa.gov/data/.

    :param date: A date in one of the following supported formats: '%Y-%m-%d', '%Y%m%d', %Y%j'.
    :param tile: Tile name of the HLS = Sentinel2 tiling system
        (see https://hls.gsfc.nasa.gov/products-description/tiling-system/).
    :param product: Download Landsat (use 'L30') or Sentinel-2 (use 'S30') data.
    :param version: Product version, at the time writing there was only 'v1.4' available.
    :return: The dataset URL.
    """
    base_url = "https://hls.gsfc.nasa.gov/data"

    date_yyyydoy = convert_date_to_Yj(date)
    year = date_yyyydoy[:4]
    doy = date_yyyydoy[4::]

    file_name = f"HLS.{product}.T{tile}.{year}{doy}.{version}.hdf"
    hls_dataset_url = f"{base_url}/{version}/{product}/{year}/{tile[:2]}/{tile[2]}/{tile[3]}/{tile[4]}/{file_name}"

    return hls_dataset_url

def convert_date_to_Yj(date: str) -> str:
    """Convert a date to the format '%Y%j'.

    :param date: A date in one of the following supported formats: '%Y-%m-%d', '%Y%m%d', %Y%j'.
    :return: Date as string in the format '%Y%j.
    """

    date_recognizers = [
        lambda date: datetime.datetime.strptime(date, "%Y%j"),
        lambda date: datetime.datetime.strptime(date, "%Y-%m-%d"),
        lambda date: datetime.datetime.strptime(date, "%Y%m%d")
    ]
    # convert the user given date in the required %Y%j format
    date_yyydoy = None
    for date_recognizer in date_recognizers:
        try:
            dt = date_recognizer(date)
            date_yyydoy = datetime.datetime.strftime(dt, "%Y%j")
            # exit the loop on success
            break
        except ValueError:
            # repeat the loop on failure
            continue
    if date_yyydoy is None:
        raise ValueError(
            f"Date {date} did not match any supported format '%Y-%m-%d', '%Y%m%d', %Y%j'.")
    return date_yyydoy


def get_available_datasets(products, years, tiles, return_list=True):
    """Get all the datasets available for your products, years and tiles of interest."""
    urls_to_screen = []
    for product in products:
        for year in years:
            for tile in tiles:
                url = parse_url(f"{year}-01-01", tile, product)
                urls_to_screen += ["/".join(url.split("/")[:-1]) + "/"]
    datasets = _get_directories_in_directories(urls_to_screen, "*.hdf")
    if not return_list:
        datasets = dataframe_from_urls(datasets)
    return datasets


def dataframe_from_urls(urls):
    """Convert list of HLS dataset URLs in dataframe (columns: product, tile, date, url)."""
    import pandas as pd
    datasets = pd.DataFrame(pd.Series(urls).str.split("/", expand=True))[11] \
        .str.split(".", expand=True)[[1, 2, 3]] \
        .rename({1: "product", 2: "tile", 3: "date"}, axis=1)
    datasets.tile = datasets.tile.str.replace("T", "")
    datasets.date = pd.to_datetime(datasets.date, format="%Y%j")
    datasets["url"] = urls
    return datasets


def _get_directories(url, href_match):
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')
    urls = []
    for node in soup.find_all('a'):
        if node.get('href'):
            href = node.get("href")
            if fnmatch.fnmatch(href, href_match):
                urls.append(url + href)
    return urls


def _get_directories_in_directories(url_list, href_match):
    urls_new = []
    for url in tqdm(url_list, total=len(url_list)):
        urls_new += _get_directories(url, href_match)
    return urls_new

