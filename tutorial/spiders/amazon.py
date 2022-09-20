# -*- coding: utf-8 -*-
import scrapy
from urllib.parse import urlencode
import boto3
import os
import pandas as pd
queries = ["girls knitted skirts"]  ## Enter keywords here ['keyword1', 'keyword2', 'etc']
API = '8b3a71023fb9b91ea8df34d364e883e4'  ## Insert Scraperapi API key here. Signup here for free trial with 5,000 requests: https://www.scraperapi.com/signup


def get_url(url):
    payload = {'api_key': API, 'url': url, 'country_code': 'us'}
    proxy_url = 'http://api.scraperapi.com/?' + urlencode(payload)
    return proxy_url


class AmazonSpider(scrapy.Spider):
    name = 'amazon'

    def start_requests(self):
        filename = "asin_codes.csv"
        df = pd.read_csv(filename)
        query = filename[:-4]
        codes = list(set(list(df["codes"])))
        s3 = boto3.resource('s3')
        for code in codes:
            url = 'https://www.amazon.com/dp/' + code
            yield scrapy.Request(url=get_url(url), callback=self.parse_product_page, meta={
                'code': code, 'query': query, 's3': s3 })

    def parse_product_page(self, response):

        s3 = response.meta['s3']
        code = response.meta['code']
        query = response.meta['query']

        files = os.listdir()
        if "codes" not in files:
            os.mkdir("codes")
        if query not in os.listdir("codes"):
            os.mkdir("codes/"+query)

        page = response.text

        s3.Bucket('testamzproductpages').put_object(Key=code + ".html", Body=page)

        with open('codes/'+code+".html", "w") as f:
            f.write(page)

        title = response.xpath('//*[@id="productTitle"]/text()').extract_first()
        rating = response.xpath('//*[@id="acrPopover"]/@title').extract_first()
        number_of_reviews = response.xpath('//*[@id="acrCustomerReviewText"]/text()').extract_first()
        yield {
            "asin": code, "title": title, 'No. of ratings': number_of_reviews, 'Stars': rating,
        }



