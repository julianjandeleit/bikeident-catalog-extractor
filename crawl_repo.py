#%%
from repository import Repository, Catalog, ProductSeries

# scrape webpage
import scrapy
from scrapyscript import Job, Processor
# text cleaning
import re
from typing import Type
import pandas as pd
import pathlib
import json
from urllib.parse import urlencode

processor = Processor(settings=None)

#%%
class ReifenSpider(scrapy.Spider):

    name = "BikeComponents"
    chunk_idx = 1
    url_template = "https://www.bike-components.de/de/s/?keywords={query}"

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)


        self.start_urls = [
            self.url_template.format(query=urlencode({"keywords": kwargs["query"]}))
        ]


    def parse(self, response):
        products = pd.json_normalize(json.loads(response.text)["initialData"]["products"])
        print(f"------- {products}")
        if len(products) == 0:
            return
        
        for index, product in products.iterrows():
            yield {
                "brand": product["data.manufacturer"].strip(),
                "product": product["data.name"].strip(),
                "price": re.findall("\d+\,\d+",product["data.price"]),
                "link": response.urljoin(product["data.link"]),
            }

        self.chunk_idx += 1
        target = self.url_template.format(chunk=self.chunk_idx)
        yield response.follow(target, callback=self.parse)
#%% load repository
ARTNO_KEY = 'ART.-NO.'
repo = Repository.load(path=pathlib.Path("/home/julian/code/BikeIdent/demo_catalog"))
def filter_attrs(repo: Repository):
    for entry in repo.entries:
        m = entry.attributes
        m = m.replace({"nan": None})
        m = m[m[ARTNO_KEY].str.len() > 3]
        entry.attributes = m
filter_attrs(repo)
#%% exec
for entry in repo.entries:
    print(entry.name, entry.variant)
    for art_no in entry.attributes[ARTNO_KEY]:
        print(art_no)


#job = Job(ReifenSpider)
#results = processor.run(job)
# %%
