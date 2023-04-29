#%%
from repository import Repository, Catalog, ProductSeries

# scrape webpage
import scrapy
from scrapy.http.response.html import HtmlResponse
from scrapy.selector.unified import Selector
from scrapyscript import Job, Processor
# text cleaning
import re
from typing import Type
import pandas as pd
import pathlib
import json
from urllib.parse import urlencode
from tqdm.auto import tqdm
settings = scrapy.settings.Settings(values={'LOG_LEVEL': 'CRITICAL'})
processor = Processor(settings=settings)


#%%
class ReifenSpider(scrapy.Spider):

    name = "BikeComponents"
    chunk_idx = 1
    url_template = "https://www.bike-components.de/de/s/?{query}"

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)

        self.extractor = kwargs["extractor"]

        self.start_urls = [
            self.url_template.format(query=urlencode({"keywords": kwargs["query"]}))
        ]


    def parse(self, response):
        target = response.xpath('//*[@id="grid-content"]/div/div/div[1]/a[1]/@href').get()
        target = response.urljoin(target)
        target = target.replace("/de/","/en/")
        yield response.follow(target, callback=self.parse_product)
        
    def parse_product(self, response: HtmlResponse):
        elems = list(response.xpath('//*[@id="module-product-detail"]/div[3]/div[2]/div/div[1]/ul/li'))
        #print("url: ", response.url)
        res = self.extractor(elems)
        yield res
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
def extractor(artNo: str, product: ProductSeries, elements: list[Selector]):
    product.attributes = product.attributes.set_index(ARTNO_KEY)
    attribs = product.attributes.loc[artNo].to_dict()
    for elem in elements:
        info_text = "".join(elem.xpath("./div/text()").getall())
        # find matching entry
        has_color = re.search(str(attribs['COLOUR']).strip(), info_text.strip(), re.IGNORECASE)
        has_etrto = re.search(str(attribs['ETRTO']).strip(), info_text.strip(), re.IGNORECASE)
        has_size = re.search(str(attribs['SIZE']).strip(), info_text.strip(), re.IGNORECASE)
        if has_color and (has_etrto or has_size):
            in_stock = re.search("in stock", info_text) != None
            price_text = "".join(elem.xpath("./div/div/text()").getall())
            ts = re.search('(\d+[,\.]\d+)€', price_text)
            price = None
            if ts:
                price = ts.group(1)
                # we want dots in our data
                price = price.replace(',','.')
            return {"in_stock":in_stock, "price": price}
        
results = []
for entry in tqdm(repo.entries):
    for art_no in entry.attributes[ARTNO_KEY]:
        job = Job(ReifenSpider, query=entry.name+" "+entry.variant, extractor=lambda es: extractor(art_no, entry, es))
        result = processor.run(job)
        if len(result) != 0:
            results.append((art_no, result[0]))
# flatten results
results = [(a, d['in_stock'], d['price']) for a, d in results]
df = pd.DataFrame(results, columns=["artno", "in stock", "price"])
df = df.set_index("artno")
print(df)
#job = Job(ReifenSpider)
#results = processor.run(job)
# %%
