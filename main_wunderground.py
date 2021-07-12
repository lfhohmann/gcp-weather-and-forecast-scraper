#!/usr/bin/env python3
from datetime import datetime as dt
from helpers import load_config
import scraper_wunderground
from const import *
import boto3
import time


def dynamoDB_put(table, data):
    # Convert values to ints, because DynamoDB does not support floats
    if "temp" in data:
        data["temp"] = round(data["temp"] * 10)

    if "temp_feel" in data:
        data["temp_feel"] = round(data["temp_feel"] * 10)

    if "dew_point" in data:
        data["dew_point"] = round(data["dew_point"] * 10)

    if "humidity" in data:
        data["humidity"] = round(data["humidity"])

    if "wind_speed" in data:
        data["wind_speed"] = round(data["wind_speed"] * 10)

    if "wind_gust" in data:
        data["wind_gust"] = round(data["wind_gust"] * 10)

    if "wind_bearing" in data:
        data["wind_bearing"] = round(data["wind_bearing"])

    if "pressure" in data:
        data["pressure"] = round(data["pressure"] * 100)

    if "precip_rate" in data:
        data["precip_rate"] = round(data["precip_rate"] * 100)

    if "precip_total" in data:
        data["precip_total"] = round(data["precip_total"] * 100)

    if "uv_index" in data:
        data["uv_index"] = round(data["uv_index"])

    if "radiation" in data:
        data["radiation"] = round(data["radiation"] * 10)

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table)

    return table.put_item(Item=data)


if __name__ == "__main__":
    config = load_config(CONFIG_PATH)

    print(f"{dt.now().strftime(r'%Y/%m/%d %H:%M:%S')} - SCRAPE STARTED")

    # Iterate over the list of stations present in the config.yaml file
    for station in config["wunderground_stations"]:
        data = scraper_wunderground.get_data(station, config["units"])

        if data:
            # Only write to Database if returned data isn't empty
            data["station_id"] = station["id"]
            data["timestamp"] = time.time_ns()

            response = dynamoDB_put(WUNDERGROUND_DB_TABLE, data)

            print(
                f"{dt.now().strftime(r'%Y/%m/%d %H:%M:%S')} - {station['id']} - Data retrieved and put in DB: Response code - {response['ResponseMetadata']['HTTPStatusCode']}"
            )

            if station["put_in_short_db"]:
                print(station["id"])

        else:
            print(
                f"{dt.now().strftime(r'%Y/%m/%d %H:%M:%S')} - {station['id']} - Unable to retrieve data"
            )
