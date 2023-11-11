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


# def get_rasters(bucket: str, prefix: str, suffix: str) -> List[str]:
#     rasters = []
#     s3 = boto3.client('s3')
#     paginator = s3.get_paginator('list_objects_v2')
#     for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
#         for obj in page['Contents']:
#             if obj['Key'].endswith(suffix):
#                 rasters.append(f'/vsis3/{bucket}/{obj["Key"]}')
#     return rasters


def get_rasters(url_file):
    with open(url_file, newline='') as urlfile:
        records = urlfile.read().split('\n')[:-1]
    return records


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


def remove_prefix(raster_path, prefix):
    return raster_path[len(prefix):]


def get_raster_metadata(raster_path: str, bucket: str, s3_prefix: str) -> dict:
    #assert raster_path.startswith(f'/vsis3/{bucket}/{s3_prefix}/')
    key = remove_prefix(raster_path, f'/vsis3/{bucket}/')
    download_url = f'https://hyp3-testing.s3.us-west-2.amazonaws.com/{key}'
    name = Path(raster_path).stem
    acquisition_date = \
        name[36:38] + '/' + name[38:40] + '/' + name[32:36] + ' ' + name[41:43] + ':' + name[43:45] + ':' + name[45:47]
    info = gdal.Info(raster_path, format='json')
    return {
        'Raster': info['description'],
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
        'DownloadURL': download_url,
        'URLDisplay': name,
        'Polarization': name.split('_')[9],
        'StartDate': acquisition_date,
        'EndDate': acquisition_date,
    }


def update_csv(csv_file: str, rasters: List[str], bucket: str, s3_prefix: str):
    if os.path.isfile(csv_file):
        with open(csv_file) as f:
            records = [record for record in csv.DictReader(f)]
    else:
        records = []
    logging.info(f'Found {len(records)} items in {csv_file}')

    existing_rasters = [record['Raster'] for record in records]
    new_rasters = set(rasters) - set(existing_rasters)
    logging.info(f'Adding {len(new_rasters)} new items to {csv_file}')

    if new_rasters:
        header_record = get_raster_metadata(next(iter(new_rasters)), bucket, s3_prefix)
        with open(csv_file, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=header_record.keys(), lineterminator=os.linesep)
            if not existing_rasters:
                writer.writeheader()
            for raster in new_rasters:
                record = get_raster_metadata(raster, bucket, s3_prefix)
                writer.writerow(record)

    with open(csv_file) as f:
        records = [record for record in csv.DictReader(f)]
    logging.info(f'Sorting rasters in {csv_file}')
    records = sorted(records, key=lambda x: x['EndDate'])
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=records[0].keys(), lineterminator=os.linesep)
        writer.writeheader()
        writer.writerows(records)


def calculate_overview_fields(mosaic_dataset, local_path):
    # This function calculates custom attribute values for the overview record
    print('Calculating field values for overview record')
    ds = os.path.join(local_path, mosaic_dataset)
    ds_cursor = arcpy.da.UpdateCursor(ds, ['Tag', 'MinPS', 'Category', 'StartDate', 'EndDate', 'GroupName',
                                           'Name', 'Polarization', 'DownloadURL', 'URLDisplay'])

    logging.info('Calculating Overview Start and End Dates')
    start_dates = [row[1] for row in arcpy.da.SearchCursor(mosaic_dataset, ['Tag', 'StartDate']) if row[0] != 'Dataset']
    overview_start_date = min(start_dates).replace(microsecond=0) + datetime.timedelta(hours=-8)
    overview_end_date = max(start_dates).replace(microsecond=0) + datetime.timedelta(hours=8)

    if ds_cursor is not None:
        print('Updating Overview Field Values')
        for row in ds_cursor:
            if row[0] == 'Dataset':
                ProjectName, ProdTypeOvField, PolOvField, _, _, _ = row[6].split('_')

                DLOvField = 'Zoom in further to access download link'

                row[0] = f'{ProjectName}_{ProdTypeOvField}_{PolOvField}_Overview'
                row[1] = 450
                row[2] = 2
                row[3] = overview_start_date
                row[4] = overview_end_date
                row[5] = f'{ProjectName}_{ProdTypeOvField}_{PolOvField} Mosaic Overview'
                row[7] = PolOvField
                row[8] = DLOvField
                row[9] = DLOvField

                ds_cursor.updateRow(row)
                print('Overview fields updated')
        del ds_cursor


def add_property(property_set: etree.Element, property_key: str, property_value: str) -> None:
    xsi_type = etree.QName('http://www.w3.org/2001/XMLSchema-instance', 'type')
    prop = etree.SubElement(property_set, 'PropertySetProperty', {xsi_type: 'typens:PropertySetProperty'})
    etree.SubElement(prop, 'Key').text = property_key
    etree.SubElement(prop, 'Value', {xsi_type: 'xs:string'}).text = property_value


