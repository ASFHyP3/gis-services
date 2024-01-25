OPERA GIS Services
=========
**_A workflow for programatically standing up an OPERA Image Service_**
-----

## Steps for creating a service
Below are the steps to create an image service using OPERA data. 

### 1. Check permissions and server set up
Prior to running the workflow, ensure that permissions are granted to pull from the EDC-hosted S3 bucket `asf-cumulus-prod-opera-products` and push and pull from a separate S3 bucket for overviews. 

Ensure that the `arcpy` conda environment is created and activated. 
```
cd /home/arcgis/gis-services/image_server/
mamba env create -f environment.yml
conda env activate arcpy
```

Check there is a server connection json file. This workflow will assume that this file will be in the home directory (`/home/arcgis`). If there is another location for this file, make sure to enter its location as an argument [when running the code](#Run-the-image-services-code).

### 2. Set up appropriate config file
The rest of this workflow will require a configuration file to populate the image service. This configuration *must* include: 
- `project_name` : the project name
- `raster_store`: A place to store rasters locally 
- `bucket`: the S3 bucket in which the source rasters are located
- `overview_path`: vsis3 path where overviews will be stored
- `s3_suffix`: suffix of desired rasters (generally the polarization and file extension)
- `opera_version`: version of the OPERA project for desired rasters (so far there is just `V1`)
- `dataset_name`: name of dataset with which local files and tags will be named
- `raster_function_templates`: list of possible raster functions to be used. Only the `default_raster_function_template` *must* be listed
- `default_raster_function_template`: raster function template most useful that will be used by default
- `service_folder`: folder on the service management site where the image service will be saved
- `service_name`: name of the service on the server site and ArcOnline

The service definition overrides are required for metadata but not as critical for the creation steps. Feel free to copy [an existing configuration file](config) and update it for your needs, as most of the information remains consistent across services.

### 3. Create a list of URIs to include
This workflow uses a list of raster vsis3 URIs to specify desired rasters. This is created using the `update_opera_urls.py` and can be automated to run on a cron job using `update_opera_urls.sh` so that the latest rasters are included. The script `update_opera_urls.py` can be updated to include limiting search parameters. This must be run for each unique dataset name. If there are major updates to the list of rasters, it may be useful to delete the existing url csv and re-run for an updated list.

You will need to specify the configuration file and working directory. The working directory parameter is optional. 
```
python /home/arcgis/gis-services/image_services/opera/update_opera_urls.py /home/arcgis/gis-services/image_services/opera/config/rtc_vv.json --working_directory /home/arcgis/gis-services/image_services/opera
```

### 4. Run the image services code
In your working directory, run `make_opera_services.py` with the configuration file created in the previous step. If you are not running from the working directory, specify the directory in which you want the resulting `csv`, `gdb`, and `sd` files to be saved with the `--curent-working-directory` tag. If your server connection file lives outside of the home directory, specify its location with the `--server-connection-file` tag. 
```
python home/arcgis/gis-services/image_services/opera/make_opera_services.py home/arcgis/gis-services/image_services/opera/config/rtc_vv.json
```
Common issues result from server permission errors and server connection glitches. Services can take a while to create, so if you are unsure if there's progress, check that the `.csv` file is gaining entries. 

### 5. Check your image services! 
Log on to your image service manager and check that everything worked as expected! 
In our experience, if you successfully run the workflow, the image services work as expected. Permissions-related issues are common and can arise if the server does not have access to the mosaiced rasters. Make sure you can zoom in and out to different levels, ensuring to check overviews and if rasters load. The services time out if loading takes more than a minute, so the browser's developer tools can be useful to check how long each layer takes to load. We also check that the features in the table matches the number of rasters plus an overview layer.
