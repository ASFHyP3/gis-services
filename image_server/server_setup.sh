#!/bin/bash
set -e

read -sp 'siteadmin password: ' siteadmin_password
echo ""
read -sp 'asf_publisher password: ' asf_publisher_password
echo ""

echo "increasing limit on open file descriptors for ubuntu user"
echo 'ubuntu soft nofile 65535' | sudo tee -a /etc/security/limits.conf
ulimit -S -n 65535

echo "installing AWS CLI"
sudo apt install unzip
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -R awscliv2.zip aws

echo "installing ArcGIS Server"
aws s3 cp s3://hyp3-software/ArcGISImageServer_ArcGISServer_1561174.prvc .
aws s3 cp s3://hyp3-software/ArcGISServer.tar.gz .
tar xvf ArcGISServer.tar.gz
ArcGISServer/Setup -m silent -l yes -a /home/ubuntu/ArcGISImageServer_ArcGISServer_1561174.prvc
rm -R ArcGISImageServer_ArcGISServer_1561174.prvc ArcGISServer.tar.gz ArcGISServer

echo "configuring ArcGIS Server to run at startup"
/home/ubuntu/arcgis/server/stopserver.sh
sudo cp /home/ubuntu/arcgis/server/framework/etc/scripts/arcgisserver.service /etc/systemd/system/
sudo chmod 600 /etc/systemd/system/arcgisserver.service
sudo systemctl enable arcgisserver.service
sudo systemctl start arcgisserver.service

echo "installing arcpy conda environment"
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh -b
source /home/ubuntu/miniforge3/etc/profile.d/conda.sh
mamba env create -f /home/ubuntu/gis-services/image_server/environment.yml -y
conda env config vars set ARCGISHOME=/home/ubuntu/arcgis/server/ -n arcpy
mamba shell init
rm Miniforge3-Linux-x86_64.sh

echo "creating server_connection.json"
echo "{\"url\": \"https://localhost:6443/arcgis/admin\", \"username\": \"asf_publisher\", \"password\": \"$asf_publisher_password\"}" > /home/ubuntu/server_connection.json

echo "creating ArcGIS Server site"
/home/ubuntu/arcgis/server/tools/createsite/createsite.sh --username siteadmin --password $siteadmin_password
