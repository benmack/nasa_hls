FROM osgeo/gdal:ubuntu-full-latest

LABEL maintainer="Ben Mack"
LABEL nasa-hls='2020-08-23'

RUN apt-get update \
 && apt-get install python3-pip -y

WORKDIR /home/hls

COPY ./nasa_hls /home/hls/nasa_hls/nasa_hls
COPY ./requirements.txt /home/hls/nasa_hls/requirements.txt
COPY ./setup.py /home/hls/nasa_hls/setup.py

RUN pip3 install --no-cache-dir -r /home/hls/nasa_hls/requirements.txt

RUN pip3 install --no-cache-dir /home/hls/nasa_hls
