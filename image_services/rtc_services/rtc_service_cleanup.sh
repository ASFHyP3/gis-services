#!/bin/bash

#pull any remote changes
cd /home/arcgis/gis-services
git pull
chmod 777 /home/arcgis/gis-services/image_services/rtc_services/rtc_service_cleanup.sh

#Script that sorts through rtc image_services directories and deletes geodatabases and service definitions > a day old

find /home/arcgis/gis-services/image_services/rtc_services/ -name *gdb -type d -mmin +10800 -exec rm -Rv {} \;
find /home/arcgis/gis-services/image_services/rtc_services/ -name *.sd -type f -mmin +10800 -exec rm -Rv {} \;
