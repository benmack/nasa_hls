import click
import datetime
import numpy as np
import pandas as pd
from pathlib import Path

import nasa_hls

@click.command()
@click.option('-s', '--src', help="Directory (with .hdf files), path to one .hdf file or a csv with a 'path' column with paths to .hdf files.")
@click.option('-d', '--dir_dst', help="Destination directory for the converted data.")
@click.option('-b', '--bands', type=str, default=None, help="List of bands. Default is None, i.e. all bands.")
@click.option('-c', '--max_cloud_coverage', type=int, default=80, help="Maximum cloud cover.")
@click.option('-g', '--gdal_translate_options', type=str, default=None, help="GDAL translate options. Example 1 (build Cloud Optimized GeoTiff): '-of COG'. Example 2 (using quotes): '-of GTiff -co \"TILED=YES\"'.")
@click.option('-o', '--overwrite', type=bool, default=False, required=False, show_default=True)
def convert_batch(src, 
                  dir_dst, 
                  bands=None, 
                  max_cloud_coverage=80, 
                  gdal_translate_options=None, 
                  overwrite=False):

    #src = "./query-results_downloads"
    # src = "./query-results_downloads/HLS.L30.T32UMU.2018001.v1.4.hdf"
    #src = "./query-results_downloads/datasets_downloaded_2020-06-16T21:53:01.csv"

    if Path(src).is_dir():
        path_list = list(Path(src).glob("*.hdf"))
    elif Path(src).is_file():
        if ".hdf" in str(src):
            path_list = [src]
        elif ".csv" in str(src):
            path_list = pd.read_csv(src)["path"].values
        else:
            raise Exception(f"'Invalid 'src'. Expecting directory (with .hdf files), path to one .hdf file or a csv with a 'path' column with paths to .hdf files. Got {src}")
    else:
        raise Exception(f"'Invalid 'src'. Expecting directory (with .hdf files), path to one .hdf file or a csv with a 'path' column with paths to .hdf files. Got {src}")

    if bands is not None:
        bands = [b.strip() for b in bands.split(",")]

    nasa_hls.convert_hdf2tiffs_batch(path_list, 
                                    Path(dir_dst), 
                                    bands=bands, 
                                    max_cloud_coverage=max_cloud_coverage,
                                    gdal_translate_options=gdal_translate_options)
