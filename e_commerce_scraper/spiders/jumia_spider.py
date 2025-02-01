import scrapy
from e_commerce_scraper.items import ProductItem


class JumiaSpiderSpider(scrapy.Spider):
    name = "jumia_spider"
    allowed_domains = ["jumia.com.eg"]
    start_urls = [f"https://www.jumia.com.eg"]
    # page_count = 0

    def __init__(self, product_name=None, *args, **kwargs):
        super(JumiaSpiderSpider, self).__init__(*args, **kwargs)
        self.product_name = product_name
        self.start_urls = [f"https://www.jumia.com.eg/catalog/?q={product_name}/"]


    def parse(self, response):
        products_url = response.css('article.prd._fb.col.c-prd a.core::attr(href)').getall()

        if not products_url:
            yield response.request.replace(dont_filter=True)
            return

        for product_url in products_url:
            product_url = 'https://www.jumia.com.eg' + product_url
            yield response.follow(product_url, callback=self.parse_product)

    def extract_description(self, response):
        description = response.css('div.markup.-mhm.-pvl.-oxa.-sc p::text').get()
        if not description:
            description = response.css('div.markup.-mhm.-pvl.-oxa.-sc::text').get()
            if not description:
                description = ''
        description += ', '.join(response.css('div.markup.-mhm.-pvl.-oxa.-sc ul li::text').getall())

        return description.strip()

    def extract_product_details(self, response):
        # Select the <ul> list and iterate over each <li> item
        product_details = {}

        # Select all <li> elements inside the <ul>
        list_items = response.css('ul.-pvs.-mvxs.-phm.-lsn li.-pvxs')
        values = response.css('ul.-pvs.-mvxs.-phm.-lsn li.-pvxs::text').getall()

        for i in range(len(list_items)):
            key = list_items[i].css('span.-b::text').get()
            value = values[i]

            # Add the key-value pair to the dictionary
            if key and value:
                product_details[key] = value.replace(': ', '')

        return product_details

    def extract_reviews(self, response):
        reviews_elements = response.css('article.-pvs.-hr._bet')
        reviews = {}
        if not reviews_elements:
            reviews = "There are no reviews"
            return reviews

        review_counter = 1
        for review in reviews_elements:
            reviewer_name = review.css('div.-df.-j-bet.-i-ctr.-gy5 div.-pvs span:nth-child(2)::text').get()
            if reviewer_name:
                reviewer_name = reviewer_name.replace('by ', '')
            review_rate = review.css('div.stars._m._al.-mvs::text').get()
            if review_rate:
                review_rate = review_rate.split(' ')[0]
            review_date = review.css('div.-df.-j-bet.-i-ctr.-gy5 span.-prs::text').get()
            verified_purchase = review.css('div.-df.-i-ctr.-gn5.-fsh0::text').get()
            if not verified_purchase:
                verified_purchase = 'Not Verified Purchase'
            review_text = review.css('p.-pvs::text').get()

            reviews[f'Review no. {review_counter}'] = {
                'reviewer_name': reviewer_name,
                'review_rate': review_rate,
                'review_date': review_date,
                'verified_purchase': verified_purchase,
                'review_text': review_text,
            }
            review_counter += 1
        return reviews

    def parse_product(self, response):
        img_url = response.css('div#imgs a::attr(href)').get()

        if not img_url:
            yield response.request.replace(dont_filter=True)
            return
        product_item = ProductItem()
        img_url = response.css('div#imgs a::attr(href)').get()
        title = response.css('h1.-fs20.-pts.-pbxs::text').get()
        brand = response.css('p.-m.-pbs::text').get()
        description = self.extract_description(response)
        features = response.css('div.markup.-pam li::text').getall()
        product_details = self.extract_product_details(response)
        product_price = response.css('span.-b.-ubpt.-tal.-fs24.-prxs::text').get()
        if not product_price:
            product_price = "Price not available"
        else:
            product_price = product_price.replace('EGP', '').split('-')
        product_rate = response.css('div.-df.-i-ctr.-pbs div.stars._m._al::text').get()
        if not product_rate:
            product_rate = "There are no rates"
        else:
            product_rate = product_rate.split(' ')[0]
        number_of_rates = response.css('div.-df.-i-ctr.-pbs a.-plxs._more::text').get()
        if not number_of_rates:
            number_of_rates = "There are no rates"
        number_of_rates = (number_of_rates.replace('verified', '').replace(')', '')
                           .replace('(', '').replace('  ratings', '')
                           .replace(' rating', ''))
        product_sizes = response.css('label.vl::text').getall()
        product_colors = "No other available colors"
        reviews = self.extract_reviews(response)

        product_item['product_url'] = response.url
        product_item['img_url'] = img_url
        product_item['product_title'] = title
        product_item['brand'] = brand
        product_item['description'] = description
        product_item['features'] = features
        product_item['details'] = product_details
        product_item['product_price'] = product_price
        product_item['product_rate'] = product_rate
        product_item['number_of_rates'] = number_of_rates
        product_item['product_sizes'] = product_sizes
        product_item['colors'] = product_colors
        product_item['reviews'] = reviews

        yield product_item
