## Changelog

### 0.1.1

:Date: Aug 23, 2020

#### New Features

#### Fixes

#### Other Changes

* Docker images for shell and JupyterLab

* Command line interface added:
    * hls_query: nasa_hls.scripts.query:query
    * hls_download: nasa_hls.scripts.download:download
    * hls_convert_batch: nasa_hls.scripts.convert:convert_batch

### 0.1.0

:Date: Mar 7, 2020

#### New Features

* Parameter `gdal_translate_options` allows to create costumized GeoTIFF with `convert_hdf2tiffs`.

#### Fixes

* Missing bands ('Red_Edge2':'B06', 'Water_Vapor' : 'B09') added to `uitls.BAND_NAMES`.

#### Other Changes

* Minor changes in tutorials.
* Added CHANGELOG (this file)