from decimal import Decimal
from unittest.mock import patch, Mock
from django.test import TestCase, SimpleTestCase
from django.core.management import call_command
from catalog.models import Product
from catalog.scraper import parse_product, parse_listing, safe_url, ScrapeError, BooksClient

URL = 'https://books.toscrape.com/catalogue/example_1/index.html'
HTML = '''<div class="product_main"><h1>Example &amp; Book</h1><p class="price_color">£12.50</p></div>
<div class="item active"><img src="../../media/example.jpg"></div>
<div id="product_description"></div><p>A sample description.</p>
<table><tr><th>UPC</th><td>sample-1</td></tr><tr><th>Availability</th><td>In stock (3 available)</td></tr></table>'''

class ParserTests(SimpleTestCase):
    def test_product(self):
        data = parse_product(HTML, URL)
        self.assertEqual(data['title'], 'Example & Book')
        self.assertEqual(data['price'], Decimal('12.50'))
        self.assertEqual(data['image_url'], 'https://books.toscrape.com/media/example.jpg')
        self.assertEqual(data['description'], 'A sample description.')

    def test_layout_change_fails(self):
        with self.assertRaises(ScrapeError):
            parse_product('<html>Blocked</html>', URL)

    def test_listing_and_next(self):
        links, nxt = parse_listing('<article class="product_pod"><h3><a href="example_1/index.html">Book</a></h3></article><li class="next"><a href="page-2.html">Next</a></li>', 'https://books.toscrape.com/catalogue/page-1.html')
        self.assertEqual(links, [URL])
        self.assertTrue(nxt.endswith('/catalogue/page-2.html'))

    def test_external_urls_rejected(self):
        with self.assertRaises(ScrapeError):
            safe_url(URL, 'https://other.example/book')

    def test_throttle_stops_without_retry(self):
        client = BooksClient(0)
        with patch.object(client.session, 'get', return_value=Mock(status_code=429)) as get:
            with self.assertRaises(ScrapeError):
                client.get(URL)
            self.assertEqual(get.call_count, 1)
        client.close()

class IntegrationTests(TestCase):
    @patch('catalog.scraper.BooksClient.products')
    def test_repeat_run_updates_and_exports(self, products):
        products.side_effect = lambda pages: iter([parse_product(HTML, URL)])
        call_command('scrape', pages=1)
        call_command('scrape', pages=1)
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(self.client.get('/').status_code, 200)
        data = self.client.get('/export/json/').json()
        self.assertEqual(data[0]['price'], '12.50')
        self.assertEqual(data[0]['currency'], 'GBP')
        self.assertContains(self.client.get('/export/csv/'), 'sample-1')
        self.assertEqual(self.client.get('/export/json/?q=absent').json(), [])

    def test_csv_formula_safety(self):
        data = parse_product(HTML, URL)
        data['title'] = '=1+1'
        Product.objects.create(**data)
        self.assertContains(self.client.get('/export/csv/'), "'=1+1")
