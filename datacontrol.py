import flet as ft
from typing import Generic, TypeVar


D = TypeVar('D')
class DataControl(ft.UserControl,Generic[D]):
    def __init__(self, data: D, on_changed = None):
        super().__init__()
        self._data = data
        self._widget = ft.Container()
        self.on_changed = on_changed
        
        
    def get_data(self) -> D:
        return self._data
        
    def update_data(self, data: D):
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