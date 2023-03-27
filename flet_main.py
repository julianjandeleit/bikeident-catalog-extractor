#!/usr/bin/env python
import flet as ft
import pandas as pd
from dataclasses import dataclass, asdict
import yaml
import tabula
from threading import Thread
import ast
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

class EditableDataView(ft.UserControl):
    def __init__(self, data: pd.DataFrame):
        super().__init__()
        #print("create")
        self.df = data
        self.build_rows()
        self.test = False
     
    def build_rows(self):
        rows = []
        for r in range(self.df.shape[0]):
            cells = []
            for c in range(self.df.shape[1]):
                cells.append(ft.DataCell(
                    CustomCell(self.df.iloc[r, c], r, c, self),
                    show_edit_icon=False,
                    on_tap=lambda e: e.control._DataCell__content.open_dlg()
                ))
            row = ft.DataRow(cells=cells)
            rows.append(row)
        self.rows = rows

    def build(self):
        #print(f"{df.columns}")
        self.build_rows()
        rws = self.rows
        if self.test:
            rws = []
        self.test = True
        return ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c)) for c in df.columns],
            rows=rws,
        )
        
class EditCell(DataControl):
    def __init__(self, data,on_data_changed = None, width = None):
        super().__init__(data)
        self.isEditing = False 
        self.on_data_changed = on_data_changed
        self.edit_width = width
        
    def build_widget(self) -> ft.UserControl:
        data, row, col = self.get_data()
        if self.isEditing:
            return ft.TextField(value=data,filled=True,border=None,text_style=ft.TextStyle(size=15),width=self.edit_width,autofocus=True,content_padding=0,on_submit=self.on_submit)
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
        
class CustomDataView(DataControl):
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
        return ft.Row(
            scroll="ALWAYS",
            controls=[ft.DataTable(
            columns=[ft.DataColumn(ft.Row(alignment=ft.MainAxisAlignment.START,vertical_alignment=ft.CrossAxisAlignment.START,controls=[EditCell((c, None,i),width=75,on_data_changed=self.col_changed)])) for i,c in enumerate(data.columns)],
            rows=rows,
        )])
        
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
        print("loading "+path)
        with open(path, "r+") as file:
            c = yaml.safe_load(file)
            c = Catalog(**c)
            return c

    def save(self,path):
        with open(path,"w+") as file:
            yaml.safe_dump(asdict(self),file)
    
@dataclass
class ProducSeries:
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
        return ProducSeries(**dct)
    
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
    
    def __init__(self,data, on_save = None):
        super().__init__(data)
        self.on_save = on_save
    
    def build_widget(self) -> ft.UserControl:
        data :Catalog = self.get_data()
        
        self.brand = ft.TextField(value=data.brand, label="brand",on_blur=lambda _: self.store_attr("brand",self.brand.value),col=4)
        self.product_type = ft.TextField(value=data.product_type, label="product_type",on_blur=lambda _: self.store_attr("product_type",self.product_type.value),col=4)
        self.version_key = ft.TextField(value=data.version_key, label="version_key",on_blur=lambda _: self.store_attr("version_key",self.version_key.value),col=4)
        self.versions = EditableRow(data.version_types,label="Version Types",on_changed=lambda d: self.store_attr("version_types",d))
        self.attribs = EditableRow(data.attribute_types,label="Attribute Types",on_changed=lambda d: self.store_attr("attribute_types",d))
        
        return ft.Column(controls=[ft.Text("Catalog",style=ft.TextThemeStyle.HEADLINE_LARGE),ft.Text("Basis Attributes", style=ft.TextThemeStyle.HEADLINE_MEDIUM),ft.ResponsiveRow([self.brand,self.product_type, self.version_key]), self.versions, self.attribs, ft.ElevatedButton("Save", on_click=self.save)])

    def save(self, e):
        catalog = Catalog(self.brand.value, self.product_type.value, self.version_key.value, self.versions.get_data(), self.attribs.get_data())
        #y = yaml.dump(catalog,allow_unicode=True,default_flow_style=False,tags=False,explicit_start=True)
        #c = yaml.safe_load(y)
        #y = yaml.safe_dump(asdict(catalog))
        #c = yaml.safe_load(y)
        #c = Catalog(**c)
        #print(c)
        if self.on_save != None:
            self.on_save(catalog)
            
        self.page.snack_bar = ft.SnackBar(
            bgcolor=ft.colors.LIGHT_GREEN_600,
            content=ft.Text("Catalog Saved")
            )
        self.page.snack_bar.open = True
        self.page.update()
        