def build_wms_extension() -> etree.Element:
    xsi_type = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "type")

    svc_extension = etree.Element('SVCExtension', {xsi_type: 'typens:SVCExtension'})

    etree.SubElement(svc_extension, 'Enabled').text = 'true'
    etree.SubElement(svc_extension, 'TypeName').text = 'WMSServer'

    property_set = etree.SubElement(svc_extension, 'Props', {xsi_type: 'typens:PropertySet'})
    property_array = etree.SubElement(property_set, 'PropertyArray', {xsi_type: 'typens:ArrayOfPropertySetProperty'})
    add_property(property_array, 'name', 'WMS')
    add_property(property_array, 'contactOrganization', 'Alaska Satellite Facility')
    add_property(property_array, 'address', '2156 Koyukuk Drive')
    add_property(property_array, 'addressType', 'physical')
    add_property(property_array, 'city', 'Fairbanks')
    add_property(property_array, 'stateOrProvince', 'Alaska')
    add_property(property_array, 'country', 'US')
    add_property(property_array, 'contactVoiceTelephone', '907-474-5041')
    add_property(property_array, 'contactElectronicMailAddress', 'uso@asf.alaska.edu')
    add_property(property_array, 'accessConstraints',
                 'There are no restrictions on the use of this data, but it must be acknowledged or '
                 'cited as follows: "This imagery was generated by ASF DAAC HyP3 using GAMMA software. '
                 'Contains modified Copernicus Sentinel data, processed by ESA."')
    add_property(property_array, 'title', '')
    add_property(property_array, 'abstract', '')

    info_property_set = etree.SubElement(svc_extension, 'Info', {xsi_type: 'typens:PropertySet'})
    info_property_array = etree.SubElement(info_property_set, 'PropertyArray',
                                           {xsi_type: 'typens:ArrayOfPropertySetProperty'})
    add_property(info_property_array, 'WebEnabled', 'true')
    add_property(info_property_array, 'WebCapabilities',
                 'GetCapabilities,GetMap,GetFeatureInfo,GetStyles,GetLegendGraphic,GetSchemaExtension')

    return svc_extension


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--working-directory', default=os.getcwd())
    parser.add_argument('--server-connection-file', default='/home/arcgis/server_connection.json')
    parser.add_argument('config_file')
    args = parser.parse_args()

    template_directory = Path(__file__).parent.absolute() / 'raster_function_templates'

    with open(args.config_file) as f:
        config = json.load(f)

    url_file = '/home/arcgis/gis-services/image_services/opera/urls.txt'
    csv_file = os.path.join(args.working_directory, f'{config["project_name"]}_{config["dataset_name"]}.csv')

    raster_function_template = ''.join([f'{template_directory / template};'
                                        for template in config['raster_function_templates']])
    if config['default_raster_function_template'] != 'None':
        default_raster_function_template = str(template_directory / config['default_raster_function_template'])
    else:
        default_raster_function_template = 'None'

    arcpy.env.parallelProcessingFactor = '75%'

    try:
        #rasters = get_rasters(config['bucket'], config['s3_prefix'], config['s3_suffix'])
        rasters = get_rasters(url_file)
        update_csv(csv_file, rasters, config['bucket'], config['s3_prefix'])

        for attempt in Retrying(stop=stop_after_attempt(3), wait=wait_fixed(60), reraise=True,
                                before_sleep=before_sleep_log(logging, logging.WARNING)):
            with attempt:
                today = datetime.datetime.now(datetime.timezone.utc).strftime('%y%m%d_%H%M')
                output_name = f'{config["project_name"]}_{config["dataset_name"]}_{today}'
                overview_name = f'{output_name}_overview'
                local_overview_filename = f'{overview_name}.crf'
                s3_overview = f'{config["overview_path"]}{overview_name}.crf'
                service_definition = os.path.join(args.working_directory, f'{output_name}.sd')

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
            transmission_fields='Name;StartDate;EndDate;MinPS;MaxPS;LowPS;HighPS;Date;Dataset_ID;CenterX;'
                                'CenterY;Tag;GroupName;Polarization;DownloadURL;URLDisplay',
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

        logging.info(f'Calculating custom field values in {mosaic_dataset}')
        arcpy.management.CalculateFields(
            in_table=mosaic_dataset,
            fields=[
                ['MaxPS', '460'],
                ['Tag', '"_".join(!Name!.split("_")[0:3] + [!Name!.split("_")[9]])'],
                ['GroupName', '!Name!.rsplit("_", 1)[0]'],
            ],
        )
        with tempfile.TemporaryDirectory(dir=config['raster_store']) as temp_dir:
            local_overview = os.path.join(temp_dir, local_overview_filename)

            logging.info(f'Generating {local_overview}')
            with arcpy.EnvManager(cellSize=450):
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

        logging.info('Populate overview attributes')
        calculate_overview_fields(mosaic_dataset, args.working_directory)

        with tempfile.NamedTemporaryFile(suffix='.sddraft') as service_definition_draft:
            logging.info(f'Creating draft service definition {service_definition_draft.name}')
            arcpy.CreateImageSDDraft(
                raster_or_mosaic_layer=mosaic_dataset,
                out_sddraft=service_definition_draft.name,
                service_name=config['service_name'],
            )

            tree = etree.parse(service_definition_draft.name)

            logging.info(f'Enabling WMS in {service_definition_draft.name}')
            extensions = tree.find('/Configurations/SVCConfiguration/Definition/Extensions')
            extensions.append(build_wms_extension())

            logging.info(f'Editing service definition overrides for {service_definition_draft.name}')
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

        for attempt in Retrying(stop=stop_after_attempt(3), reraise=True,
                                before_sleep=before_sleep_log(logging, logging.WARNING)):
            with attempt:
                logging.info(f'Publishing {service_definition}')
                server = Server(**server_connection)
                server.publish_sd(service_definition, folder=config['service_folder'])

    except arcpy.ExecuteError:
        logging.error(arcpy.GetMessages())
        raise


if __name__ == '__main__':
    main()
