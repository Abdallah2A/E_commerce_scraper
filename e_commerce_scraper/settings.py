# Scrapy settings for e_commerce_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import json
from datetime import datetime

BOT_NAME = "e_commerce_scraper"

SPIDER_MODULES = ["e_commerce_scraper.spiders"]
NEWSPIDER_MODULE = "e_commerce_scraper.spiders"

# Load API key from config.json
with open(r'e_commerce_scraper\config.json', 'r') as config_file:
    config = json.load(config_file)

SCRAPE_OPS_API_KEY = config['SCRAPE_OPS_API_KEY']
SCRAPE_OPS_FAKE_BROWSER_HEADER_ENDPOINT = 'https://headers.scrapeops.io/v1/browser-headers'
SCRAPE_OPS_FAKE_BROWSER_HEADER_ENABLED = True
SCRAPE_OPS_NUM_RESULTS = 50

# Robot.txt rules
ROBOTSTXT_OBEY = True

# Downloader Middleware
DOWNLOADER_MIDDLEWARES = {
    "e_commerce_scraper.middlewares.ScrapeOpsFakeBrowserHeaderAgentMiddleware": 400,
}

# Item Pipelines - Using JsonLinesItemExporter
ITEM_PIPELINES = {
    'e_commerce_scraper.pipelines.JsonPipeline': 300,
}

# Remove FEEDS since we're using a custom pipeline
# FEEDS settings conflict with the `JsonPipeline` pipeline.
# FEEDS = {}

###############
# Retry on 503 status code
RETRY_ENABLED = True
RETRY_TIMES = 5  # Number of retries
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# Set download delay to avoid rate limiting
# CONCURRENT_REQUESTS = 16
