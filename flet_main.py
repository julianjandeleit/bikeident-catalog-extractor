#!/usr/bin/env python
import flet as ft
import pandas as pd
from dataclasses import dataclass, asdict
import yaml
import tabula
from threading import Thread
import numpy as np
import ast
from spreadsheet import Spreadsheet
import pdfplumber
#import uuid


def load_csv(path: str):
    return pd.read_csv(path)

# def df_to_view(df: pd.DataFrame):
#    columns = [ft.DataColumn(ft.Text(name)) for name in df.columns ]


#df = load_csv("data/table_out.csv")
df = pd.DataFrame()
df = df.rename(columns={"0":"A"})
dfs = [df]

class DataControl(ft.UserControl):
    def __init__(self, data, on_changed = None):
        super().__init__()
        self._data = data
        self._widget = ft.Container()
        self.on_changed = on_changed
        
        
    def get_data(self):
        return self._data
        
    def update_data(self, data):
        """ Update data and rebuild widget """
        self._data = data
        if self.on_changed != None:
            self.on_changed(self.get_data())
        if self.page != None:
            self.update()
        
    def store_attr(self,attr,value):
        """ Store attribute of data without rebuilding widget. (Necessary for storing input between external rebuild) """
        try:
            setattr(self._data,attr,value)
        except:
            # assume is dict
            self._data[attr] = value
        if self.on_changed != None:
            self.on_changed(self.get_data())

    def build_widget(self) -> ft.UserControl:
        return ft.Container() # override to change to your needs
        
    def _build_widget(self):
        widget = self.build_widget()
        self._widget.content = widget
        
    def build(self):
        self._build_widget()
        return self._widget
        
    def update(self):
        self._build_widget()
        if self.page != None:
            super().update()

class Test2(DataControl):
    def build_widget(self) -> ft.UserControl:
        text = ft.Text(self.get_data())
        button = ft.TextButton("change", on_click=lambda e: self.update_data("new value"))
        children = [text]
        if self.data != "new value":
            children += [button]
        return ft.Row(controls=children)

class Test(ft.UserControl):
    def __init__(self, data):
        print("init")
        super().__init__()
        self.data = data
        self.widget = ft.Container()
        
    def build_widget(self):
        self.text = ft.Text(self.data)
        self.button = ft.TextButton("change", on_click=self.handle_click)
        children = [self.text]
        if self.data != "new value":
            children += [self.button]
        self.widget.content = ft.Row(controls=children)
        #if self.data == "new value":
        #    self.button = ft.Container(padding=10, bgcolor="red")
        
    def build(self):
        print("build")
        self.build_widget()
        return self.widget
        
    def handle_click(self, e):
        print("handle")
        self.data = "new value"
        self.update()
        
    def update(self):
        print("update")
        self.build_widget()
        super().update()

class CustomCell(ft.UserControl):
    def __init__(self, value, row, col, parent):
        super().__init__()
        self.value = value
        self.row = row
        self.col = col
        self.parent = parent

    def build(self):
        return ft.Text(self.value)

    def open_dlg(self):
        global df
        tmp = list(df.loc[0])
        tmp[0] = "test"
        df.loc[0] = tmp
        #df.rename(columns={"A": "Test"},inplace=True)
        #print(self.df.columns)
        dlg = ft.AlertDialog(title=ft.Text(
            f"{self.value}"), content=ft.Text(f"({self.row}, {self.col})"))
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
        
