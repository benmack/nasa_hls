from bs4 import BeautifulSoup
import datetime
import fnmatch
import requests
from subprocess import Popen, PIPE
from tqdm import tqdm
import urllib


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

    date_yyyydoy = convert_data(date)
    year = date_yyyydoy[:4]
    doy = date_yyyydoy[4::]

    file_name = f"HLS.{product}.T{tile}.{year}{doy}.{version}.hdf"
    hls_dataset_url = f"{base_url}/{version}/{product}/{year}/{tile[:2]}/{tile[2]}/{tile[3]}/{tile[4]}/{file_name}"

    return hls_dataset_url

def convert_data(date: str) -> str:
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

