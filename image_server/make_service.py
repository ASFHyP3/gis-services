import arcpy
import configparser

def make_service(cfg):
    
    gdb_dir = cfg['gdb_dir']
    gdb_name = cfg['gdb_name']
    dataset_name = cfg['dataset_name']

    mosaic_dataset = f'{gdb_dir}/{gdb_name}/{dataset_name}'

    arcpy.management.CreateFileGDB(
        out_folder_path=f'{gdb_dir}/',
        out_name=f'{gdb_name}',
    )

    arcpy.management.CreateMosaicDataset(
        in_workspace=f'{gdb_dir}/{gdb_name}',
        in_mosaicdataset_name=f'{dataset_name}',
        coordinate_system=3857,
    )

    arcpy.management.AddFields(
        in_table=f'{gdb_dir}/{gdb_name}/{dataset_name}',
        field_description=[
            ['Tile', 'TEXT'],
            ['DownloadURL', 'TEXT'],
            ['URLDisplay', 'TEXT'],
            ['Dataset_ID', 'TEXT'],
        ],
    )

    arcpy.management.CreateCloudStorageConnectionFile(
        out_folder_path=f'{gdb_dir}/',
        out_name=f'{dataset_name}.acs',
        service_provider='AMAZON',
        bucket_name='glo-30-hand',
        region='us-west-2',
        config_options='AWS_NO_SIGN_REQUEST=YES',
        folder='v1/2021/',
    )

    arcpy.management.AddRastersToMosaicDataset(
        in_mosaic_dataset=mosaic_dataset,
        raster_type='Raster Dataset',
        input_path=f'{gdb_dir}/{dataset_name}.acs',
        filter='*HAND.tif',
    )

    arcpy.management.CalculateFields(
        in_table=f'{gdb_dir}/{gdb_name}/{dataset_name}',
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
        in_mosaic_dataset=mosaic_dataset,
        reset_footprint='NONE',
        min_data_value=0,
        max_data_value=1,
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
        processing_templates=f'{gdb_dir}/GLO30_HAND_2SDstretch.rft.xml;None',
        default_processing_template=f'{gdb_dir}/GLO30_HAND_2SDstretch.rft.xml',
    )

    arcpy.management.CalculateCellSizeRanges(
        in_mosaic_dataset=mosaic_dataset,
        do_compute_min='NO_MIN_CELL_SIZES',
        do_compute_max='NO_MAX_CELL_SIZES',
        max_range_factor=10,
        cell_size_tolerance_factor=0.8,
        update_missing_only='UPDATE_ALL',
    )

    with arcpy.EnvManager(pyramid='PYRAMIDS 3', parallelProcessingFactor=7, cellSize=600):
        arcpy.management.CopyRaster(
            in_raster=mosaic_dataset,
            out_rasterdataset='/home/arcgis/raster_store/hand_overview_global_pyramid3.crf',
        )

    input('aws s3 cp /home/arcgis/raster_store/hand_overview_global_pyramid3.crf s3://hyp3-nasa-disasters/overviews/hand_overview_global_pyramid3.crf --recursive')

    arcpy.management.AddRastersToMosaicDataset(
        in_mosaic_dataset=mosaic_dataset,
        raster_type='Raster Dataset',
        input_path='/vsis3/hyp3-nasa-disasters/overviews/hand_overview_global_pyramid3.crf',
    )

    selection = arcpy.management.SelectLayerByAttribute(
        in_layer_or_view=mosaic_dataset,
        selection_type='NEW_SELECTION',
        where_clause="Name = 'hand_overview_global_pyramid3'",
    )
    arcpy.management.CalculateFields(
        in_table=selection,
        fields=[
            ['MinPS', '600'],
            ['Category', '2'],
        ],
    )

    arcpy.CreateImageSDDraft(
        raster_or_mosaic_layer=mosaic_dataset,
        out_sddraft=f'{gdb_dir}/hand.sddraft',
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
        in_service_definition_draft=f'{gdb_dir}/hand.sddraft',
        out_service_definition=f'{gdb_dir}/hand.sd',
    )


config = configparser.RawConfigParser()

config.read('config.cfg')

cfg = dict(config.items('GDB'))

make_service(cfg)

print('completed ...')


