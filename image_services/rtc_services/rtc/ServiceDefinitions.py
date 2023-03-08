# Script for testing generation of draft service definition, staging it, and publishing it to the server
import json
from lxml import etree

import arcpy
from arcgis.gis.server import Server

mosaic_dataset = '/home/arcgis/hjkristenson/gis-services/image_services/rtc_services/rtc/RTCservices_RTC_VV_230307_1947.gdb/RTC_VV'
config_file = '/home/arcgis/hjkristenson/gis-services/image_services/rtc_services/rtc/rtc_vv.json'

with open(config_file) as f:
    config = json.load(f)

out_sddraft = '/home/arcgis/hjkristenson/gis-services/image_services/rtc_services/rtc/RTC_VV_230307_1947_DSDTest.sddraft'
service_definition = '/home/arcgis/hjkristenson/gis-services/image_services/rtc_services/rtc/RTC_VV_230307_1947_DSDTest.sd'

arcpy.CreateImageSDDraft(
    raster_or_mosaic_layer=mosaic_dataset,
    out_sddraft=out_sddraft,
    service_name='ASF_S1_RTC_VV_TEST',
)

tree = etree.parse(out_sddraft)
for key, value in config['service_definition_overrides'].items():
    tree.find(key).text = value
tree.write(out_sddraft)

arcpy.server.StageService(
    in_service_definition_draft=out_sddraft,
    out_service_definition=service_definition,
)

server_connection_file = '/home/arcgis/server_connection.json'
with open(server_connection_file) as f:
    server_connection = json.load(f)
server = Server(**server_connection)

server.publish_sd(service_definition, folder='hjkristenson')
