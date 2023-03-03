import argparse
import datetime
import json
import logging
import os
import subprocess
import tempfile

import arcpy
from arcgis.gis.server import Server


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--raster-filter', default='*_VH.tif')
parser.add_argument('--server-connection-file', default='server_connection.json')
parser.add_argument('--service-name', default='ASF_S1_RTC_VH')
parser.add_argument('--service-folder', default='ASF_S1')
parser.add_argument('--working-directory', default=os.getcwd())
args = parser.parse_args()

today = datetime.datetime.now(datetime.timezone.utc).strftime('%y%m%d_%H%M')

project_name = 'RTCservices'
dataset_name = 'RTC_VH'
raster_store = '/home/arcgis/raster_store/'
s3_path = '/vsis3/hyp3-nasa-disasters/'
s3_prefix = 'RTC_services/'
overview_path = '/vsis3/hyp3-nasa-disasters/overviews/'

output_name = f'{project_name}_{dataset_name}_{today}'
raster_function_template = f'{args.working_directory}/Sentinel1_RTC_Power.rft.xml;' \
                           f'{args.working_directory}/Sentinel1_RTC_Amplitude.rft.xml;' \
                           f'{args.working_directory}/Sentinel1_RTC_dB.rft.xml;' \
                           f'{args.working_directory}/Sentinel1_RTC_dB_Stretch.rft.xml'
default_raster_function_template = f'{args.working_directory}/Sentinel1_RTC_dB_Stretch.rft.xml'
overview_name = f'{output_name}_overview'
local_overview_filename = f'{overview_name}.crf'
s3_overview = f'{overview_path}{overview_name}.crf'
service_definition = os.path.join(args.working_directory, f'{output_name}.sd')

arcpy.env.parallelProcessingFactor = '75%'


logging.info(f'Creating geodatabase')
geodatabase = arcpy.management.CreateFileGDB(
    out_folder_path=args.working_directory,
    out_name=f'{output_name}.gdb',
)

logging.info(f'Creating mosaic dataset')
mosaic_dataset = str(arcpy.management.CreateMosaicDataset(
    in_workspace=geodatabase,
    in_mosaicdataset_name=dataset_name,
    coordinate_system=3857,
))

logging.info(f'Adding fields to {mosaic_dataset}')
arcpy.management.AddFields(
    in_table=mosaic_dataset,
    field_description=[
        ['StartDate', 'DATE'],
        ['EndDate', 'DATE'],
        ['DownloadURL', 'TEXT'],
    ],
)

logging.info(f'Adding source rasters to {mosaic_dataset}')
arcpy.management.AddRastersToMosaicDataset(
    in_mosaic_dataset=mosaic_dataset,
    raster_type='Raster Dataset',
    input_path=f'{s3_path}{s3_prefix}',
    filter=args.raster_filter,
)

logging.info(f'Calculating custom field values in {mosaic_dataset}')
arcpy.management.CalculateFields(
    in_table=mosaic_dataset,
    fields=[
        ['GroupName', '!Name!.split(";")[0][:-3]'],
        ['Tag', '!Name!.split("_")[8]'],
        ['MaxPS', '1610'],
        ['StartDate', '!Name!.split("_")[2][4:6] + "/" + !Name!.split("_")[2][6:8] + "/" + !Name!.split("_")[2][:4] + " " + !Name!.split("_")[2][9:11] + ":" + !Name!.split("_")[2][11:13] + ":" + !Name!.split("_")[2][13:15]'],
        ['EndDate', '!Name!.split("_")[2][4:6] + "/" + !Name!.split("_")[2][6:8] + "/" + !Name!.split("_")[2][:4] + " " + !Name!.split("_")[2][9:11] + ":" + !Name!.split("_")[2][11:13] + ":" + !Name!.split("_")[2][13:15]'],
        ['DownloadURL', f'"https://s3-us-west-2.amazonaws.com/hyp3-nasa-disasters/{s3_prefix}"+!Name!+".tif"'],
    ],
)

logging.info(f'Building raster footprints for {mosaic_dataset}')
arcpy.management.BuildFootprints(
    in_mosaic_dataset=mosaic_dataset,
    reset_footprint='NONE',
    min_data_value=0,
    max_data_value=4294967295,
    approx_num_vertices=12,
    update_boundary='UPDATE_BOUNDARY',
)

logging.info(f'Building {mosaic_dataset} dataset boundary')
arcpy.management.BuildBoundary(
    in_mosaic_dataset=mosaic_dataset,
    append_to_existing='OVERWRITE',
    simplification_method='NONE',
)

