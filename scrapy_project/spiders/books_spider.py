import scrapy
import json
import os

class BooksSpider(scrapy.Spider):
    name = 'books'
    allowed_domains = ['books.toscrape.com']
    start_urls = ['https://books.toscrape.com/']
    
    def __init__(self):
        # Buat folder data jika belum ada
        if not os.path.exists('data'):
            os.makedirs('data')
    
    def parse(self, response):
        # Ekstrak semua link buku dari halaman
        book_links = response.css('article.product_pod h3 a::attr(href)').getall()
        
        # Ikuti setiap link buku
        for link in book_links:
            yield response.follow(link, self.parse_book)
        
        # Cari link ke halaman berikutnya
        next_page = response.css('li.next a::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)
    
    def parse_book(self, response):
        # Ekstrak rating dari class stars
        rating_class = response.css('p.star-rating::attr(class)').get()
        rating_map = {
            'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5
        }
        rating = 0
        if rating_class:
            rating_word = rating_class.split()[-1]
            rating = rating_map.get(rating_word, 0)
        
        # Ekstrak availability
        availability_text = response.css('p.availability::text').getall()
        availability = ' '.join([text.strip() for text in availability_text if text.strip()])
        
        # Ekstrak informasi buku
        yield {
            'title': response.css('h1::text').get(),
            'price': response.css('p.price_color::text').get(),
            'rating': rating,
            'availability': availability,
            'description': response.css('#product_description ~ p::text').get(),
            'upc': response.css('table.table-striped tr:nth-child(1) td::text').get(),
            'category': response.css('ul.breadcrumb li:nth-child(3) a::text').get(),
            'image_url': response.urljoin(response.css('div.item img::attr(src)').get())
        }
