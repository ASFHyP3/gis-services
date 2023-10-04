import calendar
import datetime
import json

from arcgis import GIS


def datetime_to_esri(date_time):
    return calendar.timegm(date_time.timetuple()) * 1000


webmap_id = 'bcd14ca972cf455eae744661744927df'

gis = GIS('home')
item = gis.content.get(webmap_id)

data = item.get_data()
slider_length = datetime.timedelta(weeks=51)
window_length = datetime.timedelta(weeks=3)
buffer_length = datetime.timedelta(days=1)
latest_time = data['widgets']['timeSlider']['properties']['endTime']
end_time = datetime.date.fromtimestamp(latest_time/1000) + buffer_length
time_stop_interval = {'interval': 1, 'units': 'esriTimeUnitsDays'}
data['widgets']['timeSlider']['properties']['timeStopInterval'] = time_stop_interval

data['widgets']['timeSlider']['properties']['startTime'] = datetime_to_esri(end_time - slider_length)
data['widgets']['timeSlider']['properties']['currentTimeExtent'] = [datetime_to_esri(end_time - window_length),
                                                                    datetime_to_esri(end_time)]

item.update(data=json.dumps(data))
