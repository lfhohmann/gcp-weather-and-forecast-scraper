#!/usr/bin/env python3
from pprint import pprint
import scraper_google
from const import *
import boto3
import yaml
import time


def load_config(filepath):
    # Loads YAML config file
    with open(filepath, "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def dynamoDB_put(data):
    # Convert values to ints, because DynamoDB does not support floats
    if "temp" in data["weather_now"]:
        data["weather_now"]["temp"] = round(data["weather_now"]["temp"] * 10)

    if "humidity" in data["weather_now"]:
        data["weather_now"]["humidity"] = round(data["weather_now"]["humidity"] * 10)

    if "wind_speed" in data["weather_now"]:
        data["weather_now"]["wind_speed"] = round(
            data["weather_now"]["wind_speed"] * 10
        )

    if "precip_prob" in data["weather_now"]:
        data["weather_now"]["precip_prob"] = round(
            data["weather_now"]["precip_prob"] * 10
        )

    for idx, _ in enumerate(data["next_days"]):
        data["next_days"][idx]["min_temp"] = round(
            data["next_days"][idx]["min_temp"] * 10
        )
        data["next_days"][idx]["max_temp"] = round(
            data["next_days"][idx]["max_temp"] * 10
        )

    for idx, _ in enumerate(data["wind"]):
        data["wind"][idx][0] = round(data["wind"][idx][0] * 10)

    for idx, _ in enumerate(data["hourly_forecast"]):
        data["hourly_forecast"][idx]["humidity"] = round(
            data["hourly_forecast"][idx]["humidity"] * 10
        )

        data["hourly_forecast"][idx]["precip_prob"] = round(
            data["hourly_forecast"][idx]["precip_prob"] * 10
        )

        data["hourly_forecast"][idx]["temp"] = round(
            data["hourly_forecast"][idx]["temp"] * 10
        )

        data["hourly_forecast"][idx]["wind_speed"] = round(
            data["hourly_forecast"][idx]["wind_speed"] * 10
        )

    # pprint(data)

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(GOOGLE_DB_TABLE)

    return table.put_item(Item=data)


if __name__ == "__main__":
    config = load_config(CONFIG_PATH)

    data = scraper_google.get_data(config["google_forecast"]["region"])

    if data:
        # Only write to Database if returned data isn't empty
        data["timestamp"] = time.time_ns()
        dynamoDB_put(data)

        print(f"{time.time_ns()} - Data retrieved and put in DB")

    else:
        print(f"{time.time_ns()} - Unable to retrieve data")
