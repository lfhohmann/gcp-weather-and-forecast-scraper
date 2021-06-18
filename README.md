# GCP Weather and Forecast Scraper

This is a scraper to run on an F1 (Free Tier) instance of Google Cloud Compute Engine for current weather data from Wunderground Personal Weather Stations and forecast weather data from Google (weather.com).

A CRON job regularly executes the scripts to scrape data from both sources (Wunderground PWSs and Google Weather) and stores them in a NoSQL database (AWS Dynamo) for later analysis.

The idea is to store data over a period of time and analyze the forecast predictions against the actual weather conditions.
