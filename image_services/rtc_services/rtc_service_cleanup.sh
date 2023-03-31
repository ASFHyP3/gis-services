#!/bin/bash

#pull any remote changes
cd /home/arcgis/gis-services
git pull

#Script that sorts through rtc image_services directories and deletes geodatabases and service definitions > a day old

find /home/arcgis/gis-services/image_services/rtc_services/nasa_disasters/ -name *gdb -type d -mmin +10800 -exec rm -Rv {} \;
find /home/arcgis/gis-services/image_services/rtc_services/nasa_disasters/ -name *.sd -type f -mmin +10800 -exec rm -Rv {} \;

find /home/arcgis/gis-services/image_services/rtc_services/hkh/ -name *gdb -type d -mmin +10800 -exec rm -Rv {} \;
find /home/arcgis/gis-services/image_services/rtc_services/hkh/ -name *.sd -type f -mmin +10800 -exec rm -Rv {} \;