# from main import scrape_news
from singleSiteVer import scrape_news
import unittest


class TestClass(unittest.TestCase):
    def test_null(self):
        with self.assertRaises(TypeError):
            scrape_news(time_range="10 days ago",selected_topics="",num_articles=2)
    def test_invalidNumber(self):    
        with self.assertRaises(IndexError):
            scrape_news(time_range="10 days ago",selected_topics="Technology news",num_articles=-1)
    def test_type(self):
        with self.assertRaises(TypeError):
            scrape_news(time_range="10 days ago",selected_topics=7,num_articles=2)
    def test_date(self):
        with self.assertRaises(TypeError):
            scrape_news(time_range="why",selected_topics="Technology news",num_articles=2)

