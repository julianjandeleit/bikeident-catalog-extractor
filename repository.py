
import pandas as pd
from dataclasses import dataclass, asdict
import yaml
import pathlib

@dataclass
class Catalog:
    brand: str = "" # Schwalbe
    product_type: str = "" # Reifen
    version_key: str = "" # "VERSION"
    version_types: list[str] = list # ["SCHWALBE PROTECTION", "ROLLING", "ROAD GRIP", ...]
    attribute_types: list[str] = list # ["DIAGMETER","ETRTO","VERSION",...]
    
    def load(path):
        #print("loading "+path)
        with open(path, "r+") as file:
            c = yaml.safe_load(file)
            c = Catalog(**c)
            return c

    def save(self,path):
        with open(path,"w+") as file:
            yaml.safe_dump(asdict(self),file)
    
@dataclass(eq=False)
class ProductSeries:
    name: str = "" # SUPER MOTO-X
    variant: str = "" # Performance Line, Drahtreifen - HS 439
    product_category: str = "" # URBAN
    versions: dict = dict # DD,Gr -> Rolling->3, RoadGrip->5, ..., DD, RA -> Rolling->4, RoadGrip->4, ...
    attributes: pd.DataFrame = pd.DataFrame # ETRTO:, SIZE:, COLOR:, BAR:, PSI:, ...
    
    def to_yaml(self):
        data = asdict(self)
        data["attributes"] = data["attributes"].to_dict()
        return yaml.safe_dump(data)

    def from_yaml(yaml_str):
        dct = yaml.safe_load(yaml_str)
        dct["attributes"] = pd.DataFrame.from_dict(dct["attributes"])
        return ProductSeries(**dct)
    
    def to_dict(self):
        data = asdict(self)
        data["attributes"] = data["attributes"].to_dict()
        return data
    
    def __eq__(self, __value: object) -> bool:
        if  not isinstance(__value, ProductSeries):
            return False
        v :ProductSeries = __value
        return v.name == self.name and v.variant == self.variant
    

    def from_dict(dct: dict):
        dct = dct.copy()
        dct["attributes"] = pd.DataFrame.from_dict(dct["attributes"])
        return ProductSeries(**dct)
    

@dataclass
class Repository:
    meta: Catalog
    entries: ProductSeries
    
    def save(self, path: pathlib.Path):
        self.catalog.save(path / "catalog.yaml")
            #self.on_catalog_changed(catalog)

        product_dicts = [entry.to_dict() for entry in self.entries]
        with open(path / "products.yaml","w+") as file:
            yaml.safe_dump_all(product_dicts,file)
            
    def load(self, path: pathlib.Path):
        catalog = Catalog.load(path / "catalog.yaml")
        products = []
        with open(path / "products.yaml","r+") as file:
            products += [ProductSeries.from_dict(p) for p in yaml.safe_load_all(file)]
            
        self.meta = catalog
        self.entries = products