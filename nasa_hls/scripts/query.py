import click
import pandas as pd
from pathlib import Path

import nasa_hls

@click.command()
@click.option('-p', '--products', help=" Landsat (L30) and/or Sentinel-2 (S30), e.g. 'L30,S30'")
@click.option('-t', '--tiles', help="List of tiles, e.g. '32UNU,32UPU' or path to a file with tiles in rows (32UNU\n32UPU).")
@click.option('-s', '--start_date', help="Start date (inclusive), e.g. '2019-01-01'")
@click.option('-e', '--end_date', help="End date (inclusive), e.g. '2019-12-31'")
@click.option('-d', '--dst_path', help="Path of a destination CSV-file.", required=False)
@click.option('-o', '--overwrite', type=bool, default=False, required=False, show_default=True)
def query(products, tiles, start_date, end_date, dst_path=None, overwrite=False):
    products = [pr.strip() for pr in products.split(",")]
    
    if Path(tiles).exists():
        with open(tiles) as src:
            tiles = src.read().split("\n")
    else:
        tiles = [tl.strip() for tl in tiles.split(",")]
    
    years = list(range(int(start_date[:4]), int(end_date[:4])+1))

    urls_datasets = nasa_hls.get_available_datasets(products=products,
                                                    years=years,
                                                    tiles=tiles)
    print(urls_datasets)
    df_datasets = nasa_hls.dataframe_from_urls(urls_datasets)
    print(df_datasets.dtypes)
    df_datasets = df_datasets.sort_values(["date", "product", "tile"]).reset_index(drop=True)
    df_datasets = df_datasets[(df_datasets["date"] >= start_date) & (df_datasets["date"] <= end_date)]
    
    if dst_path is not None:
        df_datasets.to_csv(dst_path, index=False)
    else:
        click.echo(df_datasets)
