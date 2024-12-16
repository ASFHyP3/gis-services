import argparse
import csv
import json
import logging
import os

import boto3
import requests

S3_CLIENT = boto3.client("s3")
log = logging.getLogger(__name__)


def query_cmr(polarization):
    session = requests.Session()
    search_url = "https://cmr.earthdata.nasa.gov/search/granules.umm_json"

    params = {
        "short_name": "OPERA_L2_RTC-S1_V1",
        "attribute[]": f"string,POLARIZATION,{polarization}",
        "page_size": 2000,
    }
    headers = {}
    vsis3_uris = []
    while True:
        response = session.get(search_url, params=params, headers=headers)
        response.raise_for_status()
        for granule in response.json()["items"]:
            for url in granule["umm"]["RelatedUrls"]:
                if url["URL"].startswith("s3://") and url["URL"].endswith(
                    f"{polarization}.tif"
                ):
                    vsis3_uris.append(url["URL"].replace("s3://", "/vsis3/"))
                    break
        if "CMR-Search-After" not in response.headers:
            break
        headers["CMR-Search-After"] = response.headers["CMR-Search-After"]
    return vsis3_uris


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--working-directory", default=os.getcwd())
    parser.add_argument("config_file")
    args = parser.parse_args()

    with open(args.config_file) as f:
        config = json.load(f)

    polarization = config["s3_suffix"][1:3]
    url_file = os.path.join(
        args.working_directory,
        f'{config["project_name"]}_{config["dataset_name"]}_vsis3_urls.csv',
    )
    log.info(f"Querying CMR for OPERA {polarization} products")
    vsis3_urls = query_cmr(polarization)

    with open(url_file, "w", newline="") as f:
        writer = csv.writer(f)
        for url in vsis3_urls:
            writer.writerow([url])


if __name__ == "__main__":
    main()
