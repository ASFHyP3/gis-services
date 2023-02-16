import arcpy


arcpy.management.CreateFileGDB(
    out_folder_path='/home/arcgis/asjohnston/',
    out_name='hand.gdb',
)

arcpy.management.CreateMosaicDataset(
    in_workspace='/home/arcgis/asjohnston/hand.gdb',
    in_mosaicdataset_name='hand',
    coordinate_system=3857,
)

arcpy.management.AddFields(
    in_table='/home/arcgis/asjohnston/hand.gdb/hand',
    field_description=[
        ['Tile', 'TEXT'],
        ['DownloadURL', 'TEXT'],
        ['URLDisplay', 'TEXT'],
        ['Dataset_ID', 'TEXT'],
    ],
)

arcpy.management.CreateCloudStorageConnectionFile(
    out_folder_path='/home/arcgis/asjohnston/',
    out_name='hand.acs',
    service_provider='AMAZON',
    bucket_name='glo-30-hand',
    region='us-west-2',
    config_options='AWS_NO_SIGN_REQUEST=YES',
    folder='v1/2021/',
)

arcpy.management.AddRastersToMosaicDataset(
    in_mosaic_dataset='/home/arcgis/asjohnston/hand.gdb/hand',
    raster_type='Raster Dataset',
    input_path='/home/arcgis/asjohnston/hand.acs',
    filter='*Copernicus_DSM_COG_10_N0*',
)

arcpy.management.CalculateFields(
    in_table='/home/arcgis/asjohnston/hand.gdb/hand',
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

arcpy.management.BuildFootprints(
    in_mosaic_dataset='/home/arcgis/asjohnston/hand.gdb/hand',
    reset_footprint='NONE',
    min_data_value=0,
    max_data_value=1,
    approx_num_vertices=12,
    update_boundary='UPDATE_BOUNDARY',
)

arcpy.management.BuildBoundary(
    in_mosaic_dataset='/home/arcgis/asjohnston/hand.gdb/hand',
    append_to_existing='OVERWRITE',
    simplification_method='NONE',
)

arcpy.management.SetMosaicDatasetProperties(
    in_mosaic_dataset='/home/arcgis/asjohnston/hand.gdb/hand',
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
    processing_templates='/home/arcgis/asjohnston/GLO30_HAND_2SDstretch.rft.xml;None',
    default_processing_template='/home/arcgis/asjohnston/GLO30_HAND_2SDstretch.rft.xml',
)

arcpy.management.CalculateCellSizeRanges(
    in_mosaic_dataset='/home/arcgis/asjohnston/hand.gdb/hand',
    do_compute_min='NO_MIN_CELL_SIZES',
    do_compute_max='NO_MAX_CELL_SIZES',
    max_range_factor=10,
    cell_size_tolerance_factor=0.8,
    update_missing_only='UPDATE_ALL',
)

with arcpy.EnvManager(parallelProcessingFactor=7, cellSize=600):
    arcpy.management.CopyRaster(
        in_raster='/home/arcgis/asjohnston/hand.gdb/hand',
        out_rasterdataset='/home/arcgis/raster_store/hand_overview.crf',
    )

input('aws s3 cp /home/arcgis/raster_store/hand_overview.crf s3://hyp3-nasa-disasters/overviews/hand_overview.crf --recursive')

arcpy.management.AddRastersToMosaicDataset(
    in_mosaic_dataset='/home/arcgis/asjohnston/hand.gdb/hand',
    raster_type='Raster Dataset',
    input_path='/vsis3/hyp3-nasa-disasters/overviews/hand_overview.crf',
)

selection = arcpy.management.SelectLayerByAttribute(
    in_layer_or_view='/home/arcgis/asjohnston/hand.gdb/hand',
    selection_type='NEW_SELECTION',
    where_clause="Name = 'hand_overview'",
)
arcpy.management.CalculateFields(
    in_table=selection,
    fields=[
        ['MinPS', '600'],
        ['Category', '2'],
        ['ProductName', '"COP30_HAND_Overview"'],
        ['Tag', '"COP30_HAND_Overview"'],
        ['Tile', '"Zoom in further to see specific tile information"'],
        ['URLDisplay', '"Zoom in further to access download link"'],
    ],
)

arcpy.CreateImageSDDraft(
    raster_or_mosaic_layer='/home/arcgis/asjohnston/hand.gdb/hand',
    out_sddraft='/home/arcgis/asjohnston/hand.sddraft',
    service_name='HAND',
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

arcpy.server.StageService(
    in_service_definition_draft='/home/arcgis/asjohnston/hand.sddraft',
    out_service_definition='/home/arcgis/asjohnston/hand.sd',
)
