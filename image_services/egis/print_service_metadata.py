import argparse
import json

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

SEASONS = {
    'JJA': {
        'Season': 'Summer',
        'SeasonAbbrev': 'Jun/Jul/Aug',
        'SeasonFull': 'June/July/August',
    },
    'SON': {
        'Season': 'Fall',
        'SeasonAbbrev': 'Sep/Oct/Nov',
        'SeasonFull': 'September/October/November',
    },
    'DJF': {
        'Season': 'Winter',
        'SeasonAbbrev': 'Dec/Jan/Feb',
        'SeasonFull': 'December/January/February',
    },
    'MAM': {
        'Season': 'Spring',
        'SeasonAbbrev': 'Mar/Apr/May',
        'SeasonFull': 'March/April/May',
    }
}


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
    template = env.get_template(template)
    rendered = template.render(payload)
    return rendered


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-o', '--output', help='File to save output to (optional)')
    parser.add_argument('-t', '--template', help='Metadata template to fill', default='coherence.txt.j2')
    parser.add_argument('config_file', help='Configuration file from which resources are imported')
    args = parser.parse_args()

    interval, polarization, season = json.load(open(args.config_file))['dataset_name'].split('_')

    fields = {
        'interval': interval,
        'polarization': polarization,
        'months_abbreviated': SEASONS[season]['SeasonAbbrev'],
        'season': SEASONS[season]['Season'],
        'months_full': SEASONS[season]['SeasonFull']
    }

    output_text = render_template(args.template, fields)
    print(args.output)
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_text)
    else:
        print(output_text)


if __name__ == '__main__':
    main()
