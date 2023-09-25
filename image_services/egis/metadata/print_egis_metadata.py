import json
import os
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

SEASONS = {
    'JJA': {
        'Season': 'summer',
        'SeasonFull': 'June/July/August',
        'SeasonShort': 'Jun/Jul/Aug',
        'start_date': '2020-06-01',
        'end_date': '2020-08-31',
        'date_range': 'Jun 2020 to Aug 2020'
    },
    'SON': {
        'Season': 'fall',
        'SeasonFull': 'September/October/November',
        'SeasonShort': 'Sep/Oct/Nov',
        'start_date': '2020-09-01',
        'end_date': '2020-11-30',
        'date_range': 'Sep 2020 to Nov 2020'
    },
    'DJF': {
        'Season': 'winter',
        'SeasonFull': 'December/January/February',
        'SeasonShort': 'Dec/Jan/Feb',
        'start_date': '2019-12-01',
        'end_date': '2020-02-29',
        'date_range': 'Dec 2019 to Feb 2020'
    },
    'MAM': {
        'Season': 'spring',
        'SeasonFull': 'March/April/May',
        'SeasonShort': 'Mar/Apr/May',
        'start_date': '2020-03-01',
        'end_date': '2020-05-31',
        'date_range': 'Mar 2020 to May 2020'
    }
}


def organize_directories(base_directory, new_directory):
    if not Path(base_directory).exists():
        os.mkdir(base_directory)
    dir_path = Path(base_directory) / Path(new_directory)
    if not dir_path.exists():
        os.mkdir(dir_path)
    return dir_path


def get_environment() -> Environment:
    env = Environment(
        loader=PackageLoader('templates', 'egis_templates'),
        autoescape=select_autoescape(['html.j2', 'xml.j2']),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    return env


def render_template(template: str, payload: dict) -> str:
    env = get_environment()
    template = env.get_template(template)
    rendered = template.render(payload)
    return rendered


def create_metadata(interval, polarization, season, egis_base_directory, username: str = os.getlogin(),
                    data_type_code: str = 'COH'):
    data_type = data_type_code + str(interval).zfill(2)
    fields = {'season_code': season,
              'interval': interval,
              'polarization': polarization,
              'data_type': data_type,
              'season': SEASONS[season]['Season'],
              'start_date': SEASONS[season]['start_date'],
              'end_date': SEASONS[season]['end_date'],
              'date_range': SEASONS[season]['date_range'],
              'months_full': SEASONS[season]['SeasonFull'],
              'months_abbreviated': SEASONS[season]['SeasonShort'],
              'months_abbreviated_underscore': SEASONS[season]['SeasonShort'].replace('/', '_'),
              'username': username,
              'today': datetime.now().strftime('%d %B %Y'),
              }

    metadata_dir_path = organize_directories(egis_base_directory, f'GSSICB_{data_type}_{polarization}_{season}')

    parameter_text = render_template('PARAMETERS.json.j2', fields)
    with open(f'{metadata_dir_path}/PARAMETERS.json', 'w') as f:
        f.write(parameter_text)

    with open(f'{metadata_dir_path}/PARAMETERS.json') as f:
        parameters = json.load(f)
        fields['parameters'] = parameters

    metadata_text = render_template('METADATA.yaml.j2', fields)
    with open(f'{metadata_dir_path}/METADATA.yaml', 'w') as f:
        f.write(metadata_text)

    prdready_text = render_template('PRD-READY.md.j2', fields)
    with open(f'{metadata_dir_path}/PRD-READY.md', 'w') as f:
        f.write(prdready_text)


working_dir = r'/Users/jrsmale/GitHub/egis-service-manager/services/images/ASF/GSSICB_COH_'
intervals = [6, 12]
polarizations = ['VV','HH']

for interval in intervals:
    interval_str = str(interval).zfill(2)
    for polarization in polarizations:
        for season in SEASONS:
            create_metadata(interval, polarization, season, egis_base_directory=working_dir, username='Jacquelyn Smale')
