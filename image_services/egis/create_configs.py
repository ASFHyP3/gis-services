import json

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape


SEASONS = {
    'JJA': {
        'Season': 'summer',
        'SeasonAbbrev': 'Jun/Jul/Aug',
        'SeasonFull': 'June/July/August',
    },
    'SON': {
        'Season': 'fall',
        'SeasonAbbrev': 'Sep/Oct/Nov',
        'SeasonFull': 'September/October/November',
    },
    'DJF': {
        'Season': 'winter',
        'SeasonAbbrev': 'Dec/Jan/Feb',
        'SeasonFull': 'December/January/February',
    },
    'MAM': {
        'Season': 'spring',
        'SeasonAbbrev': 'Mar/Apr/May',
        'SeasonFull': 'March/April/May',
    },
}


def make_configuration(data_type, polarization, season):
    config = {
        'project_name': 'GSSICB',
        's3_prefix': 'tiles/',
        's3_suffix': f"_{SEASONS[season]['Season']}_{polarization.lower()}_{data_type}.tif",
        'dataset_name': f'{data_type}_{polarization.upper()}_{season}',
        'raster_function_templates': ['ScaledCoherence.rft.xml', 'UnscaledCoherence.rft.xml'],
        'default_raster_function_template': 'UnscaledCoherence.rft.xml',
    }
    return config


def make_metadata_fields(data_type, polarization, season):
    metadata = {
        'data_type': data_type,
        'interval': int(data_type[-2:]),
        'polarization': polarization,
        'months_abbreviated': SEASONS[season]['SeasonAbbrev'],
        'season': SEASONS[season]['Season'],
        'months_full': SEASONS[season]['SeasonFull'],
    }
    return metadata


def get_environment() -> Environment:
    env = Environment(
        loader=PackageLoader('metadata', 'templates'),
        autoescape=select_autoescape(['html.j2', 'xml.j2']),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    return env


def render_template(template: str, payload: dict) -> str:
    env = get_environment()
    template_object = env.get_template(template)
    rendered = template_object.render(payload)
    return rendered


data_types = ['COH24']
polarizations = ['VV', 'HH']

for data_type in data_types:
    for polarization in polarizations:
        for season in SEASONS:
            service_name = f'{data_type}_{polarization.upper()}_{season}'
            config_dict = make_configuration(data_type, polarization, season)
            metadata_dict = make_metadata_fields(data_type, polarization, season)

            with open(f'config/{service_name}.json', 'w') as f:
                json.dump(config_dict, f, indent=2)

            output_metadata = render_template('coherence.txt.j2', metadata_dict)
            with open(f'metadata/service_metadata/{service_name}_metadata.txt', 'w') as f:
                f.write(output_metadata)