class EditCell(DataControl):
    def __init__(self, data,on_data_changed = None, width = None):
        super().__init__(data)
        self.isEditing = False 
        self.on_data_changed = on_data_changed
        self.edit_width = width
        
    def build_widget(self) -> ft.UserControl:
        data, row, col = self.get_data()
        if self.isEditing:
            return ft.TextField(value=data,filled=True,border=None,text_style=ft.TextStyle(size=15),width=self.edit_width,autofocus=True,content_padding=0,on_blur=self.on_submit,on_submit=self.on_submit)
        else:
            return ft.GestureDetector(content=ft.Text(data), on_tap=lambda e: self.focus())
        
    def on_submit(self,e):
        new_val = e.control.value
        self.isEditing = False
        data, row, col = self.get_data()
        data = new_val
        self.update_data((data, row, col))
        if self.on_data_changed != None:
            self.on_data_changed(row, col, new_val)
    def focus(self):
        self.isEditing = True
        self.update_data(self.get_data())
        
class AddRemoveView(ft.UserControl):
    def __init__(self, label: str, positions, on_add, on_remove,col, on_update=None):
        positions = positions -1
        super().__init__(col=col)
        self.label = label
        self.on_add = on_add
        self.on_remove = on_remove
        self.slider = ft.Slider(value=0, min=0,max=positions if positions > 0 else 1, disabled= True if positions <= 0 else False,label="{value}",on_change=self.on_slider_change,divisions=positions if positions > 1 else None)
        self.slider_label = ft.Text("at index 0")
        self.on_update = on_update
        
    def on_slider_change(self,e):
        self.slider_label.value = "at index " +str(int(e.control.value))
        self.slider_label.update()
        if self.on_update:
            self.on_update(e.control.value)
        
    def build(self):
        self.vLabel = ft.Text(self.label)
        self.vAdd = ft.IconButton("add",on_click=lambda _: self.on_add(int(self.slider.value)))
        self.vRemove = ft.IconButton("remove", on_click=lambda _: self.on_remove(int(self.slider.value)))
        return ft.Row(
            controls=[self.vLabel, 
                                ft.Column([
                                    ft.Row([self.vAdd, self.vRemove]),
                                    ft.Row([self.slider_label,self.slider])],alignment=ft.MainAxisAlignment.START,horizontal_alignment=ft.CrossAxisAlignment.START)])
        
class CustomDataView(DataControl):
    
    #def __init__(data,on_changed = None):
    #    super().__init__(data=data,on_changed=on_changed)
        
        
    def on_inc_col(self, inc: int, pos: int):
        """inc should be 1 or -1"""
        df: pd.DataFrame = self.get_data()
        if inc == 1:
            print(f"cols {df.columns}")
            c_name = max([float(col) for col in df.columns if str(col).isalnum()],default=0)
            print(f"attempting {c_name}\n{df}")
            c_name = int(c_name+1)
            df.insert(pos,column=c_name,value=[np.nan for i in range(df.shape[0])])
        if inc == -1:
            #df = df.iloc[:, :-1]
            df = df.drop(df.columns[pos],axis=1)
            #print(df)
        df = df.reset_index(drop=True)
        self.update_data(df)
        
    def on_inc_row(self, inc: int, pos: int):
        """inc should be 1 or -1"""
        df: pd.DataFrame = self.get_data()
        if inc == 1:
            pre = df.iloc[:pos]
            #print(f"pre {pre}")
            new = pd.DataFrame([[np.nan]*len(df.columns)])
            post = df.iloc[pos:]
            #print(f"post {post}")
            df = pd.concat([pre, new,post],ignore_index=True)
        if inc == -1:
            df = df.drop([pos])
        
        df = df.reset_index(drop=True)
        #print(df)
        self.update_data(df)
        
    def on_create_empty(self):
        """creates dataframe with one cell"""
        df: pd.DataFrame = self.get_data()
        self.update_data(pd.DataFrame())
        self.on_inc_col(1)
        self.on_inc_row(1)

    
    def build_widget(self) -> ft.UserControl:        
        data : pd.DataFrame = self.get_data()
        rows = []
        for r in range(data.shape[0]):
            cells = []
            for c in range(data.shape[1]):
                cells.append(ft.DataCell(
                    EditCell((data.iloc[r, c], r, c), on_data_changed=self.cell_changed),
                    show_edit_icon=False,
                ))
            row = ft.DataRow(cells=cells)
            rows.append(row)
        return ft.Column(controls=[
            ft.ResponsiveRow(controls=[
                ft.TextButton("create Emptry",on_click=lambda _: self.on_create_empty(),col=4), 
                AddRemoveView(label="row",positions=data.shape[0]+1,on_add=lambda p: self.on_inc_row(1,p), on_remove=lambda p: self.on_inc_row(-1,p),col=4), 
                AddRemoveView(label="column",positions=data.shape[1]+1,on_add=lambda p: self.on_inc_col(1,p), on_remove=lambda p: self.on_inc_col(-1,p),col=4)]),
            ft.Row(
            scroll="ALWAYS",
            controls=[ft.DataTable(
            columns=[ft.DataColumn(
                ft.Row(alignment=ft.MainAxisAlignment.START,vertical_alignment=ft.CrossAxisAlignment.START,controls=[
                    EditCell((c, None,i),width=75,on_data_changed=self.col_changed)])) for i,c in enumerate(data.columns)],
            rows=rows,
        )])])
        
    def col_changed(self, _row, col, new_data):
        data = self.get_data()
        data.columns = data.columns.astype(str)
        #print("column change",data.columns.dtype, col,new_data)
        data.columns.values[col] = new_data
        self.update_data(data)
        #print(self.get_data())
        
    def cell_changed(self,row, col, new_data):
        data = self.get_data()
        data.iloc[row,col] = new_data
        self.update_data(data)
        

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
    