class RepoPicker(DataControl):
    def __init__(self, data, on_dir_picked=None):
        super().__init__(data)
        self.get_directory_dialog = ft.FilePicker(on_result=self.on_pick_result)
        self.on_dir_picked = on_dir_picked
        
    def get_overlay(self):
        return self.get_directory_dialog
        
    def build_widget(self) -> ft.UserControl:
        data = self.get_data()
        repo = ft.Text(data if data != None else "Not Selected")
        return ft.Row([ft.TextButton("select directory",on_click=lambda _:self.get_directory_dialog.get_directory_path("open catalog directory")),repo])
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
            
        
class RepoView(ft.UserControl):
    def __init__(self, on_catalog_changed = None):
        super().__init__()
        self.picker = RepoPicker(None,on_dir_picked=self.on_select_repo)
        self.on_catalog_changed = on_catalog_changed
        def on_save(c: Catalog):
             c.save(repo_path+"/catalog.yaml")
             if self.on_catalog_changed != None:
                 self.on_catalog_changed(c)

        self.cv = CatalogView(Catalog(version_types=[],attribute_types=[]), on_save=on_save)
        
    def build(self):
        return ft.Column([self.picker, self.cv])

    def get_overlay(self):
        return self.picker.get_overlay()

    def on_select_repo(self, path):
        global repo_path #TODO: should provide callback which handles this to be independent from file the class is used in
        repo_path = path
        c = Catalog.load(repo_path+"/catalog.yaml")
        self.cv.update_data(c)
        if self.on_catalog_changed != None:
            self.on_catalog_changed(c)

class TableExtractor(ft.UserControl):
    def __init__(self, path, on_select_data = None):
        super().__init__()
        self.path = path
        self.on_select_data = on_select_data

    def on_choose(self, df):
        self.dlg.open = False
        self.page.update()
        if self.on_select_data != None:
            self.on_select_data(df)

    def on_read(self,pages):
        #self.page.ad.add(ft.Text(f"reading {pages}"))
        pages = ast.literal_eval(pages)
        #self.page.add(ft.Text(f"starting tabula"))
        #try:
        dfs = tabula.read_pdf(self.path,pages=pages,pandas_options={"header":None})
        #except Exception as e:
        #    self.page.add(ft.Text(f"tabular failed with {e}"))
        self.page.add(ft.Text(f"opening result dialog"))
        self.dlg = ft.AlertDialog(title=ft.Text("select table"),content=ft.Column([ft.Container(ft.TextButton(f"{df}", data=df,on_click=lambda e: self.on_choose(e.control.data)), padding=ft.padding.only(bottom=25)) for df in dfs], scroll="ALWAYS"),visible=True)
        self.page.dialog = self.dlg
        self.dlg.open = True
        self.page.update()
    
    def build(self):
        self.number = ft.TextField(label="Enter Page Number",tooltip="needs to be a number",hint_text="22 or [22, 23]", width=150, on_submit=lambda e: self.on_read(e.control.value))
        return self.number
        
