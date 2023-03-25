#!/usr/bin/env python
import flet as ft
import pandas as pd
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
            return ft.TextField(value=data,text_size=15,border=None,text_style=ft.TextStyle(size=7), content_padding=0,on_submit=self.on_submit)
        else:
            return ft.GestureDetector(content=ft.Text(data), on_tap=lambda e: self.on_tap())
        
    def on_submit(self,e):
        new_val = e.control.value
        self.isEditing = False
        data, row, col = self.get_data()
        data = new_val
        self.update_data((data, row, col))
        if self.on_data_changed != None:
            self.on_data_changed(row, col, new_val)
    def on_tap(self):
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
#                    on_tap=lambda e: self.on_tap((e.control._DataCell__content.get_data()[1], e.control._DataCell__content.get_data()[2]))
#                    on_tap=lambda e: e.control._DataCell__content.open_dlg()
                ))
            row = ft.DataRow(cells=cells)
            rows.append(row)
        return ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c)) for c in data.columns],
            rows=rows,
        )
        
    def cell_changed(self,row, col, new_data):
        data = self.get_data()
        data.iloc[row,col] = new_data
        self.update_data(data)
        print(self.get_data().head())
        
 
def main(page: ft.Page):


    page.scroll = "ALWAYS"

    t = ft.Text(value="Hello, world", color="green")
    page.controls.append(t)

    tt = ft.Text("A")

    page.add(ft.Row(controls=[
        tt,
        ft.Text("B"),
        ft.Text("C"),
    ]
    ))
    
    page.add(Test2("old data"))
    page.add(Test2("older data"))
    
    page.add(CustomDataView(df))

    ev = ft.Ref[EditableDataView(df)]()

    def button_clicked(e):
        page.add(ft.Text(f"Clicked! {df.columns}\n{ev.df}"))
        ev.current.build_rows()
        ev.current.build()
        ev.current.df = df
        tt.value = "ASDF"
        page.update()

    page.add(ft.ElevatedButton(
        text="Click Me",
        on_click=button_clicked
    ))

    #page.add(ev)

    page.update()


ft.app(target=main)
