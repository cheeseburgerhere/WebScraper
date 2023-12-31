from generate_summaries import generate_summaries,ReadingTime,ComplexityLevel
from singleSiteVer import scrape_news
import pandas as pd

import unittest


class TestClass(unittest.TestCase):
    def test_null(self):
        with self.assertRaises(ValueError):
            df=pd.DataFrame()
            generate_summaries(df,ComplexityLevel.EASY,ReadingTime.ONE_MINUTE)
    def test_invalidNumber(self):    
        with self.assertRaises(ValueError):
            df=pd.DataFrame({
                "Content":[],
                "Test":["test","test"]
            })
            generate_summaries(df,ComplexityLevel.EASY,ReadingTime.ONE_MINUTE)
    def test_type(self):
        with self.assertRaises(ValueError):
            df=scrape_news("10 days ago","world",2)
            temp:pd.DataFrame=df.iloc[:,0:-1]
            outputToSeries=pd.Series([])
            outputToSeries.name="Summaries"
            df=pd.merge(temp,outputToSeries,right_index=True,left_index=True)
            generate_summaries(df,ComplexityLevel.EASY,ReadingTime.ONE_MINUTE)