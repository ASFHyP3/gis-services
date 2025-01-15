# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.2]
### Added
- Add `mypy` to [`static-analysis`](.github/workflows/static-analysis.yml)

## [0.7.1]
### Changed
- The [`static-analysis`](.github/workflows/static-analysis.yml) Github Actions workflow now uses `ruff` rather than `flake8` for linting.

## [0.7.0]
### Removed
- Deleted files related to PDC image services.
### Added
- Configuration files for COH24 services
- Added a README file to `/gis-services/image_services/opera/` to describe the OPERA service workflow

## [0.6.9]
### Changed
- Specified specific bucket names for write permissions granted to image server in cloudformation.yml

## [0.6.8]
### Changed
- Updated guidance for publishing services to EGIS Image Server
- Updated approach for tagging datasets and naming conventions for the datasets and services to include the OPERA version number and more descriptive fields for the overview record

## [0.6.7]
### Added
- Script for the use of the EGIS team to generate OPERA RTC mosaic datasets without the publishing step
- Script for the use of the ASF development team to generate services using test buckets instead of EDC source rasters

## [0.6.6]
### Added
- Scripts to generate OPERA RTC services, URL files, and relevant metadata

## [0.6.5]
### Changed
- Changed time slider length to 52 weeks for automated web maps

## [0.6.4]
### Added
- A new hotfix stored in our S3 bucket in `image_server/arcgis_setup.sh`
- Scripts to automatically update time sliders for web maps published by ASF

## [0.6.3]
### Added
- Scripts to generate configuration and metadata files for new datasets

### Changed
- GSSICB services created with `make_egis_services.py` now point to EDC-hosted source rasters in the `asf-ngap2w-p-s1-global-coherence` S3 bucket

## [0.6.2]
### Added
- Newly released ESRI ArcGIS Server 10.9 patch updates to `image_server/arcgis_setup.sh`
- Permissions for image server to write overviews to `s3://asf-gis-services/public/`

## [0.6.1]
### Added
- Documentation for publishing web maps to Earthdata GIS

## [0.6.0]
### Added
- Scripts to generate GSSICB Coherence image services
- Scripts to generate customized metadata content for GSSICB coherence image services
- Config files and service metadata files for all COH06 services

### Changed
- IAM permissions for image server to read from any s3 bucket

## [0.5.1]
### Changed
- Refactored the addRasters retry loop in the make_rtc_service.py and make_sample_service.py scripts to avoid duplicate entries in the mosaic dataset attribute table
- Updated HKH config files to include WMS metadata
- Updated HKH and PDC config files to increase time-out settings

## [0.5.0]
### Added
- code to enable WMS capabilities in service definition files
- Processing script and configuration files to support image services for PDC
- IAM permissions for image server to manage mosaic datasets for `s3://hyp3-pdc-data/`

### Changed
- Refactored the addRasters retry loop in the make_pdc_service.py script to avoid duplicate entries in the mosaic dataset attribute table

## [0.4.1]
### Added
- Parameters in `nasa_disasters` services to set custom service timeouts and repair cycle interval

## [0.4.0]
### Added
- Code and configuration files for generating ASF_SampleData services consistently using a mosaic dataset approach with calculated statistics

## [0.3.6]
### Added
- Resource permission for `hyp3-examples` in `image_server/cloudformation.yml`
### Changed
- URL to the lastest version for the ESRI UNDM4 patch in `image_server/arcgis_setup.sh`
- Server setup now suggests a localhost when creating `server_connection.json`

## [0.3.5]
### Added
- Documentation for publishing services to Earthdata GIS using existing MDCS-generated mosaic datasets
- Sample metadata for GSSICB services
- Documentation for adding ASF-published AGOL content to Earthdata GIS Portal
- Documentation for using the ArcGIS Assistant to update content (particularly services URLs) in web maps

## [0.3.4]
### Added
- Code to generate a perennial water service for the HKH region
### Changed
- Adjusted service definition overrides to set the minInstances to 1 and maxInstances to 9 for all services
 
## [0.3.3]
### Added
- README.md for `make_hand_service.py`
- Service definition overrides for `minInstances` and `maxInstances`for all RTC services

## [0.3.2]
### Changed
- Updated [documentation for server deployment and configuration](image_server/server_setup.md) to support a two-server configuration

## [0.3.1]
### Changed
- The `AddRastersToMosaicDataset` and `publish_sd` steps of `make_rtc_service.py` are now attempted up to three times
  to reduce the impact of intermittent errors.

## [0.3.0]
### Changed
- `make_rtc_service.py` now maintains a CSV table for adding rasters to the mosaic dataset
- support using mambaforge instead of miniconda3 for python environments

## [0.2.0]
### Added
- Configuration files supporting image services for the USDA and HKH Flood Monitoring projects
### Changed
- `rtc_services` directory now has one folder per project (`nasa_disasters`, `usda`) and a shared folder for raster
  function templates
- Updates for `make_rtc_service.py`:
  - `project_name` and `s3_prefix` are now specified in each configuration file rather than hardcoded
  - Default value for `--server-connection-file` is now `/home/arcgis/server_connection.json`

## [0.1.2]
### Added
- Shell script to pull updates from Git and cleanup `.gdb` and `.sd` RTC services added for automation with `crontab`.

## [0.1.1]
### Changed
- Default raster template is now `WatermapExtentBlueOnly` for the `rtc_services/wm` service

## [0.1.0]
### Added
- `image_server/` with resources for deploying ArcGIS Image Server 10.9.1 in AWS
- `image_services/glo_30_hand/` for one-time generation of a mosaic image service of the Global 30m Height Above Nearest
  Drainage (HAND) data set
- `image_services/rtc_services/` for daily generation and publishing of RGB, Water Map, RTC VV, and RTC VH image
  services in support of NASA Disasters
