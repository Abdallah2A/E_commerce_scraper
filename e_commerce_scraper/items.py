# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ECommerceScraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class ProductItem(scrapy.Item):
    product_url = scrapy.Field()
    img_url = scrapy.Field()
    product_title = scrapy.Field()
    brand = scrapy.Field()
    description = scrapy.Field()
    features = scrapy.Field()
    details = scrapy.Field()
    product_price = scrapy.Field()
    product_rate = scrapy.Field()
    number_of_rates = scrapy.Field()
    product_sizes = scrapy.Field()
    colors = scrapy.Field()
    reviews = scrapy.Field()
