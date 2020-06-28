FROM osgeo/gdal:ubuntu-full-latest

LABEL maintainer="Ben Mack"
LABEL nasa_hls='0.1.1'


RUN apt-get update \
 && apt-get install python3-pip -y

WORKDIR /home/hls

COPY . /home/hls/nasa_hls

RUN pip3 install --no-cache-dir -r /home/hls/nasa_hls/requirements.txt

RUN pip3 install --no-cache-dir -e /home/hls/nasa_hls
