CONFIG_PATH = "/home/lfhohmann/gcp-weather-and-forecast-scraper/config.yaml"

GOOGLE_DB_TABLE = "google_forecast"
GOOGLE_URL = "https://www.google.com/search?hl=en&lr=lang_en&ie=UTF-8&q=weather"
GOOGLE_HEADER = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Language": "en-US,en;q=0.5",
}

WUNDERGROUND_DB_TABLE = "wunderground_pws"
WUNDERGROUND_DB_SHORT_TABLE = "wunderground_pws_short"
WUNDERGROUND_URL = "https://www.wunderground.com/dashboard/pws/"
WUNDERGROUND_HEADER = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
    "Language": "en-US,en;q=0.5",
}
