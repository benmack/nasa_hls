from pathlib import Path
import urllib

from .utils import parse_url

def download(dstdir, date, tile, product, version="v1.4", overwrite=False):

    url_hdf = parse_url(date, tile=tile, product=product, version=version)
    url_hdf_hdr = url_hdf + ".hdr"
    dstdir = Path(dstdir)
    dstdir.mkdir(parents=True, exist_ok=True)

    dstpath_hdf = dstdir / url_hdf.split("/")[-1]
    dstpath_hdf_hdr = dstdir / url_hdf_hdr.split("/")[-1]

    if not Path(dstpath_hdf).exists() or overwrite:
        urllib.request.urlretrieve(url_hdf, dstpath_hdf)
    if not Path(dstpath_hdf_hdr).exists() or overwrite:
        urllib.request.urlretrieve(url_hdf_hdr, dstpath_hdf_hdr)

    return 0
