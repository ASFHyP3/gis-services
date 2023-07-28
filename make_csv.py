import argparse
import csv
import glob
import os
from pathlib import Path

from osgeo import osr, gdal

gdal.SetConfigOption('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR')

SEASONS = {
    'summer': {
        'SeasonCode': 'JJA',
        'Season': 'June/July/August',
        'StartDate': '06/01/2020',
        'EndDate': '08/31/2020',
    },
    'fall': {
        'SeasonCode': 'SON',
        'Season': 'September/October/November',
        'StartDate': '09/01/2020',
        'EndDate': '11/30/2020',
    },
    'winter': {
        'SeasonCode': 'DJF',
        'Season': 'December/January/February',
        'StartDate': '12/01/2019',
        'EndDate': '02/29/2020',
    },
    'spring': {
        'SeasonCode': 'MAM',
        'Season': 'March/April/May',
        'StartDate': '03/01/2020',
        'EndDate': '05/31/2020',
    }
}


def get_pixel_type(data_type: str) -> int:
    if data_type == 'Byte':
        return 3
    if data_type == 'Float32':
        return 9
    raise ValueError(f'Unsupported data type: {data_type}')


def get_projection(srs_wkt: str) -> str:
    srs = osr.SpatialReference()
    srs.ImportFromWkt(srs_wkt)
    return srs.GetAttrValue('AUTHORITY', 1)


def get_raster_metadata(raster_path: str) -> dict:
    assert raster_path.startswith('/vsis3/sentinel-1-global-coherence-earthbigdata/')
    key = raster_path.removeprefix('/vsis3/sentinel-1-global-coherence-earthbigdata/')
    download_url = f'https://sentinel-1-global-coherence-earthbigdata.s3.us-west-2.amazonaws.com/{key}'

    info = gdal.Info(raster_path, format='json')
    assert info['description'] == raster_path

    name = Path(info['description']).stem
    tile, season, polarization, product_type = name.split('_')
    polarization = polarization.upper()
    tag = f'{product_type}_{polarization}_{SEASONS[season]["SeasonCode"]}'
    metadata = {
        'Raster': info['description'],
        'Name': name,
        'xMin': info['cornerCoordinates']['lowerLeft'][0],
        'yMin': info['cornerCoordinates']['lowerLeft'][1],
        'xMax': info['cornerCoordinates']['upperRight'][0],
        'yMax': info['cornerCoordinates']['upperRight'][1],
        'nRows': info['size'][1],
        'nCols': info['size'][0],
        'nBands': len(info['bands']),
        'PixelType': get_pixel_type(info['bands'][0]['type']),
        'SRS': get_projection(info['coordinateSystem']['wkt']),
        'Tag': tag,
        'GroupName': tag,
        'StartDate': SEASONS[season]['StartDate'],
        'EndDate': SEASONS[season]['EndDate'],
        'ProductType': product_type,
        'Season': SEASONS[season]['Season'],
        'Polarization': polarization,
        'Tile': tile,
        'DownloadURL': download_url,
        'URLDisplay': name,
    }
    return metadata


def make_csv(csv_file: str, rasters: list[str]):
    assert len(rasters) == len(set(rasters))

    print(f'Adding {len(rasters)} new items to {csv_file}')

    records = []
    for count, raster in enumerate(rasters, start=1):
        print(f'{count}/{len(rasters)} {raster}')
        records.append(get_raster_metadata(raster))

    records.sort(key=lambda x: x['Raster'])

    with open(csv_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('tifs_dir')
    args = parser.parse_args()

    # sort in reverse because we want to generate csv for winter_vv_COH06 first
    tifs_files = sorted(glob.glob(f'{args.tifs_dir}/*.txt'), reverse=True)
    assert len(tifs_files) == 8

    os.mkdir('csvs')

    for tifs_file in tifs_files:
        with open(tifs_file) as f:
            keys = f.read().strip('\n').split('\n')

        rasters = [f'/vsis3/sentinel-1-global-coherence-earthbigdata/{key}' for key in keys]

        csv_path = f'csvs/{tifs_file.removesuffix(".txt") + ".csv"}'

        make_csv(csv_path, rasters)


if __name__ == '__main__':
    main()
