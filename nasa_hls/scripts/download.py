import click
import datetime
import numpy as np
import pandas as pd
from pathlib import Path

import nasa_hls

@click.command()
@click.option('-p', '--path_query', help="Path of a CSV-file as returned by nhls_query.")
@click.option('-d', '--dir_dst', help="Destination directory for the downloaded data.")
@click.option('-o', '--overwrite', type=bool, default=False, required=False, show_default=True)
def download(path_query, dir_dst, overwrite=False):
    df_download = pd.read_csv(path_query, parse_dates=["date"])
    df_download = df_download.sort_values(["date", "tile", "product"])
    df_download["id"] = df_download["url"].str.split("/", expand=True)[11].str[0:-4]
    df_download["path"] = dir_dst + "/" + df_download["id"] + ".hdf"
    df_download["exists_before"] = df_download.path.apply(lambda x: Path(x).exists())

    nasa_hls.download_batch(dstdir=dir_dst,
                            datasets=df_download,
                            version="v1.4",
                            overwrite=overwrite)
    df_download["exists_after"] = df_download.path.apply(lambda x: Path(x).exists())
    
    df_download["cloud_cover"] = np.NaN
    df_download["spatial_coverage"] = np.NaN

    for i in df_download.index:
        try:
            _ = nasa_hls.get_metadata_from_hdf(df_download.loc[i, "path"],
                                            fields=["cloud_cover",
                                                    "spatial_coverage"])
            df_download.loc[i, "cloud_cover"] = _["cloud_cover"]
            df_download.loc[i, "spatial_coverage"] = _["spatial_coverage"]
        except:
            pass

    df_download.to_csv(
        Path(dir_dst) / 'datasets_downloaded_{date:%Y-%m-%dT%H:%M:%S}.csv'.format( date=datetime.datetime.now()), 
        index=False
        )
