import flet as ft
from datacontrol import DataControl
import pandas as pd
import numpy as np

def _buildColumn(series: pd.Series, col_index: int, on_context_click, on_text_changed, highlight_row=None):
    vCells = ft.Column([])
    def on_h(e: ft.HoverEvent):
        if e.data == "true":
            e.control.bgcolor = ft.colors.BLUE_100
        else:
            e.control.bgcolor = None
        e.control.update()
    for i, c in enumerate(series.tolist()):
        vCells.controls.append(ft.GestureDetector(data=i,content=ft.Container(EditCell((c, col_index, i),on_data_changed=on_text_changed),bgcolor="red" if i == highlight_row else None, on_hover=on_h),on_secondary_tap=lambda e:on_context_click(col_index, e.control.data)))
    return vCells

def _buildDialog(x,y,on_close):
    return ft.AlertDialog(modal=False,actions_alignment=ft.MainAxisAlignment.END,
                   title=ft.Text(f"Zelle {x} {y}"),
                   content=ft.ResponsiveRow([
        ft.Column(controls=[
            ft.TextButton("Spalte löschen",on_click=lambda _:on_close("spalte löschen",x,y)),
            ft.TextButton("neue spalte links einfügen",on_click=lambda _:on_close("spalte links",x,y)),
            ft.TextButton("neue spalte rechts einfügen",on_click=lambda _:on_close("spalte rechts",x,y))],
        col=6,tight=True,alignment=ft.MainAxisAlignment.START),
        ft.Column(controls=[
            ft.TextButton("Zeile löschen",on_click=lambda _:on_close("zeile löschen",x,y)),
            ft.TextButton("neue Zeile darüber einfügen",on_click=lambda _:on_close("zeile oben",x,y)),
            ft.TextButton("neue zeile darunter einfügen",on_click=lambda _:on_close("zeile unten",x,y)),],
        col=6,tight=True,alignment=ft.MainAxisAlignment.START),
        ft.TextButton("Zeile mit Spaltennamen tauschen",on_click=lambda _:on_close("zeile header",x,y),col=12),],alignment=ft.MainAxisAlignment.START,vertical_alignment=ft.CrossAxisAlignment.START))

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

class Spreadsheet(DataControl[pd.DataFrame]):
    def __init__(self, data: pd.DataFrame, on_changed=None):
        super().__init__(data, on_changed)
        self.highlight_column = None
        self.highlight_row = None


    def on_inc_col(self, inc: int, pos: int):
        """inc should be 1 or -1"""
        df: pd.DataFrame = self.get_data()
        if inc == 1:
            print(f"cols {df.columns}")
            c_name = max([float(col) for col in df.columns if str(col).isnumeric()],default=0)
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

    def on_context(self, x,y):
        if self.page == None:
            return
        def on_close(name, x, y):
            #print(name,x,y)
            if name == "spalte löschen":
                self.on_inc_col(-1,x)
            if name == "spalte links":
                self.on_inc_col(1,x)
            if name == "spalte rechts":
                self.on_inc_col(1,x+1)
            if name == "zeile löschen":
                self.on_inc_row(-1,y)
            if name == "zeile oben":
                self.on_inc_row(1,y)
            if name == "zeile unten":
                self.on_inc_row(1,y+1)

            if name == "zeile header":
                df = self.get_data()
                columns_old = df.columns.astype(str)
                df.columns = df.iloc[y].astype(str)
                df.iloc[y] = columns_old.astype(str)
                #df = pd.concat([df.iloc[:,x].str.split(" ",expand=True),df])
                self.update_data(df)
            
            self.page.dialog.open = False
            self.page.update()
        self.page.dialog = _buildDialog(x,y,on_close=on_close)
        self.page.dialog.open = True
        self.page.update()

    def on_text_changed(self, row, col, text):
        print("on text changesd",col,row)
        df = self.get_data()
        df.iloc[col,row] = text
        self.update_data(df)

    def col_changed(self, _row, col, new_data):
        data = self.get_data()
        data.columns = data.columns.astype(str)
        #print("column change",data.columns.dtype, col,new_data)
        data.columns.values[col] = new_data
        self.update_data(data)
        #print(self.get_data())

    def build_widget(self) -> ft.UserControl:
        df = self.get_data()

        vBody = ft.Row(scroll="ALWAYS")
        for i in range(df.shape[1]):
            #print(df.iloc[:,i])
    
            series :pd.Series = df.iloc[:,i]
            #print(series)
            vName = EditCell((series.name, None,i),width=75,on_data_changed=self.col_changed)
            vCol = _buildColumn(series, i,highlight_row=self.highlight_row,on_context_click=self.on_context,on_text_changed=lambda e,f,c: self.on_text_changed(e,f,c))
            vBody.controls.append(ft.Container(ft.Column(controls=[vName,ft.Text("-"),vCol]),bgcolor="red" if self.highlight_column == i else None))
        
        return vBody

def main(page: ft.Page):

    print("starting app")
    sheet = Spreadsheet(pd.read_csv("data/table_out.csv"))
    def on_highlight_column(e):
        sheet.highlight_column = 2
        sheet.update()
    page.add(ft.TextButton("highlight col",on_click=on_highlight_column))

    def on_highlight_row(e):
        sheet.highlight_row = 4
        print(sheet.get_data())
        sheet.update()

    page.add(ft.TextButton("highlight row",on_click=on_highlight_row))
    page.add(ft.Container(padding=ft.padding.all(50),content=sheet))
        
    page.update()


#ft.app(target=main)