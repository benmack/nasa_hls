import logging
from pathlib import Path
from tqdm import tqdm
import subprocess

from .utils import BAND_NAMES
from .utils import get_cloud_coverage_from_hdf


log = logging.getLogger(__name__)


def convert_hdf2tiffs_batch(hdf_paths, dstdir, bands=None, max_cloud_coverage=100,
                            gdal_translate_options=None):
    """Convert a batch of nasa-hls hdf files to single layer file GeoTiffs."""

    converted = []
    for hdf_path in tqdm(hdf_paths, total=len(hdf_paths)):
        dir_tiffs = convert_hdf2tiffs(hdf_path=hdf_path, dstdir=dstdir, bands=bands,
                                      max_cloud_coverage=max_cloud_coverage,
                                      gdal_translate_options=gdal_translate_options)
        if dir_tiffs is not None:
            converted.append(dir_tiffs)
    return converted

def convert_hdf2tiffs(hdf_path, dstdir, bands=None, max_cloud_coverage=100,
                      gdal_translate_options=None):
    """Convert (a subset of) hdf-file layers to single layer file GeoTiffs.
    
    Starting with GDAL 3.1 a Cloud Optimized GeoTIFF generator is available.
    It can be used to generate COGs instead of normal GeoTIFFs.
    For building a COG with default options simply use 
    `gdal_translate_options='-of COG'`.
    For more information and options see https://gdal.org/drivers/raster/cog.html.
    """

    if ".L30." in str(hdf_path):
        product = "L30"
    elif ".S30." in str(hdf_path):
        product = "S30"
    else:
        log.exception(f"FATAL ERROR : COULD NOT DERIVE PRODUCT.")
        raise ValueError(f"Could not derive the product ('L30' or 'S30') from the {hdf_path}.")

    if bands is None:
        bands = list(BAND_NAMES[product].keys())

    return_none = False
    for long_band_name in bands:
        if long_band_name not in BAND_NAMES[product].keys():
            continue
        else:
            band = BAND_NAMES[product][long_band_name]

        if not isinstance(hdf_path, str):
            hdf_path_str = str(hdf_path.resolve())
        else:
            hdf_path = Path(hdf_path)
            hdf_path_str = hdf_path

        if max_cloud_coverage < 100:
            try:
                cc = get_cloud_coverage_from_hdf(hdf_path_str)
                log.debug(f"DERIVED CLOUD COVER: {cc}")
            except:
                log.exception(f"COULD NOT DERIVE CLOUD COVER => PROCESSING ANYWAY: {hdf_path_str}")
                cc = 0

            if cc > max_cloud_coverage:
                log.debug(f"SKIPPING CONVERSION - TOO HIGH CLOUD COVER: {cc}")
                return_none = True
                break

        dst = (dstdir / hdf_path.stem).resolve() / f"{hdf_path.stem}__{long_band_name}.tif"
        if not dst.exists():
            cmd = f"gdal_translate HDF4_EOS:EOS_GRID:'{hdf_path_str}':Grid:{band} {dst}"
            if gdal_translate_options:
                cmd += f" {gdal_translate_options}"
            log.debug(f"CMD: {cmd}")
            dst.parent.mkdir(exist_ok=True, parents=True)
            try:
                subprocess.check_call(cmd, shell=True)
            except Exception:
                log.exception(f"ERROR DURING CONVERSION WITH CMD: {cmd}.")
    if return_none:
        return None
    else:
        return dstdir / hdf_path.stem
