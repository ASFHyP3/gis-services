# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.2.0]
### Added
- Configuration files supporting image services for the USDA project
### Changed
- `rtc_services` directory now has one folder per project (nasa_disasters, usda) and a shared folder for raster function
  templates
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
