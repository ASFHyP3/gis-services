import datetime
import subprocess

import arcpy

today = datetime.datetime.now(datetime.timezone.utc).strftime("%y%m%d_%H%M")
project_name = 'RTCservices'
service_name = 'ASF_S1_RGB'
dataset_name = 'RGB'
working_directory = '/home/arcgis/hjkristenson/RTCServices/'
output_name = f'{working_directory}{project_name}_{today}'
raster_store = '/home/arcgis/raster_store/'
s3_path = '/vsis3/hyp3-nasa-disasters/'
s3_prefix = 'RTC_services/'

geodatabase = f'{output_name}.gdb'
mosaic_dataset = f'{geodatabase}/{dataset_name}'
raster_function_template = f'None'
overview_name = f'{project_name}_{dataset_name}_{today}_overview'
local_overview = f'/home/arcgis/raster_store/{overview_name}_{today}.crf'
s3_overview = f'/vsis3/hyp3-nasa-disasters/overviews/{overview_name}_{today}.crf'
service_definition_draft = f'{output_name}.sddraft'
service_definition = f'{output_name}.sd'


arcpy.env.parallelProcessingFactor = '75%'

arcpy.management.CreateFileGDB(
    out_folder_path=working_directory,
    out_name=geodatabase,
)

arcpy.management.CreateMosaicDataset(
    in_workspace=geodatabase,
    in_mosaicdataset_name=dataset_name,
    coordinate_system=3857,
)

arcpy.management.AddFields(
    in_table=mosaic_dataset,
    field_description=[
        ['StartDate', 'DATE'],
        ['EndDate', 'DATE'],
        ['DownloadURL', 'TEXT'],
    ],
)

arcpy.management.AddRastersToMosaicDataset(
    in_mosaic_dataset=mosaic_dataset,
    raster_type='Raster Dataset',
    input_path=f'{s3_path}{s3_prefix}',
    filter='*202302*rgb.tif',
)

arcpy.management.CalculateFields(
    in_table=mosaic_dataset,
    fields=[
        ['GroupName', '!Name!.split(";")[0][:-4]'],
        ['Tag', '!Name!.split("_")[8]'],
        ['MaxPS', '1610'],
        ['StartDate', '!Name!.split("_")[2][4:6] + "/" + !Name!.split("_")[2][6:8] + "/" + !Name!.split("_")[2][:4] + " " + !Name!.split("_")[2][9:11] + ":" + !Name!.split("_")[2][11:13] + ":" + !Name!.split("_")[2][13:15]'],
        ['EndDate', '!Name!.split("_")[2][4:6] + "/" + !Name!.split("_")[2][6:8] + "/" + !Name!.split("_")[2][:4] + " " + !Name!.split("_")[2][9:11] + ":" + !Name!.split("_")[2][11:13] + ":" + !Name!.split("_")[2][13:15]'],
        ['DownloadURL', f'"https://s3-us-west-2.amazonaws.com/hyp3-nasa-disasters/{s3_prefix}!Name!.tif"'],
    ],
)

arcpy.management.BuildFootprints(
    in_mosaic_dataset=mosaic_dataset,
    reset_footprint='NONE',
    min_data_value=0,
    max_data_value=4294967295,
    approx_num_vertices=12,
    update_boundary='UPDATE_BOUNDARY',
)

arcpy.management.BuildBoundary(
    in_mosaic_dataset=mosaic_dataset,
    append_to_existing='OVERWRITE',
    simplification_method='NONE',
)

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
    default_processing_template=raster_function_template,
)

arcpy.management.CalculateCellSizeRanges(
    in_mosaic_dataset=mosaic_dataset,
    do_compute_min='NO_MIN_CELL_SIZES',
    do_compute_max='NO_MAX_CELL_SIZES',
    max_range_factor=10,
    cell_size_tolerance_factor=0.8,
    update_missing_only='UPDATE_ALL',
)

with arcpy.EnvManager(cellSize=1200):
    arcpy.management.CopyRaster(
        in_raster=mosaic_dataset,
        out_rasterdataset=local_overview,
    )

subprocess.run(['aws', 's3', 'cp', local_overview, s3_overview.replace("/vsis3/", "s3://"), '--recursive'])

arcpy.management.AddRastersToMosaicDataset(
    in_mosaic_dataset=mosaic_dataset,
    raster_type='Raster Dataset',
    input_path=s3_overview,
)

# Calculate the date range of the items in the mosaic dataset
ds_cursor = arcpy.da.UpdateCursor(mosaic_dataset, ["Tag", "StartDate"])
stdatelist = []
if (ds_cursor is not None):
    log.Message('Determining Start and End Dates...', 0)
    for row in ds_cursor:
        if row[0] != 'Dataset':
            stdatelist.append(row[1])
    stdate = min(stdatelist)
    endate = min(stdatelist)

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
        ['StartDate', f'{stdate} + datetime.timedelta(hours=-8)'],
        ['EndDate', f'{endate} + datetime.timedelta(hours=8)'],
    ],
)

arcpy.CreateImageSDDraft(
    raster_or_mosaic_layer=mosaic_dataset,
    out_sddraft=service_definition_draft,
    service_name=dataset_name,
    summary="Sentinel-1 RGB Decomposition of RTC VV and VH imagery, processed by ASF. "
            "Blue areas have low returns in VV and VH (smooth surfaces such as calm water, "
            "but also frozen/crusted soil or dry sand), green areas have high returns in VH (volume "
            "scatterers such as vegetation or some types of snow/ice), and red areas have relatively high VV "
            "returns and relatively low VH returns (such as urban or sparsely vegetated areas).",
)

arcpy.server.StageService(
    in_service_definition_draft=service_definition_draft,
    out_service_definition=service_definition,
)
