import argparse
import csv
import datetime
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List

import arcpy
import boto3
from arcgis.gis.server import Server
from lxml import etree
from osgeo import gdal, osr
from tenacity import Retrying, before_sleep_log, stop_after_attempt, wait_fixed

gdal.UseExceptions()
gdal.SetConfigOption('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR')

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--server-connection-file', default='/home/arcgis/server_connection.json')
parser.add_argument('--working-directory', default=os.getcwd())
parser.add_argument('config_file')
args = parser.parse_args()

raster_store = '/home/arcgis/raster_store/'
bucket = 'hyp3-nasa-disasters'
overview_path = '/vsis3/hyp3-nasa-disasters/overviews/'
template_directory = Path(__file__).parent.absolute() / 'raster_function_templates'


service_definition = '/home/arcgis/hjkristenson/gis-services/image_services/rtc_services/usda/USDA_RTC_VV_230707_0039.sd'

logging.info(f'Creating service definition {service_definition}')
arcpy.server.StageService(
    in_service_definition_draft='/home/arcgis/hjkristenson/gis-services/image_services/rtc_services/usda/USDA_RTC_VV_230707_0039.sddraft',
    out_service_definition=service_definition,
)

with open(args.config_file) as f:
    config = json.load(f)

with open(args.server_connection_file) as f:
    server_connection = json.load(f)

for attempt in Retrying(stop=stop_after_attempt(3), reraise=True,
                        before_sleep=before_sleep_log(logging, logging.WARNING)):
    with attempt:
        logging.info(f'Publishing {service_definition}')
        server = Server(**server_connection)
        server.publish_sd(service_definition, folder=config['service_folder'])
