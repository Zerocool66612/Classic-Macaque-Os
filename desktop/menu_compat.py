"""Give generated submenus explicit ownership on PySide6 6.8 and newer."""
from PySide6.QtWidgets import QMenu
from shiboken6 import isValid

class Menu(QMenu):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self._generated_submenus=[]
    def addMenu(self,*args):
        if len(args)==1 and isinstance(args[0],str):
            child=Menu(args[0],self)
        elif len(args)==2 and isinstance(args[1],str):
            child=Menu(args[1],self);child.setIcon(args[0])
        else:return super().addMenu(*args)
        super().addMenu(child);self._generated_submenus.append(child);return child
    def clear(self):
        generated=self._generated_submenus;self._generated_submenus=[];super().clear()
        for child in generated:
            if isValid(child):child.deleteLater()
