import argparse
import json

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

SEASONS = {
    "JJA": {
        "Season": "summer",
        "SeasonAbbrev": "Jun/Jul/Aug",
        "SeasonFull": "June/July/August",
    },
    "SON": {
        "Season": "fall",
        "SeasonAbbrev": "Sep/Oct/Nov",
        "SeasonFull": "September/October/November",
    },
    "DJF": {
        "Season": "winter",
        "SeasonAbbrev": "Dec/Jan/Feb",
        "SeasonFull": "December/January/February",
    },
    "MAM": {
        "Season": "spring",
        "SeasonAbbrev": "Mar/Apr/May",
        "SeasonFull": "March/April/May",
    },
}


def get_environment() -> Environment:
    env = Environment(
        loader=PackageLoader("templates", ""),
        autoescape=select_autoescape(["html.j2", "xml.j2"]),
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
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("-o", "--output", help="File to save output to (optional)")
    parser.add_argument(
        "-t", "--template", help="Metadata template to fill", default="coherence.txt.j2"
    )
    parser.add_argument(
        "config_file", help="Configuration file from which resources are imported"
    )
    args = parser.parse_args()

    dataset_name = json.load(open(args.config_file))["dataset_name"]
    data_type, polarization, season = dataset_name.split("_")

    fields = {
        "data_type": data_type,
        "interval": int(data_type[-2:]),
        "polarization": polarization,
        "months_abbreviated": SEASONS[season]["SeasonAbbrev"],
        "season": SEASONS[season]["Season"],
        "months_full": SEASONS[season]["SeasonFull"],
    }

    output_text = render_template(args.template, fields)
    if args.output:
        output_file = args.output
    else:
        output_file = f"service_metadata/{dataset_name}_metadata.txt"

    with open(output_file, "w") as f:
        f.write(output_text)


if __name__ == "__main__":
    main()
