# amazon-python-scrapy-scraper
Python Scrapy spider that searches Amazon for a particular keyword, extracts each products ASIN ID and scrape all the main information from the product page. The spider will iterate through all pages returned by the keyword query. The following are the fields the spider scrapes for the Amazon product page:

* ASIN
* Product name
* Image url
* Price
* Description
* Available sizes
* Available colors
* Ratings
* Number of reviews
* Seller rank

This Amazon spider uses [Scraper API](https://www.scraperapi.com/) as the proxy solution. Scraper API has a free plan that allows you to make up to 1,000 requests per month which makes it ideal for the development phase, but can be easily scaled up to millions of pages per month if needs be.

## Using the Amazon Spider
Make sure Scrapy is installed:

```
pip install scrapy
```

Set the keywords you want to search in Amazon.

```
queries = ['tshirt for men', ‘tshirt for women’]
```

Signup to [Scraper API](https://www.scraperapi.com/signup) and get your free API key that allows you to scrape 1,000 pages per month for free. Enter your API key into the API variable:

```
API = ‘<YOUR_API_KEY>’

def get_url(url):
    payload = {'api_key': API, 'url': url}
    proxy_url = 'http://api.scraperapi.com/?' + urlencode(payload)
    return proxy_url

```

To activate geotageting, JS rendering, residential proxies, etc. then just add an extra parameter to the payload. Example: geotargeting requests from the United States.

```
def get_url(url):
    payload = {'api_key': API, 'url': url, 'country_code': 'us'}
    proxy_url = 'http://api.scraperapi.com/?' + urlencode(payload)
    return proxy_url
```

By default, the spider is set to have a max concurrency of 5 concurrent requests as this the max concurrency allowed on Scraper APIs free plan. If you have a plan with higher concurrency then make sure to increase the max concurrency in the `settings.py`.

```
## settings.py

CONCURRENT_REQUESTS = 5
RETRY_TIMES = 5

# DOWNLOAD_DELAY
# RANDOMIZE_DOWNLOAD_DELAY
```
We should also set `RETRY_TIMES` to tell Scrapy to retry any failed requests (to 5 for example) and make sure that `DOWNLOAD_DELAY`  and `RANDOMIZE_DOWNLOAD_DELAY` aren’t enabled as these will lower your concurrency and are not needed with Scraper API.

To run the spider, use:

```
scrapy crawl amazon -o test.csv
```

## Editing the Amazon Spider
The spider has 4 parts:

1. **start_requests -** will send a search query Amazon with a particular keyword.
2. **parse_keyword_response -** will extract the ASIN value for each product returned in the Amazon keyword query, then send a new request to Amazon to return the product page of that product. It will also move to the next page and repeat the process.
3. **parse_product_page -** will extract all the target information from the product page.
4. **get_url -** will send the request to Scraper API so it can retrieve the HTML response.

If you don't want to scrape every page returned for that keyword then comment out the `next_page` section of the parse_keyword_response:

```
def parse_keyword_response(self, response):
        products = response.xpath('//*[@data-asin]')

        for product in products:
            asin = product.xpath('@data-asin').extract_first()
            product_url = f"https://www.amazon.com/dp/{asin}"
            yield scrapy.Request(url=get_url(product_url), callback=self.parse_product_page, meta={'asin': asin})
            
        # next_page = response.xpath('//li[@class="a-last"]/a/@href').extract_first()
        # if next_page:
        #     url = urljoin("https://www.amazon.com",next_page)
        #     yield scrapy.Request(url=get_url(url), callback=self.parse_keyword_response)
 ```
 
 If you want to scrape more or less fields on the product page then edit the XPath selectors in the `parse_product_page` function:
 
 ```
def parse_product_page(self, response):
        asin = response.meta['asin']
        title = response.xpath('//*[@id="productTitle"]/text()').extract_first()
        image = re.search('"large":"(.*?)"',response.text).groups()[0]
        rating = response.xpath('//*[@id="acrPopover"]/@title').extract_first()
        number_of_reviews = response.xpath('//*[@id="acrCustomerReviewText"]/text()').extract_first()
        price = response.xpath('//*[@id="priceblock_ourprice"]/text()').extract_first()

        if not price:
            price = response.xpath('//*[@data-asin-price]/@data-asin-price').extract_first() or \
                    response.xpath('//*[@id="price_inside_buybox"]/text()').extract_first()
        
        temp = response.xpath('//*[@id="twister"]')
        sizes = []
        colors = []
        if temp:
            s = re.search('"variationValues" : ({.*})', response.text).groups()[0]
            json_acceptable = s.replace("'", "\"")
            di = json.loads(json_acceptable)
            sizes = di.get('size_name', [])
            colors = di.get('color_name', [])
        
        bullet_points = response.xpath('//*[@id="feature-bullets"]//li/span/text()').extract()
        seller_rank = response.xpath('//*[text()="Amazon Best Sellers Rank:"]/parent::*//text()[not(parent::style)]').extract()
        yield {'asin': asin, 'Title': title, 'MainImage': image, 'Rating': rating, 'NumberOfReviews': number_of_reviews,
               'Price': price, 'AvailableSizes': sizes, 'AvailableColors': colors, 'BulletPoints': bullet_points,
               'SellerRank': seller_rank}
```
