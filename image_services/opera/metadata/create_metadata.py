import argparse
import json

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape


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


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-o', '--output', help='File to save output to (optional)')
    parser.add_argument(
        '-t',
        '--template',
        help='Metadata template to fill',
        default='rtc_metadata.txt.j2',
    )
    parser.add_argument('config_file', help='Configuration file from which resources are imported')
    args = parser.parse_args()

    polarization = json.load(open(args.config_file))['s3_suffix'][1:3]

    if polarization[0] != polarization[1]:
        polarization_description = (
            f'Values for the {polarization} (cross-polarized) polarization are generally '
            f'driven by volume scattering, with more complex volume scatterers (such as dense '
            f'vegetation) returning higher backscatter values. Surface water generally '
            f'appears very dark, as it is predominantly a surface scatterer; most returns '
            f'remain in the primary polarization. '
        )
    elif polarization[0] == 'V':
        polarization_description = (
            f'Values for the {polarization} polarization are commonly driven by surface '
            f'roughness and/or soil moisture, with rougher surfaces and higher soil moisture '
            f'returning higher backscatter values. Surface water appears very dark under calm '
            f'conditions, as the signal bounces off the surface away from the sensor. '
        )
    elif polarization[0] == 'H':
        polarization_description = (
            f'Values for the {polarization} polarization are a predominance of double-bounce '
            f'scattering, with signal bouncing off the ground and then off of surficial '
            f'objects (e.g., stemmy vegetation, manmade structures) and back towards the '
            f'sensor. Surface water appears very dark under calm conditions, as the signal '
            f'bounces off the surface away from the sensor. '
        )
    else:
        polarization_description = ''
    fields = {
        'polarization': polarization,
        'polarization_description': polarization_description,
    }

    output_text = render_template(args.template, fields)
    if args.output:
        output_file = args.output
    else:
        output_file = f'metadata/metadata_text/OPERA_RTC_{polarization}_metadata.txt'

    with open(output_file, 'w') as f:
        f.write(output_text)


if __name__ == '__main__':
    main()
