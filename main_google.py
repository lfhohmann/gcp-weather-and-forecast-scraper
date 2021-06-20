#!/usr/bin/env python3
import scraper_google
import boto3
import yaml
import time

CONFIG_PATH = "/home/lfhohmann/gcp-weather-and-forecast-scraper/config.yaml"
DB_TABLE = "google_forecast"


def load_config(filepath):
    # Loads YAML config file
    with open(filepath, "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def dynamoDB_put(data):

    # Convert values to ints, because DynamoDB does not support floats
    if "temp" in data:
        data["temp"] = round(data["temp"] * 10)

    if "humidity" in data:
        data["humidity"] = round(data["humidity"] * 10)

    if "wind" in data:
        data["wind"] = round(data["wind"] * 10)

    if "precip" in data:
        data["precip"] = round(data["precip"] * 10)

    for idx, _ in enumerate(data["next_days"]):
        data["next_days"][idx]["min_temp"] = round(
            data["next_days"][idx]["min_temp"] * 10
        )
        data["next_days"][idx]["max_temp"] = round(
            data["next_days"][idx]["max_temp"] * 10
        )

    for idx, _ in enumerate(data["curves"]["precip"]):
        data["curves"]["precip"][idx][0] = round(data["curves"]["precip"][idx][0] * 10)

    for idx, _ in enumerate(data["curves"]["wind"]):
        data["curves"]["wind"][idx][0] = round(data["curves"]["wind"][idx][0] * 10)

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(DB_TABLE)

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
