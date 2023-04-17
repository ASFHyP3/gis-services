# Global 30m Height Above Nearest Drainage (HAND)

`make_hand_service.py` attempts to generate a mosaic dataset for the HAND geotiffs under `s3://glo-30-hand/v1/2021/`.

> :warning: `make_hand_service.py` did not create the production mosaic used for the image service at
> https://gis.asf.alaska.edu/arcgis/rest/services/GlobalHAND/GLO30_HAND/ImageServer. The script encounters errors when
> generating an overview for the entire dataset due to projection issues for the geotiffs at the South Pole (S90).
> The mosaic used in production was manually generated to include every geotiff, with an overview layer that excludes
> the S90 geotiffs.
