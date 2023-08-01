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
from osgeo import gdal, osr


SEASONS = {
    'summer': {
        'SeasonCode': 'JJA',
        'Season': 'June/July/August',
        'StartDate': '06/01/2020',
        'EndDate': '08/31/2020',
    },
    'fall': {
        'SeasonCode': 'SON',
        'Season': 'September/October/November',
        'StartDate': '09/01/2020',
        'EndDate': '11/30/2020',
    },
    'winter': {
        'SeasonCode': 'DJF',
        'Season': 'December/January/February',
        'StartDate': '12/01/2019',
        'EndDate': '02/29/2020',
    },
    'spring': {
        'SeasonCode': 'MAM',
        'Season': 'March/April/May',
        'StartDate': '03/01/2020',
        'EndDate': '05/31/2020',
    }
}


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
        return 9
    raise ValueError(f'Unsupported data type: {data_type}')


def get_projection(srs_wkt: str) -> str:
    srs = osr.SpatialReference()
    srs.ImportFromWkt(srs_wkt)
    return srs.GetAttrValue('AUTHORITY', 1)


def get_raster_metadata(raster_path: str) -> dict:
    assert raster_path.startswith('/vsis3/sentinel-1-global-coherence-earthbigdata/')
    key = raster_path.removeprefix('/vsis3/sentinel-1-global-coherence-earthbigdata/')
    download_url = f'https://sentinel-1-global-coherence-earthbigdata.s3.us-west-2.amazonaws.com/{key}'

    name = Path(raster_path).stem
    tile, season, polarization, product_type = name.split('_')
    polarization = polarization.upper()
    tag = f'{product_type}_{polarization}_{SEASONS[season]["SeasonCode"]}'

    info = gdal.Info(raster_path, format='json')
    return {
        'Raster': raster_path,
        'Name': name,
        'xMin': info['cornerCoordinates']['lowerLeft'][0],
        'yMin': info['cornerCoordinates']['lowerLeft'][1],
        'xMax': info['cornerCoordinates']['upperRight'][0],
        'yMax': info['cornerCoordinates']['upperRight'][1],
        'nRows': info['size'][1],
        'nCols': info['size'][0],
        'nBands': len(info['bands']),
        'PixelType': get_pixel_type(info['bands'][0]['type']),
        'SRS': get_projection(info['coordinateSystem']['wkt']),
        'Tag': tag,
        'GroupName': tag,
        'StartDate': SEASONS[season]['StartDate'],
        'EndDate': SEASONS[season]['EndDate'],
        'ProductType': product_type,
        'Season': SEASONS[season]['Season'],
        'Polarization': polarization,
        'Tile': tile,
        'DownloadURL': download_url,
        'URLDisplay': name,
        'MaxPS': '910',
    }


def update_csv(csv_file: str, rasters: List[str]):
    if os.path.isfile(csv_file):
        with open(csv_file) as f:
            records = [record for record in csv.DictReader(f)]
    else:
        records = []
    logging.info(f'Found {len(records)} items in {csv_file}')

    existing_rasters = [record['Raster'] for record in records]
    new_rasters = set(rasters) - set(existing_rasters)

    logging.info(f'Adding {len(new_rasters)} new items to {csv_file}')
    for raster in new_rasters:
        record = get_raster_metadata(raster)
        records.append(record)

    records = sorted(records, key=lambda x: x['Raster'])
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=records[0].keys(), lineterminator=os.linesep)
        writer.writeheader()
        writer.writerows(records)

