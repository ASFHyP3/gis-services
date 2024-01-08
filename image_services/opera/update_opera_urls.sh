#!/bin/bash

# wrapper script to run update_opera_urls.py via a cron schedule
# some arcpy commands require the python session to be tied to a terminal, so the crontab should look like:
# 0 8 * * * script -qef -c "/home/arcgis/gis-services/image_services/rtc_services/make_rtc_service.sh /home/arcgis/gis-services/image_services/rtc_services/nasa_disasters /home/arcgis/gis-services/image_services/rtc_services/nasa_disasters/rgb.json" -a /home/arcgis/gis-services/image_services/rtc_services/nasa_disasters/make_rgb_service.log

set -e
source /home/arcgis/mambaforge/etc/profile.d/conda.sh
conda activate url-query
python /home/arcgis/gis-services/image_services/opera/update_opera_urls.py \
  --working-directory $1 \
  $2
