import datetime
import calendar

from arcgis import GIS
import json

webmap_id = '0b0336feb86e47b1a2b6ddf40b0d5bf3'
gis = GIS('home')
item = gis.content.get(webmap_id)

data = item.get_data()

delta_t = datetime.timedelta(weeks=3)
end_time = datetime.date.fromtimestamp(data['widgets']['timeSlider']['properties']['endTime']/1000)
data['widgets']['timeSlider']['properties']['startTime'] = calendar.timegm((end_time - delta_t).timetuple()) * 1000

item.update(data=json.dumps(data))
