#!/bin/bash

# wrapper script to run make_rgb_service.py via a cron schedule
# some arcpy commands require the python session to be tied to a terminal, so the crontab should look like:
# 0 8 * * * script -qef -c "/home/ubuntu/gis-services/image_services/rtc_services/make_rtc_service.sh /home/ubuntu/gis-services/image_services/rtc_services/nasa_disasters /home/ubuntu/gis-services/image_services/rtc_services/nasa_disasters/rgb.json" -a /home/ubuntu/gis-services/image_services/rtc_services/nasa_disasters/make_rgb_service.log

set -e
source /home/ubuntu/miniforge3/etc/profile.d/conda.sh
conda activate arcpy
python /home/ubuntu/gis-services/image_services/updating_scripts/time_slider_updates.py