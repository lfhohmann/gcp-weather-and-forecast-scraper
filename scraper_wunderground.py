#!/usr/bin/env python3

from bs4 import BeautifulSoup as bs
import requests
import boto3
import time
import yaml

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
LANGUAGE = "en-US,en;q=0.5"
URL = "https://www.wunderground.com/dashboard/pws/"

CONFIG_PATH = "/home/lfhohmann/gcp-weather-and-forecast-scraper/config.yaml"
DB_TABLE = "wunderground_pws"


def _convert_inches_to_hpa(inches):
    # Converts Inches of Mercury to Hectopascal
    return round(inches * 33.86, 2)


def _convert_inches_to_mm(inches):
    # Converts Inches of Mercury to Milimeters of Mercury
    return round(inches * 25.4, 2)


def _convert_mph_to_kph(mph):
    # Converts Miles per Hour to Kilometers per Hour
    return round(mph * 1.6, 1)


def _convert_f_to_c(f):
    # Converts Farenheit to Celsius
    return round((f - 32) * (5 / 9), 1)


def load_config(filepath):
    # Loads YAML config file
    with open(filepath, "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def get_wunderground_data(
    station,
    output_units={"temp": "c", "pressure": "hpa", "speed": "kph", "precip": "mm"},
):
    """Function to scrape data from Wunderground Personal Weather Station web page
        without API key.

    ### Args:
        station (dict): A dictionary containing the "station_id" and a list of the desired values to be
                        extracted under the "parameters" key.
        output_units (dict, optional): A dictionary with the desired output units. "temp" can be either "c", for
                                       Celsius, or "f", for Farenheit. "pressure" can be "hpa",for HectoPascal, "mm",
                                       for Milimeters of Mercury or "inches", for Inches of Mercury. "speed" refers to
                                       "wind_speed" and "wind_gust"units, can be either "kph", for Kilometers per
                                       Hour, or "mph", for Miles per Hour. And "precip" refers to "precip_rate" and
                                       "precip_total" units, can be either "mm", for Milimeters, or "inches" for
                                       Inches.

                                       Defaults to {"temp": "c", "pressure": "hpa", "speed": "kph", "precip": "mm"}.

    ### Returns:
        dict: A dictionary is returned with all requested parameters from the chosen Wunderground PWS.
    """
    try:
        # Read data from URL
        session = requests.Session()
        session.headers["User-Agent"] = USER_AGENT
        session.headers["Accept-Language"] = LANGUAGE
        session.headers["Content-Language"] = LANGUAGE
        html = session.get(f"{URL}{station['id']}")
        soup = bs(html.text, "html.parser")

        # Store data in dictionary
        data = {}

        if (
            soup.findAll("span", attrs={"_ngcontent-app-root-c173": ""})[21].text
            == "Online"
        ):
            # Only extract data if station is online

            # Last updated value
            data["last_updated"] = soup.findAll(
                "span", attrs={"class": "ng-star-inserted"}
            )[0].text

            strings = data["last_updated"].split()
            if (strings[0] == "(updated") and (strings[3] == "ago)"):
                value = int(strings[1])

                if (value >= 0) and (value <= 60):
                    if strings[2][0:6] == "second":
                        data["last_updated"] = value

                    elif strings[2][0:6] == "minute":
                        data["last_updated"] = value * 60

                    elif strings[2][0:4] == "hour":
                        if (value >= 0) and (value <= 24):
                            data["last_updated"] = value * 3600

                        else:
                            return None

                    else:
                        return None

                else:
                    return None

            # for idx, entry in enumerate(soup.findAll("span", attrs={"class": "wu-value"})):
            #     print(f"{idx}\t{entry}")

            # Get Temperature
            if "temp" in station["parameters"]:
                data["temp"] = soup.findAll("span", attrs={"class": "wu-value"})
                data["temp"] = round(
                    float(data["temp"][station["parameters"]["temp"]].text), 1
                )

                if output_units["temp"] == "c":
                    data["temp"] = _convert_f_to_c(data["temp"])

            # Get Dew Point
            if "dew_point" in station["parameters"]:
                data["dew_point"] = soup.findAll("span", attrs={"class": "wu-value"})
                data["dew_point"] = _convert_f_to_c(
                    float(data["dew_point"][station["parameters"]["dew_point"]].text)
                )

            # Get Humidity
            if "humidity" in station["parameters"]:
                data["humidity"] = soup.findAll("span", attrs={"class": "wu-value"})
                data["humidity"] = round(
                    float(data["humidity"][station["parameters"]["humidity"]].text)
                )

            # Get Pressure
            if "pressure" in station["parameters"]:
                data["pressure"] = soup.findAll("span", attrs={"class": "wu-value"})
                data["pressure"] = round(
                    float(data["pressure"][station["parameters"]["pressure"]].text), 2
                )

                if output_units["pressure"] == "hpa":
                    data["pressure"] = _convert_inches_to_hpa(data["pressure"])

            # Get Wind Speed
            if "wind_speed" in station["parameters"]:
                data["wind_speed"] = soup.findAll("span", attrs={"class": "wu-value"})
                data["wind_speed"] = round(
                    float(data["wind_speed"][station["parameters"]["wind_speed"]].text),
                    1,
                )

                if output_units["speed"] == "kph":
                    data["wind_speed"] = _convert_mph_to_kph(data["wind_speed"])

            # Get Wind Gust
            if "wind_gust" in station["parameters"]:
                data["wind_gust"] = soup.findAll("span", attrs={"class": "wu-value"})
                data["wind_gust"] = round(
                    float(data["wind_gust"][station["parameters"]["wind_gust"]].text), 1
                )

                if output_units["speed"] == "kph":
                    data["wind_gust"] = _convert_mph_to_kph(data["wind_gust"])

            # Get Wind Bearing
            if "wind_bearing" in station["parameters"]:
                data["wind_bearing"] = soup.find(
                    "div", attrs={"class": "arrow-wrapper"}
                )

                string_full = ((data["wind_bearing"]["style"]).split())[1]
                string_start = string_full[0:7]
                string_end = string_full[-5:-1]

                if (string_start == "rotate(") and (string_end == "deg)"):
                    data["wind_bearing"] = int(string_full[7:-5]) - 180
                else:
                    data["wind_bearing"] = None

            # Get Precipitation Rate
            if "precip_rate" in station["parameters"]:
                data["precip_rate"] = soup.findAll("span", attrs={"class": "wu-value"})
                data["precip_rate"] = round(
                    float(
                        data["precip_rate"][station["parameters"]["precip_rate"]].text
                    ),
                    2,
                )

                if output_units["precip"] == "mm":
                    data["precip_rate"] = _convert_inches_to_mm(data["precip_rate"])

            # Get Precipitation Total
            if "precip_total" in station["parameters"]:
                data["precip_total"] = soup.findAll("span", attrs={"class": "wu-value"})
                data["precip_total"] = round(
                    float(
                        data["precip_total"][station["parameters"]["precip_total"]].text
                    ),
                    2,
                )

                if output_units["precip"] == "mm":
                    data["precip_total"] = _convert_inches_to_mm(data["precip_total"])

            # Get UV Index
            if "uv_index" in station["parameters"]:
                data["uv_index"] = soup.findAll("span", attrs={"class": "wu-value"})
                data["uv_index"] = round(
                    float(data["uv_index"][station["parameters"]["uv_index"]].text)
                )

            # Get Solar Radiation
            if "radiation" in station["parameters"]:
                data["radiation"] = soup.findAll(
                    "div", attrs={"class": "weather__text"}
                )
                strings = data["radiation"][-1].text.split()

                if strings[1][-8:-3] == "watts":
                    data["radiation"] = round(float(strings[0]), 1)
                else:
                    data["radiation"] = None

        return data

    except:
        return {}


def dynamoDB_put(data):

    # Convert values to ints, because DynamoDB does not support floats
    if "temp" in data:
        data["temp"] = round(data["temp"] * 10)

    if "dew_point" in data:
        data["dew_point"] = round(data["dew_point"] * 10)

    if "wind_speed" in data:
        data["wind_speed"] = round(data["wind_speed"] * 10)

    if "wind_gust" in data:
        data["wind_gust"] = round(data["wind_gust"] * 10)

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


def main():
    config = load_config(CONFIG_PATH)

    for station in config["wunderground_stations"]:
        data = get_wunderground_data(station)

        if data:
            # Only write to Database if returned data isn't empty
            data["station_id"] = station["id"]
            data["timestamp"] = time.time_ns()

            dynamoDB_put(data)

            print(f"{time.time_ns()} - {station['id']} - Data retrieved and put in DB")

        else:
            print(f"{time.time_ns()} - {station['id']} - Unable to retrieve data")


if __name__ == "__main__":
    main()
    # schedule.every().minute.do(main)
    #
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
