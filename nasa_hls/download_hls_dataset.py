import logging
from pathlib import Path
from tqdm import tqdm
import urllib

from .utils import parse_url


log = logging.getLogger(__name__)


def download_batch(dstdir, datasets, version="v1.4", overwrite=False):
    """Download the datasets given by a dataframe as returned by ``utils.get_available_datasets``.
    """
    for i, row in tqdm(datasets.iterrows(), total=datasets.shape[0]):
        download(dstdir, row["date"].strftime("%Y-%m-%d"), row["tile"], row["product"],
                 version=version, overwrite=overwrite)


def download(dstdir, date, tile, product, version="v1.4", overwrite=False):
    """Download a HRL dataset into directory 'dstdir' given the dataset specifications.
    """
    def _download(src, dst, overwrite):
        if not Path(dst).exists() or overwrite:
            try:
                urllib.request.urlretrieve(src, dst)
            except Exception:
                log.exception(f"ERROR DURING DOWNLOAD: {dst} FROM {src}.")
                return 1
            if not Path(dst).exists():
                log.debug(f"DOWNLOAD COMPLETE: {dst} FROM {src}")
            else:
                log.debug(f"DOWNLOAD COMPLETE (EXISTING FILE OVERWRITTEN): {dst} FROM {src}")
        else:
            log.debug(f"DOWNLOAD SKIPPED (FILE EXISTS): {src} TO {dst}")

    url_hdf = parse_url(date, tile=tile, product=product, version=version)
    url_hdf_hdr = url_hdf + ".hdr"

    dstdir = Path(dstdir)
    dstdir.mkdir(parents=True, exist_ok=True)

    dstpath_hdf = dstdir / url_hdf.split("/")[-1]
    dstpath_hdf_hdr = dstdir / url_hdf_hdr.split("/")[-1]

    _download(url_hdf, dstpath_hdf, overwrite)
    _download(url_hdf_hdr, dstpath_hdf_hdr, overwrite)

    return 0
