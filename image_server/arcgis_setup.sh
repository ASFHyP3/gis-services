#!/bin/bash
set -ex

/opt/arcgis/server/tools/authorizeSoftware -f ArcGISGISServerAdvanced_ArcGISServer_1097910.prvc -e hjkristenson@alaska.edu
/opt/arcgis/server/tools/authorizeSoftware -f ArcGISImageServer_ArcGISServer_1097915.prvc -e hjkristenson@alaska.edu

mkdir /home/arcgis/raster_store

wget https://gisupdates.esri.com/QFE/S-1091-P-762/ArcGIS-1091-S-K1-Patch-linux.tar
wget https://gisupdates.esri.com/QFE/S-1091-P-770/ArcGIS-1091-S-SQ-Patch-linux.tar
wget https://gisupdates.esri.com/QFE/S-1091-P-798/ArcGIS-1091-S-SEC2022U1-PatchB-linux.tar
wget https://gisupdates.esri.com/QFE/S-1091-P-801/ArcGIS-1091-S-UNDM2-Patch-linux.tar
wget https://gisupdates.esri.com/QFE/S-1091-P-807/ArcGIS-1091-S-MPS-Patch-linux.tar
wget https://gisupdates.esri.com/QFE/S-1091-P-824/ArcGIS-1091-S-SEC2022U2-Patch-linux.tar
wget https://gisupdates.esri.com/QFE/S-1091-P-854/ArcGIS-1091-S-UNDM3-Patch-linux.tar
wget https://gisupdates.esri.com/QFE/S-1091-P-856/ArcGIS-1091-S-GSQ-Patch-linux.tar
wget https://gisupdates.esri.com/QFE/S-1091-P-871/ArcGIS-1091-S-CPS-Patch-linux.tar
wget https://gisupdates.esri.com/QFE/S-1091-P-882/ArcGIS-1091-S-UNDM4-PatchB-linux.tar
wget https://gisupdates.esri.com/QFE/S-1091-P-938/ArcGIS-1091-S-SEC2023U1-Patch-linux.tar
wget https://gisupdates.esri.com/QFE/S-1091-P-944/ArcGIS-1091-S-MFSSEC2023U1-Patch-linux.tar
wget https://gisupdates.esri.com/QFE/S-1091-P-926/ArcGIS-1091-S-UNDM5-Patch-linux.tar
wget https://gisupdates.esri.com/QFE/PFA-1091-P-785/ArcGIS-1091-PFA-SEC2022U1-Patch-linux.tar
wget https://gisupdates.esri.com/QFE/PFA-1091-P-805/ArcGIS-1091-PFA-QCS-Patch-linux.tar
wget https://gisupdates.esri.com/QFE/PFA-1091-P-839/ArcGIS-1091-PFA-SEC2022U2-PatchB-linux.tar
wget https://gisupdates.esri.com/QFE/PFA-1091-P-858/ArcGIS-1091-PFA-ESFD-Patch-linux.tar
wget https://gisupdates.esri.com/QFE/DS-1091-P-806/ArcGIS-1091-DS-DE-Patch-linux.tar
aws s3 cp s3://hyp3-software/HF-000005735.zip .

for f in *.zip; do unzip "$f"; done
for f in *.tar; do tar -xvf "$f"; done

for f in S-1091-P-*/applypatch; do "$f" -s -server; done
for f in PFA-1091-P-*/applypatch; do "$f" -s -portal; done
for f in DS-1091-P-*/applypatch; do "$f" -s -datastore; done
for f in S-1091-HF-*/applypatch; do "$f" -s -server; done

/opt/arcgis/server/tools/patchnotification/patchnotification

/opt/arcgis/server/tools/createsite/createsite.sh --username siteadmin --password $SITE_PASSWORD
