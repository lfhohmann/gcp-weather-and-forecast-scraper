from bs4 import BeautifulSoup as bs
import requests
import re

def get_google_forecast(region, output_units={"temp": "c", "speed": "kph"}):
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
    LANGUAGE = "en-US,en;q=0.5"
    URL = "https://www.google.com/search?lr=lang_en&ie=UTF-8&q=weather"

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
    data["dayhour"] = soup.find("div", attrs={"id": "wob_dts"}).text
    data["weather_now"] = soup.find("span", attrs={"id": "wob_dc"}).text
    data["precipitation"] = soup.find("span", attrs={"id": "wob_pp"}).text
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
                "name": day_name,
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

    wind = str(soup.find("div", attrs={"id": "wob_wg", "class": "wob_noe"}))
    data["curves"]["wind"] = re.findall(
        r'"(\d+ [\w\/]+) \w+ (\w+) (\w+-*\w*),* ([0-9:]+\s*\w*)" class="wob_t" style="display:inline;text-align:right">\d+ [\w\/]+<\/span><span aria-label="\d+ [\w\/]+ \w+-*\w*,* [0-9:]+\s*\w*" class="wob_t" style="display:none;text-align:right">\d+ [\w\/]+<\/span><\/div><div style="-webkit-box-flex:1"><\/div><img alt="\d+ [\w\/]+ \w+ \w+" aria-hidden="true" src="\/\/ssl.gstatic.com\/m\/images\/weather\/\w+.\w+" style="transform-origin:\d+% \d+%;transform:rotate\(\d+\w+\)',
        wind,
    )

    return data


if __name__ == "__main__":
    print(get_google_forecast("curitiba"))

