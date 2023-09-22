import os
from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

SEASONS = {
    'JJA': {
        'Season': 'summer',
        'SeasonFull': 'June/July/August',
        'start_date': '2020-06-01',
        'end_date': '2020-08-31',
        'date_range': 'Jun 2020 to Aug 2020'
    },
    'SON': {
        'Season': 'fall',
        'SeasonFull': 'September/October/November',
        'start_date': '2020-09-01',
        'end_date': '2020-11-30',
        'date_range': 'Sep 2020 to Nov 2020'
    },
    'DJF': {
        'Season': 'winter',
        'SeasonFull': 'December/January/February',
        'start_date': '2019-12-01',
        'end_date': '2020-02-29',
        'date_range': 'Dec 2019 to Feb 2020'
    },
    'MAM': {
        'Season': 'spring',
        'SeasonFull': 'March/April/May',
        'start_date': '2020-03-01',
        'end_date': '2020-05-31',
        'date_range': 'Mar 2020 to May 2020'
    }
}


def get_environment() -> Environment:
    env = Environment(
        loader=PackageLoader('templates', ''),
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


working_dir = r'egis_metadata/'
intervals = [6, 12]
polarizations = ['VV', 'HH']

for interval in intervals:
    interval_str = str(interval).zfill(2)
    for polarization in polarizations:
        for season in SEASONS:
            metadata_dir = f'{working_dir}/GSSICB_COH{interval_str}_{polarization}_{season}'
            os.mkdir(metadata_dir)
            fields = {'season_code': season,
                      'interval_int': interval,
                      'interval_str': interval_str,
                      'polarization': polarization,
                      'season': SEASONS[season]['Season'],
                      'start_date': SEASONS[season]['start_date'],
                      'end_date': SEASONS[season]['end_date'],
                      'date_range': SEASONS[season]['date_range'],
                      'months': SEASONS[season]['SeasonFull']
                      }

            output_text = render_template('egis_template.yaml.j2', fields)
            with open(f'{metadata_dir}/METADATA.yml', 'w') as f:
                f.write(output_text)
