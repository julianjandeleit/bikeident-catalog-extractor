#!/usr/bin/env python
import flet as ft
import pandas as pd
from dataclasses import dataclass, asdict
import yaml
import asyncio
from threading import Thread
#import uuid


def load_csv(path: str):
    return pd.read_csv(path)

# def df_to_view(df: pd.DataFrame):
#    columns = [ft.DataColumn(ft.Text(name)) for name in df.columns ]


df = load_csv("data/table_out.csv")
df = df.rename(columns={"0":"A"})
dfs = [df]

class DataControl(ft.UserControl):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self._widget = ft.Container()
        
        
    def get_data(self):
        return self._data
        
    def update_data(self, data):
        self._data = data
        self.update()
        
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
    def __init__(self, data,on_data_changed = None):
        super().__init__(data)
        self.isEditing = False 
        self.on_data_changed = on_data_changed
        
    def build_widget(self) -> ft.UserControl:
        data, row, col = self.get_data()
        if self.isEditing:
            return ft.TextField(value=data,filled=True,border=None,text_style=ft.TextStyle(size=15),autofocus=True,content_padding=0,on_submit=self.on_submit)
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
            columns=[ft.DataColumn(ft.Row(alignment=ft.MainAxisAlignment.START,vertical_alignment=ft.CrossAxisAlignment.START,controls=[EditCell((c, None,i),on_data_changed=self.col_changed)])) for i,c in enumerate(data.columns)],
            rows=rows,
        )])
        
    def col_changed(self, _row, col, new_data):
        data = self.get_data()
        data.columns.values[col] = new_data
        self.update_data(data)
        print(self.get_data())
        
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
    
class EditableRow(DataControl):
    
    def __init__(self, data, label=None):
        super().__init__(data)
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

        listview = ft.Row(controls=[ft.Container(ft.Text(vers),bgcolor=ft.colors.BLACK12,padding=ft.padding.all(5),border_radius=5) for vers in data])
        editrow = ft.Row([ft.Container(listview,padding=ft.padding.all(15) ,border=ft.border.all(1,color="grey"),height=75,expand=True,border_radius=5), ft.IconButton(ft.icons.ADD,on_click=self.open_dlg),ft.IconButton(ft.icons.REMOVE,on_click=self.rm_elem)])
        
        if self.label != None:
            wrapper = ft.Column(controls=[ft.Text(self.label,style=ft.TextThemeStyle.HEADLINE_MEDIUM),editrow])
            return wrapper
        else:
            return editrow
        
    
    def open_dlg(self,e):
        self.page.dialog = self.dlg_modal
        self.dlg_modal.visible = True
        self.dlg_modal.open = True
        print(self.get_data())
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
        
        self.brand = ft.TextField(value=data.brand, label="brand")
        self.product_type = ft.TextField(value=data.product_type, label="product_type")
        self.version_key = ft.TextField(value=data.version_key, label="version_key")
        self.versions = EditableRow(data.version_types,label="Version Types")
        self.attribs = EditableRow(data.attribute_types,label="Attribute Types")
        
        return ft.Column(controls=[ft.Text("Catalog",style=ft.TextThemeStyle.HEADLINE_LARGE),ft.Text("Basis Attributes", style=ft.TextThemeStyle.HEADLINE_MEDIUM),ft.Row([self.brand,self.product_type, self.version_key]), self.versions, self.attribs, ft.ElevatedButton("Save", on_click=self.save)])

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
        repo = ft.Text(data if data != None else "<Select>")
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
        
class RepoView(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.picker = RepoPicker(None,on_dir_picked=self.on_select_repo)
        
    def build(self):
        self.cv = CatalogView(Catalog(version_types=[],attribute_types=[]), on_save=lambda c: c.save(repo_path+"/catalog.yaml"))
        return ft.Column([self.picker, self.cv])

    def get_overlay(self):
        return self.picker.get_overlay()

    def on_select_repo(self, path):
        global repo_path
        repo_path = path
        self.cv.update_data(Catalog.load(repo_path+"/catalog.yaml"))
        
repo_path = None


 
def main(page: ft.Page):

    print("starting app")
    page.title = "BikeIdent PDF Catalog Extractor"
    page.scroll = "ALWAYS"

    rv = RepoView()
    page.overlay.append(rv.get_overlay())
    tv = ft.Text("tab2")    
    tbs = ft.Tabs(selected_index=0, tabs=[ft.Tab(text="Catalog"), ft.Tab(text="Entries")])
    tbs_body = ft.Container()
    def tabs_changed(e :ft.ControlEvent):
        print("tabs changed "+str(tbs.selected_index))
        if tbs.selected_index == 0:
            tbs_body.content = rv
        if tbs.selected_index == 1:
            tbs_body.content = tv
        page.update()
    tbs.on_change = tabs_changed

    page.add(tbs)
    page.add(tbs_body)
        
    page.update()


ft.app(target=main)
