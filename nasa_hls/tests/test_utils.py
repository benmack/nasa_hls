import pytest

import nasa_hls
from nasa_hls import utils

def test_convert_date():
    assert utils.convert_data("2017-01-02") == "2017002"
    assert utils.convert_data("20170102") == "2017002"
    assert utils.convert_data("2017002") == "2017002"

def test_parse_url():
    target_url = "https://hls.gsfc.nasa.gov/data/v1.4/L30/2017/32/U/N/U/HLS.L30.T32UNU.2017007.v1.4.hdf"
    assert utils.parse_url(date="2017-01-07",
                           tile="32UNU",
                           product="L30",
                           version="v1.4") == target_url