class EditableRow(DataControl):
    
    def __init__(self, data, label=None,on_changed=None):
        super().__init__(data,on_changed=on_changed)
        self.label = label
    
    def build_widget(self) -> ft.UserControl:
        data = self.get_data()
        #print(f"data is {data}")
        self.input = ft.TextField(value="",label="New Entry",autofocus=True,on_submit=self.close_dlg)
        self.dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Enter Name"),
            content=self.input,
            actions=[
                ft.TextButton("Yes", on_click=self.close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        listview = ft.Row(controls=[ft.Container(ft.Text(vers),bgcolor=ft.colors.BLACK12,padding=ft.padding.all(5),border_radius=5) for vers in data],wrap=True)
        editrow = ft.Row([ft.Container(listview,padding=ft.padding.all(15) ,border=ft.border.all(1,color="grey"),expand=True,border_radius=5), ft.IconButton(ft.icons.ADD,on_click=self.open_dlg),ft.IconButton(ft.icons.REMOVE,on_click=self.rm_elem)])
        
        if self.label != None:
            wrapper = ft.Column(controls=[ft.Text(self.label,style=ft.TextThemeStyle.HEADLINE_MEDIUM),editrow])
            return wrapper
        else:
            return editrow
        
    
    def open_dlg(self,e):
        self.page.dialog = self.dlg_modal
        self.dlg_modal.visible = True
        self.dlg_modal.open = True
        #print(self.get_data())
        self.page.update()

    def close_dlg(self,e):
        data = self.get_data()
#        print(type(data))
        data.append(self.input.value)
        self.dlg_modal.open = False
        self.page.update()
        self.update_data(data)
        
    def rm_elem(self, e):
        data: list = self.get_data()
        data.pop()
        self.update_data(data)
        
    
class CatalogView(DataControl):
    
    def __init__(self,data):
        super().__init__(data)
    
    def build_widget(self) -> ft.UserControl:
        data :Catalog = self.get_data()
        
        self.brand = ft.TextField(value=data.brand, label="Marke",on_blur=lambda _: self.store_attr("brand",self.brand.value),col=4)
        self.product_type = ft.TextField(value=data.product_type, label="Produktsparte",on_blur=lambda _: self.store_attr("product_type",self.product_type.value),col=4)
        self.version_key = ft.TextField(value=data.version_key, label="Charateristika Zuordnung (Spalte)",on_blur=lambda _: self.store_attr("version_key",self.version_key.value),col=4)
        self.versions = EditableRow(data.version_types,label="Produkt Charakteristika",on_changed=lambda d: self.store_attr("version_types",d))
        self.attribs = EditableRow(data.attribute_types,label="Produkt Eigenschaften (Tabellen Spalten)",on_changed=lambda d: self.store_attr("attribute_types",d))
        
        return ft.Column(controls=[ft.Text("Produktübergreifend",style=ft.TextThemeStyle.HEADLINE_LARGE),ft.Text("Allgemeines", style=ft.TextThemeStyle.HEADLINE_MEDIUM),ft.ResponsiveRow([self.brand,self.product_type, self.version_key]), self.versions, self.attribs])

        
class RepoPicker(DataControl):
    def __init__(self, data, on_dir_picked=None):
        super().__init__(data)
        self.get_directory_dialog = ft.FilePicker(on_result=self.on_pick_result)
        self.on_dir_picked = on_dir_picked
        
    def get_overlay(self):
        return self.get_directory_dialog
        
    def build_widget(self) -> ft.UserControl:
        data = self.get_data()
        repo = ft.Text(data if data != None else "Not Selected",overflow=ft.TextOverflow.ELLIPSIS,expand=True)
        return ft.Row([ft.TextButton("Speicherort",on_click=lambda _:self.get_directory_dialog.get_directory_path("open catalog directory")),repo])
        #self.get_directory_dialog = ft.FilePicker(on_result=self.on_pick_result)
        #self.page.overlay.append(self.get_directory_dialog)
        #return ft.Row([ft.TextButton("select directory",on_click=lambda _:self.get_directory_dialog.get_directory_path("open catalog directory")),repo])
 
    def on_pick_result(self, e):
            #self.page.overlay.remove(self.get_directory_dialog)
            #self.repo.value = e.path if e.path else "Cancelled"
            #self.repo.update()
            if e.path:
                self.update_data(e.path)
                if self.on_dir_picked != None:
                    self.on_dir_picked(self.get_data())

class PDFPicker(DataControl):
    def __init__(self, data, on_file_picked=None):
        super().__init__(data)
        self.get_directory_dialog = ft.FilePicker(on_result=self.on_pick_result)
        self.on_dir_picked = on_file_picked
        
    def get_overlay(self):
        return self.get_directory_dialog
        
    def build_widget(self) -> ft.UserControl:
        data = self.get_data()
        repo = ft.Text(data if data != None else "Not Selected",overflow=ft.TextOverflow.ELLIPSIS,expand=True)
        return ft.Row([
            ft.TextButton("Katalog PDF",on_click=lambda _:self.get_directory_dialog.pick_files("open catalog directory",allow_multiple=False, allowed_extensions=["pdf"])),
            repo])
        #self.get_directory_dialog = ft.FilePicker(on_result=self.on_pick_result)
        #self.page.overlay.append(self.get_directory_dialog)
        #return ft.Row([ft.TextButton("select directory",on_click=lambda _:self.get_directory_dialog.get_directory_path("open catalog directory")),repo])
 
    def on_pick_result(self, e:ft.FilePickerResultEvent):
            #self.page.overlay.remove(self.get_directory_dialog)
            #self.repo.value = e.path if e.path else "Cancelled"
            #self.repo.update()
            if e.files and len(e.files) != 0:
                self.update_data(e.files[0].path)
                if self.on_dir_picked != None:
                    self.on_dir_picked(self.get_data())
                    
class EditStrDict(DataControl):
    def __init__(self, data, on_changed=None, label=""):
        super().__init__(data, on_changed)
        self.label=label

    def build_widget(self) -> ft.UserControl:
        # Assuming key is string
        data : dict[str, str] =self.get_data()
        listview = ft.ResponsiveRow(controls=[ft.Container(ft.Column([ft.Text(value=key),ft.TextField(value=val, data=key,on_blur=lambda e: self.store_attr(e.control.data,e.control.value))]),bgcolor=ft.colors.BLACK12,padding=ft.padding.all(5),border_radius=5,col=4) for key, val in data.items()])
        editrow = ft.Row([ft.Container(width=50),ft.Container(listview,padding=ft.padding.all(15),border=ft.border.only(top=ft.border.BorderSide(1,"grey"),bottom=ft.border.BorderSide(1,"grey"),right=ft.border.BorderSide(1,"grey")),expand=True,border_radius=5)])
        
        return ft.Column(controls=[ft.Text(self.label),editrow])
            
class ProductListView(DataControl):

    def __init__(self, data, on_changed=None, on_select_product = None):
        super().__init__(data, on_changed)
        self.on_select_product = on_select_product

    def select(self, e):
        self.on_select_product(e.control.data)

    def remove(self,p):
        data :list[ProductSeries] = self.get_data()
        data.remove(p)
        self.update_data(data)

    def build_widget(self) -> ft.UserControl:
        data :list[ProductSeries] = self.get_data()
        def get_elem(product):
            return ft.Row([
                ft.IconButton(icon=ft.icons.REMOVE_CIRCLE_OUTLINE,data=product,on_click=lambda e: self.remove(e.control.data)),
                ft.TextButton(f"{product.name} {product.variant}", data=product, on_click=self.select)])
        return ft.Column([get_elem(p) for p in data]+[ft.IconButton(icon=ft.icons.ADD_CIRCLE_OUTLINE,on_click=lambda _: self.on_select_product(ProductSeries("","","",dict(),pd.DataFrame()))),],wrap=True)
    
def print_exception(msg, page, e: Exception):
    page.snack_bar = ft.SnackBar(
        bgcolor=ft.colors.RED,
            content=ft.Text(f"Exception {msg}\n{e}")
            )
    page.snack_bar.open = True
    page.update()
    
def print_info(msg, page):
    page.snack_bar = ft.SnackBar(
        bgcolor=ft.colors.BLUE,
            content=ft.Text(f"Info: {msg}")
            )
    page.snack_bar.open = True
    page.update()

class RepoView(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.picker = RepoPicker(None,on_dir_picked=self.on_select_repo)
        self.picker_catalog = PDFPicker(None,on_file_picked=self.on_select_catalog_file)

        catalog = Catalog(version_types=[],attribute_types=[])
        self.cv = CatalogView(catalog)
        self.init = ft.TextButton("Speicherort als neue Datenbank initialisieren",col=12, on_click=lambda _: self.init_repo(), disabled=True)

        self.tabs = ft.Tabs(selected_index=0, tabs=[ft.Tab(text="Produktübergreifend"), ft.Tab("Produkte"), ft.Tab(text="Produkt Details")])
        self.tabs_body = ft.Container(self.cv)
        self.tabs.on_change = self.tabs_changed

        self.products = ProductListView([], on_select_product=self.on_select_product)
        self.selected_product = None
        self.pdf_path = ""
        self.productView = ProductView(ProductSeries("","","",{},pd.DataFrame()),variant_types = catalog.version_types,attribute_types=catalog.attribute_types,pdf_path=self.pdf_path, on_changed=self.product_changed)
    
    def product_changed(self, product:ProductSeries):
        products :list[ProductSeries]= self.products.get_data()
        base_product: ProductSeries = self.productView.base_product
        #print(f"updating product {base_product} {product}\n{products}")
        if base_product.name == "" and base_product.variant == "":
            return
        if base_product in products:
            i = products.index(base_product)
            products[i] = product
        else:
            products.append(product)
        
        #self.products.update_data(products)

    def on_select_product(self,product:ProductSeries):
        #self.productView.update_data(e.control.data)
        self.selected_product = product
        #print(f"updating selected product to ", product.name)
        self.tabs.tabs[2].text = f"Produkt {product.name}"
        self.tabs.tabs[2].update()
        self.tabs.selected_index = 2
        self.tabs_changed(None)
        self.tabs.update()
        self.productView.base_product=product
        self.productView.update_data(product)
        self.update()

    def update_products(self):
        with open(repo_path+"/products.yaml","r+") as file:
            self.products.update_data([ProductSeries.from_dict(p) for p in yaml.safe_load_all(file)])

    def on_catalog_changed(self, c: Catalog):
        #print("catalog changed to "+c.brand)
        self.productView.variant_types = c.version_types
        self.productView.attribute_types = c.attribute_types
        self.update_products()

    def tabs_changed(self, e :ft.ControlEvent):
            #print("tabs changed "+str(self.tabs.selected_index))
            if repo_path == "" or repo_path == None:
                self.tabs.selected_index = 0
                self.tabs.update()
                # TODO: why does tab body get stuck when moving to other tabs before loading?
                return
            if self.tabs.selected_index == 0:
                self.tabs_body.content = self.cv
            if self.tabs.selected_index == 1:
                self.tabs_body.content = self.products
            if self.tabs.selected_index == 2:
                if self.selected_product == None:
                    self.tabs_body.content = ft.Text("Select Product first")
                else:
                    self.tabs_body.content = self.productView
            self.update()
        
    def build(self):
        return ft.Column([
            ft.ResponsiveRow([
                ft.Container(c,col=4,bgcolor=ft.colors.BLUE_GREY_100,border_radius=5) for c in [self.picker, self.picker_catalog]] + [ft.ElevatedButton("Daten Speichern", bgcolor=ft.colors.LIGHT_GREEN_200, col=4,on_click=lambda e: self.save_data()), self.init]),
            self.tabs, self.tabs_body])

    def get_overlays(self):
        return [self.picker.get_overlay(),self.picker_catalog.get_overlay()]

    def init_repo(self):
        c = Catalog(brand="",product_type="",version_key="", version_types=[],attribute_types=[])
        self.products.update_data([])
        self.cv.update_data(c)
        self.save_data()
        
        self.on_catalog_changed(c)
        self.init.disabled = True
        self.init.update()

    def on_select_repo(self, path):
        global repo_path #TODO: should provide callback which handles this to be independent from file the class is used in
        repo_path = path
        try:
            c = Catalog.load(repo_path+"/catalog.yaml")
            self.cv.update_data(c)
            self.on_catalog_changed(c)
            self.init.disabled = True
            self.init.update()
            print_info("catalog loaded", self.page)
        except Exception as e:
            #print_exception("loading data", self.page, e)
            print_info("Selected directory was not a Bikeident Database",self.page)
            self.init.disabled = False
            self.init.update()
    def on_select_catalog_file(self,file):
        self.pdf_path = file
        print(f"pdf path {self.pdf_path}")
        self.productView.pdf_path = self.pdf_path
        self.productView.update()
        #self.update_products()

    def save_data(self):
        #print("saving data")
        catalog = Catalog(self.cv.brand.value, self.cv.product_type.value, self.cv.version_key.value, self.cv.versions.get_data(), self.cv.attribs.get_data())
        products :list[ProductSeries]= self.products.get_data()

        try:
            catalog.save(repo_path+"/catalog.yaml")
            #self.on_catalog_changed(catalog)

            product_dicts = [p.to_dict() for p in products]
            with open(repo_path+"/products.yaml","w+") as file:
                yaml.safe_dump_all(product_dicts,file)
            

            self.page.snack_bar = ft.SnackBar(
                bgcolor=ft.colors.LIGHT_GREEN_600,
                content=ft.Text("Data Saved")
                )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(
                bgcolor=ft.colors.RED,
                content=ft.Text(f"Saving Failed:\n{e}")
                )
            self.page.snack_bar.open = True
            self.page.update()

class TableExtractor(ft.UserControl):
    def __init__(self, path, on_select_data = None):
        super().__init__()
        self.path = path
        self.on_select_data = on_select_data
        
        self.help_text =  """
Tabellen werden Extrahiert aus dem PDF welches oben bei `Katalog PDF` ausgewählt ist.
Um eine Tabelle zu extrahieren, die ensprechende Seitenzahl im PDF angeben und in dem Popup die passende Tabelle auswählen.
Bei Problemen muss das `Katalog PDF` möglicherweise ausgewählt werden bevor mit der Bearbeitung eines Produktes begonnen wird.
 
Abschließend müssen die vorgegebenen Spaltennamen der Tabelle noch manuell zugeordnet und umbenannt werden.
            
## Das Modul um Tabellen zu Extrahieren benötigt Java
            
Wenn Java auf dem PC noch nicht installiert ist:
            
1. [Java Umgebung](https://www.java.com/de/download/manual.jsp) herunterladen und installieren (zum Beispiel Version `Windows online`).
2. Computer neustarten (Je nach System reicht ein Neustart der App).
"""

    def on_choose(self, df):
        self.dlg.open = False
        self.page.update()
        if self.on_select_data != None:
            self.on_select_data(df)

    def on_read(self,pages):
        #self.page.ad.add(ft.Text(f"reading {pages}"))
        pages = ast.literal_eval(pages)
        if not isinstance(pages, list):
            pages = [pages]
        #self.page.add(ft.Text(f"starting tabula"))
        try:
            tables = pdfplumber.open(self.path, pages=pages)
            dfs = []
            for page in tables.pages:
                tables = page.find_tables(table_settings={"vertical_strategy": "lines_strict", "horizontal_strategy": "lines_strict"})
                for table in tables:
                    tc = table.extract(x_tolerance = 15)
                    df = pd.DataFrame(tc[0::])
                    df = df.replace(r'^\s*$', np.nan, regex=True)
                    df = df.fillna(value=np.nan)
                    #df.columns = df.columns.str.replace(r'^\s*$', "nan")
                    dfs.append(df)
            #dfs = tabula.read_pdf(self.path,pages=pages,guess=True,encoding="cp1252",pandas_options={"header":None})
        except Exception as e:
            print_exception("extracting table:",self.page, e)
            return
        #self.page.add(ft.Text(f"opening result dialog"))
        self.dlg = ft.AlertDialog(title=ft.Text("select table"),content=ft.Column([ft.Container(ft.TextButton(f"{df}", data=df,on_click=lambda e: self.on_choose(e.control.data)), padding=ft.padding.only(bottom=25)) for df in dfs], scroll="ALWAYS"),visible=True)
        self.page.dialog = self.dlg
        self.dlg.open = True
        self.page.update()
        
    def on_help(self):
        self.dlg = ft.AlertDialog(
            title=ft.Text("Anleitung Tabellen Extrahierer"),
            content=ft.Markdown(
            self.help_text,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            on_tap_link=lambda e: self.page.launch_url(e.data),
        ))
        self.page.dialog = self.dlg
        self.dlg.open = True
        self.page.update()
    
    def build(self):
        self.number = ft.TextField(label="Tabelle aus PDF lesen",tooltip="Seitenzahl",hint_text="22 oder [22, 23]", width=150, on_submit=lambda e: self.on_read(e.control.value))
        self.help = ft.IconButton(icon=ft.icons.HELP, on_click=lambda e: self.on_help())
        return ft.Row([self.number,self.help])
        
class ProductView(DataControl):
    def __init__(self, data: ProductSeries, variant_types: list[str],attribute_types, pdf_path="", on_changed = None):
        super().__init__(data, on_changed=on_changed)
        self.base_product = data
        self.variant_types = variant_types
        self.attribute_types = attribute_types
        self.variants_data = list(data.versions.keys())
        self.pdf_path = pdf_path

        
    def store_variants(self, d, do_update=True):
        # TODO: how to generalize this to DataControl?
        self.variants_data = d
        self.variant_entries.controls.clear()
        data :ProductSeries = self.get_data()
        #print("data", data)
        def store_version_attr(d: dict, key):
            print(f"got {d} {key}")
            data :ProductSeries = self._data
            data.versions[key] = d
            self.update_data(data)
            
        print(f"variants data {self.variants_data} {self.variant_types}")
        key_surplus = [k for k in data.versions.keys() if k not in self.variants_data]
        print(f"key surplus {key_surplus}")
        for k in key_surplus:
            del data.versions[k]
        for version in self.variants_data:
            entries = data.versions.get(version)
            print(f"{version} {entries}")
            if entries == None:
                entries = dict()
                for k in self.variant_types:
                    entries[k] = ""
            data.versions[version] = entries
            self.variant_entries.controls.append(EditStrDict(entries,label=version,on_changed=lambda d: store_version_attr(d,version)))
        if do_update:
            self.variant_entries.update()

    def store_missing_columns(self, do_update=True):
        data :ProductSeries= self.get_data()
        data.attributes = self.primary_attribs.get_data()
        print(self.get_data().attributes)
        self.missing_column_names.controls[1].controls  = [ft.Text(name) for name in self.attribute_types if name not in data.attributes.columns]
        if do_update:
            self.missing_column_names.update()

    def create_empty_table(self, e):
        """creates dataframe with one cell"""
        self.primary_attribs.update_data(pd.DataFrame())
        self.primary_attribs.on_inc_col(1,0)
        self.primary_attribs.on_inc_row(1,0)

    def build_widget(self) -> ft.UserControl:
        data: ProductSeries = self.get_data()
        self.variants_data = list(data.versions.keys())
        self.name = ft.TextField(value=data.name, label="Name",on_blur=lambda e: self.store_attr("name",e.control.value),col=4)
        self.finish = ft.TextField(value=data.variant, label="Ausführung", on_blur=lambda e:self.store_attr("variant",e.control.value),col=4)
        self.category = ft.TextField(value=data.product_category, label="Kategorie innerhalb Sparte", on_blur=lambda e:self.store_attr("product_category",e.control.value),col=4)
        self.variants = EditableRow(self.variants_data,label="Charakteristika Varianten", on_changed=lambda d: self.store_variants(d))
        self.variant_entries = ft.Column([])
        self.store_variants(self.variants_data,do_update=False) # build entries for initial data

        def onDF(df):
            self.primary_attribs.update_data(df)
            self.store_attr("attributes", df)
        self.table_selector = TableExtractor(self.pdf_path, on_select_data=lambda df: onDF(df))
        self.missing_column_names = ft.Column([ft.Text("Missing Column Names",style=ft.TextThemeStyle.LABEL_MEDIUM),ft.Row([],wrap=True)])
        self.init_df = ft.TextButton("Leere Tabelle Erstellen",on_click=self.create_empty_table)
        self.primary_attribs = Spreadsheet(data.attributes,on_changed=lambda e: self.store_missing_columns())
        self.store_missing_columns(do_update=False)
        return ft.Column([ft.Text("Product",style=ft.TextThemeStyle.HEADLINE_MEDIUM),ft.ResponsiveRow([self.name,self.finish,self.variants]), self.variant_entries,self.missing_column_names,ft.Row([self.table_selector,self.init_df]),self.primary_attribs])

        
repo_path = None


 
def main(page: ft.Page):

    print("starting app")
    page.title = "BikeIdent Database Editor"
    page.window_width = 1080
    page.window_height = 720
    page.window_min_height = 480
    page.window_min_width = 640
    page.scroll = "ALWAYS"

    repoView = RepoView()
    page.overlay.extend(repoView.get_overlays())
    page.add(repoView)
        
    page.update()


ft.app(target=main)