def calculate_fields(mosaic_dataset):
    # This function adds custom fields to the mosaic dataset and populates the values for the source rasters.

    try:
        arcpy.management.AddFields(
            in_table=mosaic_dataset,
            field_description=[
                ['StartDate', 'DATE'],
                ['EndDate', 'DATE'],
                ['Season', 'TEXT'],
                ['Polarization', 'TEXT'],
                ['Tile', 'TEXT'],
                ['Dataset_ID', 'TEXT'],
                ['DownloadURL', 'TEXT'],
                ['URLDisplay', 'TEXT']
            ],
        )
    except:
        logging.info('No New Fields Added')

    ds = mosaic_dataset
    ds_cursor = arcpy.da.UpdateCursor(ds, ["Name", "ProductType", "Season", "Polarization", "Tile", "Dataset_ID",
                                           "Tag", "MaxPS", "StartDate", "EndDate", "GroupName", "DownloadURL",
                                           "URLDisplay"])
    if ds_cursor is not None:
        for row in ds_cursor:
            try:
                NameField = row[0]
                ProductTypeField = NameField.split("_")[3]
                SeasonName = NameField.split("_")[1]
                StartDateField = SEASONS[SeasonName]['StartDate'],
                EndDateField = SEASONS[SeasonName]['EndDate'],
                SeasonField = SEASONS[SeasonName]['Season'],
                SeasonCode = SEASONS[SeasonName]['SeasonCode']
                PolarizationField = str(NameField.split("_")[2]).upper()
                TileField = NameField.split("_")[0]
                DatasetIDField = ProductTypeField + '_' + PolarizationField + '_' + SeasonCode
                TagField = DatasetIDField
                MaxPSField = 910
                GroupNameField = DatasetIDField
                DownloadURLField = r'https://sentinel-1-global-coherence-earthbigdata.s3.us-west-' \
                                   r'2.amazonaws.com/data/tiles/{}/{}.tif'.format(TileField, NameField)
                row[1] = ProductTypeField
                row[2] = SeasonField
                row[3] = PolarizationField
                row[4] = TileField
                row[5] = DatasetIDField
                row[6] = TagField
                row[7] = MaxPSField
                row[8] = StartDateField
                row[9] = EndDateField
                row[10] = GroupNameField
                row[11] = DownloadURLField
                row[12] = NameField
                ds_cursor.updateRow(row)
            except Exception as exp:
                print(str(exp))
        del ds_cursor


gdal.UseExceptions()
gdal.SetConfigOption('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR')

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--working-directory', default=os.getcwd())
parser.add_argument('config_file')
args = parser.parse_args()

bucket = 'sentinel-1-global-coherence-earthbigdata'
overview_path = '/vsis3/asf-gis-services/public/GSSICB/'
template_directory = Path(__file__).parent.absolute() / 'raster_function_templates'

with open(args.config_file) as f:
    config = json.load(f)

csv_file = os.path.join(args.working_directory, f'{config["project_name"]}_{config["dataset_name"]}.csv')

raster_function_template = ''.join([f'{template_directory / template};'
                                    for template in config['raster_function_templates']])
if config['default_raster_function_template'] != 'None':
    default_raster_function_template = str(template_directory / config['default_raster_function_template'])
else:
    default_raster_function_template = 'None'

arcpy.env.parallelProcessingFactor = '75%'

rasters = get_rasters(bucket, config['s3_prefix'], config['s3_suffix'])
update_csv(csv_file, rasters)

today = datetime.datetime.now(datetime.timezone.utc).strftime('%y%m%d_%H%M')
output_name = f'{config["project_name"]}_{config["dataset_name"]}_{today}'
overview_name = f'{output_name}_overview'
local_overview_filename = f'{overview_name}.crf'
s3_overview = f'{overview_path}{overview_name}.crf'
service_definition = os.path.join(args.working_directory, f'{output_name}.sd')

try:

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

    logging.info(f'Adding source rasters to {mosaic_dataset}')
    arcpy.management.AddRastersToMosaicDataset(
        in_mosaic_dataset=mosaic_dataset,
        raster_type='Table',
        input_path=csv_file,
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
                            'Tag;GroupName;StartDate;EndDate;ProductType;Season;Polarization;Tile;DownloadURL;URLDisplay',
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

    local_overview = os.path.join(os.getcwd(), local_overview_filename)

    logging.info(f'Generating {local_overview}')
    with arcpy.EnvManager(cellSize=900):
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

    logging.info('Calculating custom fields for overview record')
    selection = arcpy.management.SelectLayerByAttribute(
        in_layer_or_view=mosaic_dataset,
        selection_type='NEW_SELECTION',
        where_clause=f"Name = '{overview_name}'",
    )

    calculate_fields(selection)
    arcpy.management.CalculateFields(
        in_table=selection,
        fields=[
            ['MinPS', '900'],
            ['MaxPS', '144000'],
            ['LowPS', '900'],
            ['HighPS', '144000'],
            ['Category', '2'],
            ['GroupName', '"Mosaic Overview"'],
        ],
    )

except arcpy.ExecuteError:
    logging.error(arcpy.GetMessages())
    raise
