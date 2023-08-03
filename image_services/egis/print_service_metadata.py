import argparse
import csv
import os
from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape


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
    fields = {
            'interval': '06',
            'polarization': 'VV',
            'months_abbreviated': 'Dec/Jan/Feb',
            'season': 'Winter',
            'months_full': 'December/January/February'
             }

    output_text = render_template('coherence.txt.j2', fields)
    print(output_text)


if __name__ == '__main__':
    main()
