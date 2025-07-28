#!/bin/bash
set -ex

/opt/arcgis/server/tools/authorizeSoftware -f 11_5/ArcGISImageServer_ArcGISServer_1561174.prvc -e hjkristenson@alaska.edu

mkdir /home/arcgis/raster_store

/opt/arcgis/server/tools/patchnotification/patchnotification

/opt/arcgis/server/tools/createsite/createsite.sh --username siteadmin --password $SITE_PASSWORD
