import calendar
import datetime
import json

from arcgis import GIS


def datetime_to_esri(date_time):
    return calendar.timegm(date_time.timetuple()) * 1000


webmap_id = '0b0336feb86e47b1a2b6ddf40b0d5bf3'
gis = GIS('home')
item = gis.content.get(webmap_id)

data = item.get_data()

slider_length = datetime.timedelta(weeks=51)
window_length = datetime.timedelta(weeks=3)
latest_time = data['widgets']['timeSlider']['properties']['endTime']
end_time = datetime.date.fromtimestamp(latest_time/1000)


data['widgets']['timeSlider']['properties']['startTime'] = datetime_to_esri(end_time - slider_length)
data['widgets']['timeSlider']['properties']['currentTimeExtent'] = [datetime_to_esri(end_time - window_length),
                                                                    datetime_to_esri(end_time)]

item.update(data=json.dumps(data))
