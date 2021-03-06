#!/usr/bin/env python3
from bs4 import BeautifulSoup as bs
from helpers import load_config
from pprint import pprint
from const import *
import converters
import requests
import re


REGEX_MAPPING = {
    "online": r"Online\(updated",
    "last_updated": r"Online\(updated\s(\d+)\s(\w+)\sago\)",
    "temp": r"Current\sConditions\s([\d\.]+)",
    "temp_feel": r"Feels\sLike\s([\d\.]+)",
    "dew_point": r"DEWPOINT([\d\.]+)",
    "humidity": r"HUMIDITY([\d\.]+)",
    "pressure": r"PRESSURE([\d\.]+)",
    "wind_speed": r"WIND\s&\sGUST\s([\d\.]+)\s.\s.\s[\d\.]+",
    "wind_gust": r"WIND\s&\sGUST\s[\d\.]+\s.\s.\s([\d\.]+)",
    "wind_direction": r"(\w+)\sWIND\s&\sGUST",
    "wind_bearing": r"rotate\(([\d]+)deg\)",
    "precip_rate": r"PRECIP\sRATE([\d\.]+)",
    "precip_total": r"PRECIP\sACCUM([\d\.]+)",
    "uv_index": r"UV([\d\.]+)",
    "radiation": r"radiationCURRENT([\d\.]+) watts",
}


def get_data(
    station,
    output_units={"temp": "c", "pressure": "hpa", "speed": "kmph", "precip": "mm"},
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
        session.headers["User-Agent"] = WUNDERGROUND_HEADER["User-Agent"]
        session.headers["Accept-Language"] = WUNDERGROUND_HEADER["Language"]
        session.headers["Content-Language"] = WUNDERGROUND_HEADER["Language"]
        html = session.get(f"{WUNDERGROUND_URL}{station['id']}")
        soup = bs(html.text, "html.parser")

        # Pull data from page
        raw_data_list = soup.findAll("div")
        raw_data_str = ""

        # Make one long string to search with regex
        for entry in raw_data_list:
            raw_data_str += entry.text

        data = {}

        # Check if station is online
        if re.findall(REGEX_MAPPING["online"], raw_data_str):

            # Get Last Updated value
            data["last_updated"] = re.findall(
                REGEX_MAPPING["last_updated"], raw_data_str
            )[0]

            if data["last_updated"]:
                time = int(data["last_updated"][0])

                if 0 <= time <= 60:
                    if "second" in data["last_updated"][1]:
                        data["last_updated"] = time

                    elif "minute" in data["last_updated"][1]:
                        data["last_updated"] = time * 60

                    elif "hour" in data["last_updated"][1]:
                        if 0 <= time <= 24:
                            data["last_updated"] = time * 3600

                        else:
                            return {}

                    else:
                        return {}

                else:
                    return {}

            # Iterate over station's parameters and extract each one with regex
            for parameter in station["parameters"]:
                if parameter != "wind_bearing" and parameter != "radiation":
                    data[parameter] = re.findall(
                        REGEX_MAPPING[parameter], raw_data_str
                    )[0]

                    try:
                        data[parameter] = float(data[parameter])
                    except:
                        pass

                # Wind Bearing is a special case and must be extracted with different rules
                elif parameter == "wind_bearing":
                    data[parameter] = soup.find("div", attrs={"class": "arrow-wrapper"})
                    data[parameter] = ((data[parameter]["style"]).split())[1]
                    data[parameter] = re.findall(
                        REGEX_MAPPING[parameter], data[parameter]
                    )

                    if data[parameter]:
                        data[parameter] = float(data[parameter][0]) - 180

                # Solar Radiation is a special case and must be extracted with different rules
                elif parameter == "radiation":
                    data[parameter] = re.findall(REGEX_MAPPING[parameter], raw_data_str)

                    if data[parameter][0]:
                        data[parameter] = float(data[parameter][0])

            # Convert units if necessary
            if output_units["temp"] == "c":
                if "temp" in data:
                    data["temp"] = converters.f_to_c(data["temp"])
                if "temp_feel" in data:
                    data["temp_feel"] = converters.f_to_c(data["temp_feel"])
                if "dew_point" in data:
                    data["dew_point"] = converters.f_to_c(data["dew_point"])

            if output_units["pressure"] == "hpa":
                if "pressure" in data:
                    data["pressure"] = converters.inches_to_hpa(data["pressure"])
            elif output_units["pressure"] == "mm":
                if "pressure" in data:
                    data["pressure"] = converters.inches_to_mm(data["pressure"])

            if output_units["speed"] == "kmph":
                if "wind_speed" in data:
                    data["wind_speed"] = converters.mph_to_kmph(data["wind_speed"])
                if "wind_gust" in data:
                    data["wind_gust"] = converters.mph_to_kmph(data["wind_gust"])
            if output_units["speed"] == "mps":
                if "wind_speed" in data:
                    data["wind_speed"] = converters.mph_to_mps(data["wind_speed"])
                if "wind_gust" in data:
                    data["wind_gust"] = converters.mph_to_mps(data["wind_gust"])

            if output_units["precip"] == "mm":
                if "precip_rate" in data:
                    data["precip_rate"] = converters.inches_to_mm(data["precip_rate"])
                if "precip_total" in data:
                    data["precip_total"] = converters.inches_to_mm(data["precip_total"])

        return data

    except:
        return {}


if __name__ == "__main__":
    """For testing purposes"""

    config = load_config(CONFIG_PATH)

    # Iterate over the list of stations present in the config.yaml file
    for station in config["wunderground_stations"]:
        data = get_data(station, config["units"])

        if data:
            print(station["id"])
            pprint(data)

        else:
            print(f"{station['id']} - Unable to retrieve data")
