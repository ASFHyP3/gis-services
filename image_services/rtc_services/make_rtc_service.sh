#!/bin/bash

# wrapper script to run make_rgb_service.py via a cron schedule
# some arcpy commands require the python session to be tied to a terminal, so the crontab should look like:
# 0 8 * * * script -qef -c "/home/arcgis/gis-services/image_services/rtc_services/make_rtc_service.sh /home/arcgis/gis-services/image_services/rtc_services/rgb /home/arcgis/gis-services/image_services/rtc_services/rgb/rgb.json" -a /home/arcgis/gis-services/image_services/rtc_services/rgb/make_rgb_service.log

set -e
source /home/arcgis/miniconda3/etc/profile.d/conda.sh
conda activate arcpy
python /home/arcgis/gis-services/image_services/rtc_services/make_rtc_service.py \
  --server-connection-file /home/arcgis/server_connection.json \
  --working-directory $1 \
  $2