logging.info(f'Setting properties for {mosaic_dataset}')
arcpy.management.SetMosaicDatasetProperties(
    in_mosaic_dataset=mosaic_dataset,
    rows_maximum_imagesize=5000,
    columns_maximum_imagesize=5000,
    allowed_compressions='JPEG;NONE;LZ77',
    default_compression_type='JPEG',
    JPEG_quality=80,
    resampling_type='NEAREST',
    LERC_Tolerance=0.01,
    clip_to_footprints='CLIP',
    clip_to_boundary='CLIP',
    color_correction='NOT_APPLY',
    footprints_may_contain_nodata='FOOTPRINTS_MAY_CONTAIN_NODATA',
    allowed_mensuration_capabilities='BASIC',
    default_mensuration_capabilities='BASIC',
    allowed_mosaic_methods='Center;NorthWest;Nadir;LockRaster;ByAttribute;Seamline;None',
    default_mosaic_method='ByAttribute',
    order_field='StartDate',
    order_base='1/1/2050 12:00:00 AM',
    sorting_order='Ascending',
    mosaic_operator='FIRST',
    blend_width=10,
    view_point_x=300,
    view_point_y=300,
    max_num_per_mosaic=50,
    cell_size_tolerance=1.8,
    cell_size=3,
    metadata_level='BASIC',
    transmission_fields='Name;StartDate;EndDate;MinPS;MaxPS;LowPS;HighPS;Date;ZOrder;Dataset_ID;CenterX;CenterY;Tag;ProductName;GroupName;DownloadURL',
    use_time='ENABLED',
    start_time_field='StartDate',
    end_time_field='EndDate',
    max_num_of_download_items=50,
    max_num_of_records_returned=2000,
    processing_templates=f'{raster_function_template};None',
    default_processing_template=default_raster_function_template,
)

logging.info('Calculating cell size ranges')
arcpy.management.CalculateCellSizeRanges(
    in_mosaic_dataset=mosaic_dataset,
    do_compute_min='NO_MIN_CELL_SIZES',
    do_compute_max='NO_MAX_CELL_SIZES',
    max_range_factor=10,
    cell_size_tolerance_factor=0.8,
    update_missing_only='UPDATE_ALL',
)

with tempfile.TemporaryDirectory(dir=raster_store) as temp_dir:
    local_overview = os.path.join(temp_dir, local_overview_filename)

    logging.info(f'Generating {local_overview}')
    with arcpy.EnvManager(cellSize=1200):
        arcpy.management.CopyRaster(
            in_raster=mosaic_dataset,
            out_rasterdataset=local_overview,
        )

    logging.info(f'Moving CRF to {s3_overview}')
    subprocess.run(['aws', 's3', 'cp', local_overview, s3_overview.replace('/vsis3/', 's3://'), '--recursive'])

logging.info('Adding overview to mosaic dataset')
arcpy.management.AddRastersToMosaicDataset(
    in_mosaic_dataset=mosaic_dataset,
    raster_type='Raster Dataset',
    input_path=s3_overview,
)

logging.info('Calculating Overview Start and End Dates')
start_dates = [row[1] for row in arcpy.da.SearchCursor(mosaic_dataset, ['Tag', 'StartDate']) if row[0] != 'Dataset']
overview_start_date = min(start_dates).replace(microsecond=0) + datetime.timedelta(hours=-8)
overview_end_date = max(start_dates).replace(microsecond=0) + datetime.timedelta(hours=8)

logging.info('Calculating custom fields for overview record')
selection = arcpy.management.SelectLayerByAttribute(
    in_layer_or_view=mosaic_dataset,
    selection_type='NEW_SELECTION',
    where_clause=f"Name = '{overview_name}'",
)

arcpy.management.CalculateFields(
    in_table=selection,
    fields=[
        ['MinPS', '1600'],
        ['Category', '2'],
        ['GroupName', '"Mosaic Overview"'],
        ['StartDate', f'"{overview_start_date}"'],
        ['EndDate', f'"{overview_end_date}"'],
    ],
)

with tempfile.NamedTemporaryFile(suffix='.sddraft') as service_definition_draft:
    logging.info(f'Creating draft service definition {service_definition_draft.name}')
    arcpy.CreateImageSDDraft(
        raster_or_mosaic_layer=mosaic_dataset,
        out_sddraft=service_definition_draft.name,
        service_name=args.service_name,
        summary='Radiometric Terrain Corrected (RTC) products generated from Sentinel-1 SAR imagery, '
                'processed by ASF. Surface water appears very dark under calm conditions, as signal bounces '
                'off the surface away from the sensor. High VH values commonly indicate the presence of vegetation.'
    )

    logging.info(f'Creating service definition {service_definition}')
    arcpy.server.StageService(
        in_service_definition_draft=service_definition_draft.name,
        out_service_definition=service_definition,
    )

with open(args.server_connection_file) as f:
    server_connection = json.load(f)
server = Server(**server_connection)

for service in server.services.list(folder=args.service_folder):
    if service.properties['serviceName'] == args.service_name:
        logging.info(f'Deleting existing {args.service_folder}/{args.service_name} service')
        service.delete()
        break

logging.info(f'Publishing {service_definition}')
server.publish_sd(service_definition, folder=args.service_folder)
