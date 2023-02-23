import argparse
import os
import subprocess
import tempfile

import arcpy

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('working_directory')
parser.add_argument('--dataset-name', default='GLO30_HAND', help='Dataset name.')
parser.add_argument(
    '--rasters-filter',
    default='REGEX:.*Copernicus_DSM_COG_10_[NS][0-8]\d_00_[EW]\d\d\d_00_HAND.tif',
    help=(
        'Rasters from the glo-30-hand collection will be selected using this '
        'filter before they are added to the mosaic dataset. The syntax is as '
        'expected by the `filter` option of arcpy.management.AddRastersToMosaicDataset.'
    )
)
args = parser.parse_args()


dataset_name = args.dataset_name
working_directory = args.working_directory
raster_store = '/home/arcgis/raster_store/'

geodatabase = f'{working_directory}{dataset_name}.gdb'
mosaic_dataset = f'{geodatabase}/{dataset_name}'
raster_function_template = f'{working_directory}GLO30_HAND_2SDstretch.rft.xml'
overview_name = f'{dataset_name}_Overview'
local_overview_filename = f'{overview_name}.crf'
s3_overview = f'/vsis3/hyp3-nasa-disasters/overviews/{overview_name}.crf'
service_definition = f'{working_directory}{dataset_name}.sd'


arcpy.env.parallelProcessingFactor = '75%'

try:
    print('CreateFileGDB')
    arcpy.management.CreateFileGDB(
        out_folder_path=working_directory,
        out_name=f'{dataset_name}.gdb',
    )

    print('CreateMosaicDataset')
    arcpy.management.CreateMosaicDataset(
        in_workspace=geodatabase,
        in_mosaicdataset_name=dataset_name,
        coordinate_system=3857,
    )

    print('AddFields')
    arcpy.management.AddFields(
        in_table=mosaic_dataset,
        field_description=[
            ['Tile', 'TEXT'],
            ['DownloadURL', 'TEXT'],
            ['URLDisplay', 'TEXT'],
            ['Dataset_ID', 'TEXT'],
        ],
    )

    print('AddRastersToMosaicDataset')
    arcpy.management.AddRastersToMosaicDataset(
        in_mosaic_dataset=mosaic_dataset,
        raster_type='Raster Dataset',
        input_path='/vsis3/glo-30-hand/v1/2021/',
        filter=args.rasters_filter,
    )

    print('CalculateFields')
    arcpy.management.CalculateFields(
        in_table=mosaic_dataset,
        fields=[
            ['Tile', '!Name!.split("_")[4] + !Name!.split("_")[6]'],
            ['Tag', '"GLO30_HAND"'],
            ['Dataset_ID', '"Global_30m_HAND"'],
            ['ProductName', '"GLO30_HAND_"+ !Name!.split("_")[4] + !Name!.split("_")[6]'],
            ['URLDisplay', '"GLO30_HAND_"+ !Name!.split("_")[4] + !Name!.split("_")[6]'],
            ['DownloadURL', '"https://glo-30-hand.s3.amazonaws.com/v1/2021/" + !Name! + ".tif"'],
            ['MaxPS', '610'],
        ],
    )

    print('BuildFootprints')
    arcpy.management.BuildFootprints(
        in_mosaic_dataset=mosaic_dataset,
        reset_footprint='NONE',
        min_data_value=0,
        max_data_value=1,
        approx_num_vertices=12,
        update_boundary='UPDATE_BOUNDARY',
    )

    print('BuildBoundary')
    arcpy.management.BuildBoundary(
        in_mosaic_dataset=mosaic_dataset,
        append_to_existing='OVERWRITE',
        simplification_method='NONE',
    )

    print('SetMosaicDatasetProperties')
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
        order_field='Name',
        sorting_order='Ascending',
        mosaic_operator='FIRST',
        blend_width=10,
        view_point_x=300,
        view_point_y=300,
        max_num_per_mosaic=50,
        cell_size_tolerance=1.8,
        cell_size=3,
        metadata_level='BASIC',
        transmission_fields='Name;MinPS;MaxPS;LowPS;HighPS;ZOrder;Dataset_ID;CenterX;CenterY;Tag;Tile;ProductName;DownloadURL;URLDisplay',
        use_time='DISABLED',
        max_num_of_download_items=50,
        max_num_of_records_returned=2000,
        processing_templates=f'{raster_function_template};None',
        default_processing_template=raster_function_template,
    )

    print('CalculateCellSizeRanges')
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
        with arcpy.EnvManager(cellSize=600):
            print(f'CopyRaster from {mosaic_dataset} to {local_overview}')
            arcpy.management.CopyRaster(
                in_raster=mosaic_dataset,
                out_rasterdataset=local_overview,
            )

        print('aws s3 cp')
        subprocess.run(['aws', 's3', 'cp', local_overview, s3_overview.replace("/vsis3/", "s3://"), '--recursive'])

    print('AddRastersToMosaicDataset')
    arcpy.management.AddRastersToMosaicDataset(
        in_mosaic_dataset=mosaic_dataset,
        raster_type='Raster Dataset',
        input_path=s3_overview,
    )

    print('SelectLayerByAttribute')
    selection = arcpy.management.SelectLayerByAttribute(
        in_layer_or_view=mosaic_dataset,
        selection_type='NEW_SELECTION',
        where_clause=f"Name = '{overview_name}'",
    )
    print('CalculateFields')
    arcpy.management.CalculateFields(
        in_table=selection,
        fields=[
            ['MinPS', '600'],
            ['Category', '2'],
            ['ProductName', f'"{overview_name}"'],
            ['Tag', f'"{overview_name}"'],
            ['Tile', '"Zoom in further to see specific tile information"'],
            ['URLDisplay', '"Zoom in further to access download link"'],
        ],
    )

    with tempfile.NamedTemporaryFile(suffix='.sddraft') as service_definition_draft:
        print(f'CreateImageSDDraft: {service_definition_draft.name}')
        arcpy.CreateImageSDDraft(
            raster_or_mosaic_layer=mosaic_dataset,
            out_sddraft=service_definition_draft.name,
            service_name=dataset_name,
            summary="Height Above Nearest Drainage (HAND) is a terrain model that normalizes topography to the relative " \
                        "heights along the drainage network and is used to describe the relative soil gravitational potentials " \
                        "or the local drainage potentials. Each pixel value represents the vertical distance to the nearest " \
                        "drainage. The HAND data provides near-worldwide land coverage at 30 meters and was produced from " \
                        "the 2021 release of the Copernicus GLO-30 Public DEM as distributed in the Registry of Open Data on " \
                        "AWS (https://registry.opendata.aws/copernicus-dem/) using the the ASF Tools Python Package " \
                        "(https://hyp3-docs.asf.alaska.edu/tools/asf_tools_api/#asf_tools.hand.calculate) and the PySheds " \
                        "Python library (https://github.com/mdbartos/pysheds). The HAND data are provided as a tiled set of " \
                        "Cloud Optimized GeoTIFFs (COGs) with 30-meter (1 arcsecond) pixel spacing. The COGs are organized " \
                        "into the same 1 degree by 1 degree grid tiles as the GLO-30 DEM, and individual tiles are " \
                        "pixel-aligned to the corresponding COG DEM tile.",
        )

        print('StageService')
        arcpy.server.StageService(
            in_service_definition_draft=service_definition_draft.name,
            out_service_definition=service_definition,
        )
except arcpy.ExecuteError:
    print(arcpy.GetMessages())
    raise
