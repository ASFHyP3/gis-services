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


def get_rasters(bucket: str, prefix: str, suffix: str) -> List[str]:
    rasters = []
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page['Contents']:
            if obj['Key'].endswith(suffix):
                rasters.append(f'/vsis3/{bucket}/{obj["Key"]}')
    return rasters


def get_pixel_type(data_type: str) -> int:
    if data_type == 'Byte':
        return 3
    if data_type == 'Float32':
        return 10
    raise ValueError(f'Unsupported data type: {data_type}')


def get_projection(srs_wkt: str) -> str:
    srs = osr.SpatialReference()
    srs.ImportFromWkt(srs_wkt)
    return srs.GetAttrValue('AUTHORITY', 1)


def get_raster_metadata(raster_path: str) -> dict:
    info = gdal.Info(raster_path, format='json')
    metadata = {
        'Raster': info['description'],
        'Name': os.path.basename(info['description']),
        'xMin': info['cornerCoordinates']['lowerLeft'][0],
        'yMin': info['cornerCoordinates']['lowerLeft'][1],
        'xMax': info['cornerCoordinates']['upperRight'][0],
        'yMax': info['cornerCoordinates']['upperRight'][1],
        'nRows': info['size'][1],
        'nCols': info['size'][0],
        'nBands': len(info['bands']),
        'PixelType': get_pixel_type(info['bands'][0]['type']),
        'SRS': get_projection(info['coordinateSystem']['wkt']),
    }
    return metadata


def update_csv(csv_file: str, bucket: str, prefix: str, suffix: str):
    if os.path.isfile(csv_file):
        with open(csv_file) as f:
            records = [record for record in csv.DictReader(f)]
    else:
        records = []
    logging.info(f'Found {len(records)} items in {csv_file}')

    all_rasters = get_rasters(bucket, prefix, suffix)
    existing_rasters = [record['Raster'] for record in records]
    new_rasters = set(all_rasters) - set(existing_rasters)

    logging.info(f'Adding {len(new_rasters)} new items to {csv_file}')
    for raster in new_rasters:
        record = get_raster_metadata(raster)
        records.append(record)

    with open(csv_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)


gdal.UseExceptions()
gdal.SetConfigOption('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR')

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--server-connection-file', default='/home/arcgis/server_connection.json')
parser.add_argument('--working-directory', default=os.getcwd())
parser.add_argument('config_file')
args = parser.parse_args()

today = datetime.datetime.now(datetime.timezone.utc).strftime('%y%m%d_%H%M')

raster_store = '/home/arcgis/raster_store/'
bucket = 'hyp3-nasa-disasters'
overview_path = '/vsis3/hyp3-nasa-disasters/overviews/'
template_directory = Path(__file__).parent.absolute() / 'raster_function_templates'

with open(args.config_file) as f:
    config = json.load(f)

csv_file = os.path.join(args.working_directory, f'{config["project_name"]}_{config["dataset_name"]}.csv')
output_name = f'{config["project_name"]}_{config["dataset_name"]}_{today}'
raster_function_template = ''.join([f'{template_directory / template};'
                                    for template in config['raster_function_templates']])
if config['default_raster_function_template'] != 'None':
    default_raster_function_template = str(template_directory / config['default_raster_function_template'])
else:
    default_raster_function_template = 'None'
overview_name = f'{output_name}_overview'
local_overview_filename = f'{overview_name}.crf'
s3_overview = f'{overview_path}{overview_name}.crf'
service_definition = os.path.join(args.working_directory, f'{output_name}.sd')

arcpy.env.parallelProcessingFactor = '75%'

try:
    update_csv(csv_file, bucket, config['s3_prefix'], config['s3_suffix'])

    logging.info('Creating geodatabase')
    geodatabase = arcpy.management.CreateFileGDB(
        out_folder_path=args.working_directory,
        out_name=f'{output_name}.gdb',
    )
    logging.info('Creating mosaic dataset')
    mosaic_dataset = str(arcpy.management.CreateMosaicDataset(
        in_workspace=geodatabase,
        in_mosaicdataset_name=config['dataset_name'],
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
        raster_type='Table',
        input_path=csv_file,
    )

    logging.info(f'Calculating custom field values in {mosaic_dataset}')
    arcpy.management.CalculateFields(
        in_table=mosaic_dataset,
        fields=[
            ['GroupName', '!Name![:46]'],
            ['Tag', '!Name!.split("_")[8]'],
            ['MaxPS', '1610'],
            ['StartDate', '!Name!.split("_")[2][4:6] + "/" + !Name!.split("_")[2][6:8] + "/" '
                          '+ !Name!.split("_")[2][:4] + " " + !Name!.split("_")[2][9:11] + ":" '
                          '+ !Name!.split("_")[2][11:13] + ":" + !Name!.split("_")[2][13:15]'],
            ['EndDate', '!Name!.split("_")[2][4:6] + "/" + !Name!.split("_")[2][6:8] + "/" '
                        '+ !Name!.split("_")[2][:4] + " " + !Name!.split("_")[2][9:11] + ":" '
                        '+ !Name!.split("_")[2][11:13] + ":" + !Name!.split("_")[2][13:15]'],
            ['DownloadURL', f'"https://s3-us-west-2.amazonaws.com/hyp3-nasa-disasters/{config["s3_prefix"]}" '
                            f'+ !Name! + ".tif"'],
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
        transmission_fields='Name;StartDate;EndDate;MinPS;MaxPS;LowPS;HighPS;Date;ZOrder;Dataset_ID;CenterX;CenterY;'
                            'Tag;ProductName;GroupName;DownloadURL',
        use_time='ENABLED',
        start_time_field='StartDate',
        end_time_field='EndDate',
        max_num_of_download_items=50,
        max_num_of_records_returned=2000,
        processing_templates=f'{raster_function_template}None',
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
            service_name=config['service_name'],
            copy_data_to_server=True,
        )

        tree = etree.parse(service_definition_draft.name)
        for key, value in config['service_definition_overrides'].items():
            tree.find(key).text = value
        tree.write(service_definition_draft.name)

        logging.info(f'Creating service definition {service_definition}')
        arcpy.server.StageService(
            in_service_definition_draft=service_definition_draft.name,
            out_service_definition=service_definition,
        )

    with open(args.server_connection_file) as f:
        server_connection = json.load(f)
    server = Server(**server_connection)

    logging.info(f'Publishing {service_definition}')
    server.publish_sd(service_definition, folder=config['service_folder'])

except arcpy.ExecuteError:
    logging.error(arcpy.GetMessages())
    raise