class ProductView(DataControl):
    def __init__(self, data: ProducSeries, variant_types: list[str],attribute_types, on_save):
        super().__init__(data)
        self.variant_types = variant_types
        self.attribute_types = attribute_types
        self.variants_data = list(data.versions.keys())
        self.on_save = on_save
        
    def store_variants(self, d, do_update=True):
        # TODO: how to generalize this to DataControl?
        self.variants_data = d
        self.variant_entries.controls.clear()
        data :ProducSeries = self.get_data()
        def store_version_attr(d: dict, key):
            print(f"got {d} {key}")
            data :ProducSeries = self._data
            data.versions[key] = d

        for version in self.variants_data:
            entries = data.versions.get(version)
            if entries == None:
                entries = dict()
                for k in self.variant_types:
                    entries[k] = ""
                data.versions[version] = entries
            self.variant_entries.controls.append(EditStrDict(entries,label=version,on_changed=lambda d: store_version_attr(d,version)))
            
        if do_update:
            self.variant_entries.update()

    def store_missing_columns(self, do_update=True):
        data :ProducSeries= self.get_data()
        self.missing_column_names.controls = [ft.Text(name) for name in self.attribute_types if name not in data.attributes.columns]
        if do_update:
            self.missing_column_names.update()

    def build_widget(self) -> ft.UserControl:
        data: ProducSeries = self.get_data()
        self.name = ft.TextField(value=data.name, label="name",on_blur=lambda e: self.store_attr("name",e.control.value),col=4)
        self.finish = ft.TextField(value=data.variant, label="finish", on_blur=lambda e:self.store_attr("variant",e.control.value),col=4)
        self.category = ft.TextField(value=data.product_category, label="product class", on_blur=lambda e:self.store_attr("product_category",e.control.value),col=4)
        self.variants = EditableRow(self.variants_data,label="variants", on_changed=lambda d: self.store_variants(d))
        self.variant_entries = ft.Column([])
        self.store_variants(self.variants_data,do_update=False) # build entries for initial data

        path = "C:/Users/Julian/Downloads/Schwalbe Katalog 2022.pdf"
        def onDF(df):
            self.primary_attribs.update_data(df)
            self.store_attr("attributes", df)
        self.table_selector = TableExtractor(path, on_select_data=lambda df: onDF(df))
        self.missing_column_names = ft.Row([],wrap=True)
        self.primary_attribs = CustomDataView(data.attributes,on_changed=lambda e: self.store_missing_columns())
        self.store_missing_columns(do_update=False)
        self.save = ft.ElevatedButton("Save", on_click=lambda _: self.on_save(self.get_data()))
        return ft.Column([ft.Text("Product",style=ft.TextThemeStyle.HEADLINE_MEDIUM),ft.ResponsiveRow([self.name,self.category,self.finish,self.variants]), self.variant_entries, self.table_selector,self.missing_column_names,self.primary_attribs,self.save])

        
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
    page.overlay.append(repoView.get_overlay())
    catalog :Catalog = repoView.cv.get_data()
    def on_product_save(ps: ProducSeries):
        #ps.save(repo_path+"/products.yaml")
        yml = ps.to_yaml()
        print(yml)
        print(ProducSeries.from_yaml(yml))

    productView = ProductView(ProducSeries("","","",{}, pd.DataFrame()),variant_types = catalog.version_types,attribute_types=catalog.attribute_types,on_save=on_product_save)
    def on_catalog_changed(c: Catalog):
        productView.variant_types = c.version_types
        productView.attribute_types = c.attribute_types
    repoView.on_catalog_changed = on_catalog_changed 
    tbs = ft.Tabs(selected_index=0, tabs=[ft.Tab(text="Catalog"), ft.Tab(text="Entries")])
    tbs_body = ft.Container(repoView)
    def tabs_changed(e :ft.ControlEvent):
        print("tabs changed "+str(tbs.selected_index))
        if tbs.selected_index == 0:
            tbs_body.content = repoView
        if tbs.selected_index == 1:
            tbs_body.content = productView
        page.update()
    tbs.on_change = tabs_changed

    page.add(tbs)
    page.add(tbs_body)
        
    page.update()


ft.app(target=main)
