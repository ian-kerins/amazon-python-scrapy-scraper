# -*- coding: utf-8 -*-
import scrapy
from urllib.parse import urlencode
from urllib.parse import urljoin
import re
import json
import os
import logging
queries = ["girls  knitted skirts"]    ##Enter keywords here ['keyword1', 'keyword2', 'etc']
API = 'b5e67c4d019e3aa20b24fae797cf884f'                        ##Insert Scraperapi API key here. Signup here for free trial with 5,000 requests: https://www.scraperapi.com/signup


def get_url(url):
    payload = {'api_key': API, 'url': url, 'country_code': 'us'}
    proxy_url = 'http://api.scraperapi.com/?' + urlencode(payload)
    return proxy_url


class AmazonSpider(scrapy.Spider):
    name = 'amazon'

    def start_requests(self):
        for query in queries:
            url = 'https://www.amazon.com/s?' + urlencode({'k': query})
            yield scrapy.Request(url=get_url(url), callback=self.parse_keyword_response, meta={'query': query})

    def parse_keyword_response(self, response):
        products = []
        pattern = "/dp/B0[A-Z0-9]{8}"
        matches = re.findall(pattern, response.text)
        for match in matches:
            products.append(match[4:])
        products = list(set(products))
        logging.log(logging.WARNING, products)

        query_filename = '_'.join(response.meta['query'].split())
        for product in products:
            asin = product
            product_url = f"https://www.amazon.com/dp/{asin}"
            yield scrapy.Request(url=get_url(product_url), callback=self.parse_product_page, meta=
                                    {'asin': asin, 'filename': query_filename})

        next_page_class = "s-pagination-item.s-pagination-next.s-pagination-button.s-pagination-separator"
        next_page_query = 'a.'+next_page_class+"::attr(href)"
        next_page = response.css(next_page_query).get()
        if next_page:
            url = urljoin("https://www.amazon.com", next_page)
            yield scrapy.Request(url=get_url(url), callback=self.parse_keyword_response,
                                 meta={'query': response.meta['query']})

    def parse_product_page(self, response):

        filename = response.meta['filename']
        asin = response.meta['asin']
        page = response.text
        title = response.xpath('//*[@id="productTitle"]/text()').extract_first()
        rating = response.xpath('//*[@id="acrPopover"]/@title').extract_first()
        number_of_reviews = response.xpath('//*[@id="acrCustomerReviewText"]/text()').extract_first()
        price = response.xpath('//*[@id="priceblock_ourprice"]/text()').extract_first()
        files = os.listdir()
        if filename not in files:
            os.mkdir(filename)

        with open(filename+"/"+asin+".html", 'w') as f:
            f.write(page)

        yield {
            "asin": asin, "title": title, 'No. of ratings': number_of_reviews, 'Stars': rating, "price": price,
        }



