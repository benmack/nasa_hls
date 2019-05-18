# nasa-hls

Download [S30 and/or L30 data](https://hls.gsfc.nasa.gov/products-description/) from [NASA's Harmonized Landsat and Sentinel-2 project](https://hls.gsfc.nasa.gov/).

If you are lucky, your area of interest is covered by the [test sites](https://hls.gsfc.nasa.gov/test-sites/) (see also the [map with available tiles](https://hls.gsfc.nasa.gov/wp-content/uploads/2018/10/hls1.4_coverage.jpg)).

## Installation

In case you have git installed you can install the package as follows:

    pip install git+https://github.com/benmack/nasa_hls.git
    
If not and you have trouble to find a way, please [open an issue](https://github.com/benmack/nasa_hls/issues).


## Requirements

This package requires that the GDAL command line tools. 
Specifically, 

* ``gdal_translate`` is required by the function ``convert_hdf2tiffs``
* ``gdalinfo`` is required by the function ``get_cloud_coverage_from_hdf``

Furthermore it depends on the Python packages *bs4*, *requests* and *tqdm*.


## Usage

The following guides may help you to get started with the package:

* [Query and download HLS datasets with *nasa_hls*](https://github.com/benmack/nasa-hls/blob/master/docs/Query_and_download_hls_datasets_with_nasa_hls.ipynb)
