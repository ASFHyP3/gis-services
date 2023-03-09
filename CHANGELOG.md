# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


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
