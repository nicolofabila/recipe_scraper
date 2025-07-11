# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class WebscraperItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    ingredients = scrapy.Field()
    time = scrapy.Field()  # dict: prep, cook, total
    dietary_labels = scrapy.Field()
    fitness_relevance = scrapy.Field()
    difficulty = scrapy.Field()
    instructions = scrapy.Field()
    ratings = scrapy.Field()
