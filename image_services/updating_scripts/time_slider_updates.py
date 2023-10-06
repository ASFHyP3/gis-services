import calendar
import datetime
import json

import boto3
from arcgis import GIS

client = boto3.client(service_name='secretsmanager', region_name='us-west-2')
response = client.get_secret_value(SecretId='tools_user_accounts')
password_dict = json.loads(response['SecretString'])


def datetime_to_esri(date_time):
    return calendar.timegm(date_time.timetuple()) * 1000


def update_time_slider(item):
    data = item.get_data()
    slider_length = datetime.timedelta(weeks=51)
    window_length = datetime.timedelta(weeks=3)
    buffer_length = datetime.timedelta(days=1)

    today_time = datetime.date.today() + buffer_length
    data['widgets']['timeSlider']['properties']['endTime'] = datetime_to_esri(today_time)

    time_stop_interval = {'interval': 1, 'units': 'esriTimeUnitsDays'}
    data['widgets']['timeSlider']['properties']['timeStopInterval'] = time_stop_interval

    data['widgets']['timeSlider']['properties']['startTime'] = datetime_to_esri(today_time - slider_length)
    data['widgets']['timeSlider']['properties']['currentTimeExtent'] = [datetime_to_esri(today_time - window_length),
                                                                        datetime_to_esri(today_time)]

    return item.update(data=json.dumps(data))


webmap_ids = ['2205f66af0324a88a8d0b8a6c8fde5bf',  # Alaska Rivers
              '80442ecd1e0246adac5f5fb7e627e3e3',  # HKH
              '3dd8d25559db4ba6aa0e1b6e8cb5d39a',  # RTC
              'faa83e4ccfe64bb8a99c13ef70b19b8f',  # SWE
              ]

gis = GIS('https://asf-daac.maps.arcgis.com',
          password_dict['asf-agol-username'],
          password_dict['asf-agol-password'])

for webmap_id in webmap_ids:
    if update_time_slider(gis.content.get(webmap_id)):
        print(f'Updated webmap with id {webmap_id}')
    else:
        print(f'Error updating {webmap_id}')
