import arcpy
from arcpy import metadata as md

# Create a new Metadata object and add some content to it
new_md = md.Metadata()
new_md.title = 'GLO30_HAND Image Service'
new_md.tags = 'HAND, Height, Above, Nearest, Drainage, ASF, Alaska, Satellite, Facility, Copernicus, DEM, GLO-30'
new_md.summary = 'This image service provides access to a global dataset for Height Above Nearest Drainage (HAND), ' \
                 'generated from the Copernicus GLO-30 DEM by the Alaska Satellite Facility (ASF).'
new_md.description = 'Height Above Nearest Drainage (HAND) is a terrain model that normalizes topography to the ' \
                     'relative heights along the drainage network and is used to describe the relative soil ' \
                     'gravitational potentials or the local drainage potentials. Each pixel value represents the ' \
                     'vertical distance to the nearest drainage. The HAND data provides near-worldwide land ' \
                     'coverage at 30 meters and was produced from the 2021 release of the Copernicus GLO-30 ' \
                     'Public DEM as distributed in the Registry of Open Data on AWS ' \
                     '(https://registry.opendata.aws/copernicus-dem/) using the the ASF Tools Python Package ' \
                     '(https://hyp3-docs.asf.alaska.edu/tools/asf_tools_api/#asf_tools.hand.calculate) and the ' \
                     'PySheds Python library (https://github.com/mdbartos/pysheds). The HAND data are provided ' \
                     'as a tiled set of Cloud Optimized GeoTIFFs (COGs) with 30-meter (1 arcsecond) pixel spacing. ' \
                     'The COGs are organized into the same 1 degree by 1 degree grid tiles as the GLO-30 DEM, ' \
                     'and individual tiles are pixel-aligned to the corresponding COG DEM tile.'
new_md.credits = 'Copyright 2022 Alaska Satellite Facility (ASF). Produced using the Copernicus WorldDEM(TM)-30 ' \
                   '(c) DLR e.V. 2010-2014 and (c) Airbus Defence and Space GmbH 2014-2018 provided under ' \
                   'COPERNICUS by the European Union and ESA; all rights reserved. The use of the HAND data falls ' \
                   'under the terms and conditions of the Creative Commons Attribution 4.0 ' \
                   'International Public License.'
new_md.accessConstraints = 'under construction'

# Assign the Metadata object's content to a target item
# hand_path = r'C:\Users\hjkristenson\Documents\ImageServer\ImageServices\arcgis on gis-test.asf.alaska.edu.ags\GlobalHAND\GLO30_HAND_small'
# hand_path = r'https://gis-test.asf.alaska.edu/arcgis/rest/services/GlobalHAND/GLO30_HAND_small/ImageServer/info/metadata'
hand_path = r'https://gis-test.asf.alaska.edu/arcgis/rest/services/GlobalHAND/GLO30_HAND_small/ImageServer'

tgt_item_md = md.Metadata(hand_path)
print('is read only: %s' % tgt_item_md.isReadOnly)  # verify that the target is, indeed, read only
print(tgt_item_md.description)  # verify that it's hitting the right target

if not tgt_item_md.isReadOnly:
    tgt_item_md.copy(new_md)
    print('copying new metadata')
    tgt_item_md.save()
    print('new metadata saved')
else:
    print('item is read only')
