#!/usr/bin/env python3

from bs4 import BeautifulSoup as bs
from pprint import pprint
import requests
import boto3
import time
import yaml
import re

"""
This code is heavily based on Dniamir's work
https://github.com/dniamir/GoogleWeather
"""

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
LANGUAGE = "en-US,en;q=0.5"
URL = "https://www.google.com/search?lr=lang_en&ie=UTF-8&q=weather"

DB_TABLE = "google_forecast"


def _convert_mph_to_kph(mph):
    return round(mph * 1.6, 1)


def _convert_kph_to_mph(mph):
    return round(mph / 1.6, 1)


def _convert_f_to_c(f):
    return round((f - 32) * (5 / 9), 1)


def _convert_c_to_f(c):
    return round(c * (9 / 5) + 32, 1)


def load_config(filepath):
    with open(filepath, "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def get_google_forecast(region, output_units={"temp": "c", "speed": "kph"}):
    try:
        # Read data from URL
        session = requests.Session()
        session.headers["User-Agent"] = USER_AGENT
        session.headers["Accept-Language"] = LANGUAGE
        session.headers["Content-Language"] = LANGUAGE
        html = session.get(f"{URL}+{region.replace(' ', '+')}")
        soup = bs(html.text, "html.parser")

        # Store data in dictionary
        data = {}
        data["region"] = soup.find("div", attrs={"id": "wob_loc"}).text
        data["temp"] = float(soup.find("span", attrs={"id": "wob_tm"}).text)
        data["datetime"] = soup.find("div", attrs={"id": "wob_dts"}).text
        data["weather_now"] = soup.find("span", attrs={"id": "wob_dc"}).text
        data["precip"] = float(
            soup.find("span", attrs={"id": "wob_pp"}).text.replace("%", "")
        )
        data["humidity"] = float(
            soup.find("span", attrs={"id": "wob_hm"}).text.replace("%", "")
        )
        data["wind"] = soup.find("span", attrs={"id": "wob_ws"}).text

        # Convert units
        if "km/h" in data["wind"]:
            data["wind"] = float(data["wind"].replace("km/h", ""))

            if output_units["speed"] == "mph":
                data["wind"] = _convert_kph_to_mph(data["wind"])

            if output_units["temp"] == "f":
                data["temp"] = _convert_c_to_f(data["temp"])

            input_units = "metric"
        else:
            data["wind"] = float(data["wind"].replace("mph", ""))

            if output_units["speed"] == "kph":
                data["wind"] = _convert_mph_to_kph(data["wind"])

            if output_units["temp"] == "c":
                data["temp"] = _convert_f_to_c(data["temp"])

            input_units = "imperial"

        # Store data from rest of the week
        next_days = []
        days = soup.find("div", attrs={"id": "wob_dp"})
        for day in days.findAll("div", attrs={"class": "wob_df"}):
            day_name = day.find("div").attrs["aria-label"]
            weather = day.find("img").attrs["alt"]
            temp = day.findAll("span", {"class": "wob_t"})

            if input_units == "metric":
                max_temp = float(temp[0].text)
                min_temp = float(temp[2].text)
            else:
                max_temp = float(temp[1].text)
                min_temp = float(temp[3].text)

            next_days.append(
                {
                    "day": day_name,
                    "weather": weather,
                    "max_temp": max_temp,
                    "min_temp": min_temp,
                }
            )

        data["next_days"] = next_days

        # Store hourly data from precipitation probability and wind for the rest of the week
        data["curves"] = {}

        precip = str(soup.find("div", attrs={"id": "wob_pg", "class": "wob_noe"}))
        data["curves"]["precip"] = re.findall(
            r"([0-9]+)% (\w+-*\w*),* ([0-9:]+\s*\w*)", precip
        )

        # Convert values from strings to numbers
        for idx, _ in enumerate(data["curves"]["precip"]):
            data["curves"]["precip"][idx] = list(data["curves"]["precip"][idx])
            data["curves"]["precip"][idx][0] = float(data["curves"]["precip"][idx][0])

        wind = str(soup.find("div", attrs={"id": "wob_wg", "class": "wob_noe"}))
        data["curves"]["wind"] = re.findall(
            r'"(\d+ [\w\/]+) \w+ (\w+) (\w+-*\w*),* ([0-9:]+\s*\w*)" class="wob_t" style="display:inline;text-align:right">\d+ [\w\/]+<\/span><span aria-label="\d+ [\w\/]+ \w+-*\w*,* [0-9:]+\s*\w*" class="wob_t" style="display:none;text-align:right">\d+ [\w\/]+<\/span><\/div><div style="-webkit-box-flex:1"><\/div><img alt="\d+ [\w\/]+ \w+ \w+" aria-hidden="true" src="\/\/ssl.gstatic.com\/m\/images\/weather\/\w+.\w+" style="transform-origin:\d+% \d+%;transform:rotate\(\d+\w+\)',
            wind,
        )

        # Convert wind speed units if necessary
        for idx, _ in enumerate(data["curves"]["wind"]):
            data["curves"]["wind"][idx] = list(data["curves"]["wind"][idx])

            if "km/h" in data["curves"]["wind"][idx][0]:
                data["curves"]["wind"][idx][0] = float(
                    data["curves"]["wind"][idx][0].replace(" km/h", "")
                )

                if output_units["speed"] == "mph":
                    data["curves"]["wind"][idx][0] = _convert_kph_to_mph(
                        data["curves"]["wind"][idx][0]
                    )

            else:
                data["curves"]["wind"][idx][0] = float(
                    data["curves"]["wind"][idx][0].replace(" mph", "")
                )

                if output_units["speed"] == "kph":
                    data["curves"]["wind"][idx][0] = _convert_mph_to_kph(
                        data["curves"]["wind"][idx][0]
                    )

        return data

    except:
        return {}


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
    config = load_config("config.yaml")

    data = get_google_forecast(config["google_forecast"]["region"])

    dynamoDB_put(data)
    # pprint(data)
