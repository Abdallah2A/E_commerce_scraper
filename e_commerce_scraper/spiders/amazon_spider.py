import scrapy
import re
from e_commerce_scraper.items import ProductItem
from datetime import datetime


class AmazonSpiderSpider(scrapy.Spider):
    name = "amazon_spider"
    allowed_domains = ["amazon.eg"]

    def __init__(self, product_name=None, *args, **kwargs):
        super(AmazonSpiderSpider, self).__init__(*args, **kwargs)
        self.product_name = '+'.join(product_name.split())  # Format product name for URL
        self.start_urls = [f"https://www.amazon.eg/-/en/s?k={self.product_name}"]

    def start_requests(self):
        """Override start_requests to ensure the spider uses the correct search URL"""
        search_url = f"https://www.amazon.eg/-/en/s?k={self.product_name}"
        yield scrapy.Request(url=search_url, callback=self.parse)

    def parse(self, response):
        products = response.css('div.a-section.a-spacing-base')

        if not products:
            self.logger.error(f"No products found for: {self.product_name}")
            return

        for product in products:
            product_url = product.css('a.a-link-normal.s-no-outline::attr(href)').get()
            if not product_url:
                continue
            product_url = ('https://www.amazon.eg' + product.css('a.a-link-normal.s-line-clamp-4.s-link-style'
                                                                 '.a-text-normal::attr(href)').get())
            yield response.follow(product_url, callback=self.parse_product)

    def extract_price_from_core(self, response):
        """Extract price components from the core price container."""
        price = response.xpath(
            '//div[@id="corePriceDisplay_desktop_feature_div"]//span[@class="a-price-whole"]/text()'
        ).get()
        fraction = response.xpath(
            '//div[@id="corePriceDisplay_desktop_feature_div"]//span[@class="a-price-fraction"]/text()'
        ).get()
        currency = response.xpath(
            '//div[@id="corePriceDisplay_desktop_feature_div"]//span[@class="a-price-symbol"]/text()'
        ).get()
        if price and currency:
            return f"{currency}{price}.{fraction or '00'}"
        return None

    def clean_price(self, price_list):
        """Clean and format price list."""
        return ' - '.join([p.strip() for p in price_list if p.strip()])

    def extract_sizes(self, response):
        """Extract product sizes from the dropdown menu."""
        size_options = response.xpath(
            '//select[@name="dropdown_selected_size_name"]/option[@data-a-html-content]'
        )
        sizes = [
            option.xpath('@data-a-html-content').get().strip()
            for option in size_options
            if option.xpath('@data-a-html-content').get()
        ]
        return sizes if sizes else ["Sizes not available"]

    def extract_colors(self, response):
        """Extract product colors from the color variation section."""
        color_items = response.xpath(
            '//div[@id="variation_color_name"]//ul[@class="a-unordered-list a-nostyle a-button-list a-declarative'
            ' a-button-toggle-group a-horizontal a-spacing-top-micro swatches swatchesRectangle imageSwatches"]//li'
        )
        colors = []
        for item in color_items:
            title = item.xpath('./@title').get()
            if title:
                # Remove "Click to select" from the title
                color = title.replace("Click to select ", "").strip()
                colors.append(color)
        return colors if colors else ["No other available colors"]

    def extract_product_details(self, response):
        """
        Extract product details from the section with ID 'detailBulletsWrapper_feature_div'
        and return it as a cleaned dictionary.
        """
        details = {}

        # Locate the product details section
        details_section = response.css('div#detailBulletsWrapper_feature_div')

        # Extract individual details from the list items
        ul_detail_items = details_section.css('ul.a-unordered-list.a-nostyle.a-vertical.a-spacing-none'
                                              '.detail-bullet-list')

        for detail_items in ul_detail_items:
            items = detail_items.css('span.a-list-item')
            for item in items:
                # Extract key and value
                key = item.xpath('.//span[@class="a-text-bold"]/text()').get()
                value = item.xpath('.//span[not(@class="a-text-bold")]/text()').get()
                category = item.xpath('.//span[@class="a-list-item"]/a/text()').get()

                if category and value:
                    value = f"{value.strip()} {category.strip()} "

                if key and value:
                    # Clean up key and value
                    pattern = r'[\u200f\u200e\n:]'
                    key = re.sub(pattern, '', key).strip()

                    # Add cleaned data to dictionary
                    if key.count('Customer reviews') > 0:
                        continue
                    details[key] = value
        return details

    def extract_about_product(self, response):
        """Extract product about from about section"""
        about_product = []
        about_dots = response.xpath('//*[contains(text(), "About this item")]/following-sibling::ul//li')

        for dot in about_dots:
            about_product.append(dot.xpath('.//text()').get())

        return about_product

    def extract_product_features(self, response):
        features = []

        # Case 1: Table-based structure
        table_rows = response.xpath('//div[contains(@class, "a-section")]/table//tr')
        if table_rows:
            for row in table_rows:
                key = row.xpath('.//span[@class="a-size-base a-text-bold"]/text()').get()
                value = row.xpath('.//span[@class="a-size-base po-break-word"]/text()').get()
                if key and value:
                    features.append(f"{key}: {value}")

        # Case 2: List-based structure
        keys = response.css('div.a-fixed-left-grid-col.a-col-left span.a-color-base:not(.a-size-medium)::text').getall()
        values = response.css('div.a-fixed-left-grid-col.a-col-right span.a-color-base::text').getall()
        for i in range(len(keys)):
            if keys[i] and values[i]:
                features.append(f"{keys[i].strip()}: {values[i].strip()}")

        return features

    def extract_reviews(self, response):
        reviews_elements = response.css('ul#cm-cr-dp-review-list li')
        reviews = {}
        if not reviews_elements:
            reviews = "There are no reviews"
            return reviews

        review_counter = 1
        for review in reviews_elements:
            reviewer_name = review.css('span.a-profile-name::text').get()
            review_rate = review.css('span.a-icon-alt::text').get().split(' ')[0]
            date_part = review.css('span.review-date::text').get().split('on ')[-1]
            parsed_date = datetime.strptime(date_part, '%d %B %Y')
            review_date = parsed_date.strftime('%d-%m-%Y').lstrip('0').replace('-0', '-')

            verified_purchase = review.css('span.a-size-mini.a-color-state.a-text-bold::text').get()
            if not verified_purchase:
                verified_purchase = 'Not Verified Purchase'
            review_text_element = (review.css('span.a-size-base.review-text span.cr-original-review-content::text')
                                   .getall())
            review_text = ' '.join(review_text_element).strip()

            reviews[f'Review no. {review_counter}'] = {
                'reviewer_name': reviewer_name,
                'review_rate': review_rate,
                'review_date': review_date,
                'verified_purchase': verified_purchase,
                'review_text': review_text
            }
            review_counter += 1
        return reviews

    def parse_product(self, response):
        img_url = response.css('div#imgTagWrapperId img::attr(src)').get()

        if not img_url:
            yield response.request.replace(dont_filter=True)
            return

        product_item = ProductItem()
        # Extract product price
        # # Main price extraction logic
        product_price = response.css('span.a-price-range span.a-price span.a-offscreen::text').getall()

        if not product_price:
            product_price = response.css('#corePrice_desktop .a-offscreen::text').get()

        if not product_price:
            product_price = self.extract_price_from_core(response)

        if isinstance(product_price, list):
            product_price = self.clean_price(product_price[:2])

        # # Fallback if no price is found
        if not product_price:
            product_price = "Price not available"
        else:
            product_price = product_price.replace('EGP', '').split('-')

        # Extract product rating
        product_rate = response.css('span.a-declarative i.a-icon span.a-icon-alt::text').get()
        if not product_rate:
            product_rate = "There are no rates"
        else:
            product_rate = product_rate.split(' ')[0].strip()

        # Extract number of reviews
        number_of_rates = response.css('span#acrCustomerReviewText::text').get()
        if not number_of_rates:
            number_of_rates = "There are no rates"
        else:
            number_of_rates = number_of_rates.strip().replace(' ratings', '')

        # Extract sizes
        product_sizes = self.extract_sizes(response)

        # Extract colors
        product_colors = self.extract_colors(response)

        # Extract details
        product_details = self.extract_product_details(response)

        # Extract about
        about_product = self.extract_about_product(response)
        if not about_product:
            about_product = ''

        # Extract description
        description = response.css('div#productDescription span::text').get()
        if not description:
            description = ''
        description += f"\n{about_product}".strip()

        # Extract features
        features = self.extract_product_features(response)

        # Extract reviews
        reviews = self.extract_reviews(response)

        # Extract image
        img_url = response.css('div#imgTagWrapperId img::attr(src)').get()

        # Extract brand
        brand = response.css('a#bylineInfo::text').get()
        if brand:
            brand = brand.replace('Visit the ', '').replace(' Store', '').replace('Brand: ', '').strip()

        # Extract title
        title = response.css('span#productTitle::text').get()
        if title:
            title = title.strip()

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
