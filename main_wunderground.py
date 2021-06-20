import scraper_wunderground
import boto3
import yaml
import time

CONFIG_PATH = "/home/lfhohmann/gcp-weather-and-forecast-scraper/config.yaml"
DB_TABLE = "wunderground_pws"


def load_config(filepath):
    # Loads YAML config file
    with open(filepath, "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def dynamoDB_put(data):
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

    if "radiation" in data:
        data["radiation"] = round(data["radiation"] * 10)

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(DB_TABLE)

    return table.put_item(Item=data)


if __name__ == "__main__":
    config = load_config(CONFIG_PATH)

    # Iterate over the list of stations present in the config.yaml file
    for station in config["wunderground_stations"]:
        data = scraper_wunderground.get_data(station, config["units"])

        if data:
            # Only write to Database if returned data isn't empty
            data["station_id"] = station["id"]
            data["timestamp"] = time.time_ns()

            dynamoDB_put(data)

            print(f"{time.time_ns()} - {station['id']} - Data retrieved and put in DB")

        else:
            print(f"{time.time_ns()} - {station['id']} - Unable to retrieve data")
