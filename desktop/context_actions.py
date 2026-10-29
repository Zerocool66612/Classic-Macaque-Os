"""Shared file actions for desktop and file windows; never imports host files."""
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu,QInputDialog,QApplication

from menu_compat import Menu as QMenu

class ContextActions:
    def editable_paths(self,paths):
        try:
            for p in paths:self.disk.editable(p)
            return bool(paths)
        except (ValueError,OSError):return False
    def folder_writable(self,path):
        try:
            path=self.disk.inside(path)
            if path!=self.disk.root:self.disk.editable(path)
            return path.is_dir()
        except (ValueError,OSError):return False
    def copy_items(self,paths,cut=False):
        if self.editable_paths(paths):self.context_clipboard=([Path(p) for p in paths],cut)
    def can_paste(self,target):
        value=getattr(self,'context_clipboard',None)
        return bool(value and self.folder_writable(target) and self.editable_paths(value[0]) and all(p.exists() for p in value[0]))
    def paste_items(self,target):
        if not self.can_paste(target):return
        paths,cut=self.context_clipboard
        if self.transfer_paths(paths,target,copy=not cut) and cut:self.context_clipboard=None
    def rename_item(self,path):
        name,ok=QInputDialog.getText(self,'Rename','New name:',text=path.name)
        if ok:self.operation(lambda:self.disk.rename(path,name))
    def new_text_file(self,folder):
        name,ok=QInputDialog.getText(self,'New Text Document','Name:',text='Untitled.txt')
        if not ok:return
        def create():
            destination=self.disk.inside(folder)
            if not self.folder_writable(destination):raise ValueError('This folder is read only.')
            path=self.disk.unused(destination/self.disk.valid_name(name))
            with path.open('x') as f:f.write('')
        self.operation(create)
    def file_context_menu(self,paths,folder,opener=None):
        paths=tuple(Path(p) for p in paths);folder=Path(folder);menu=QMenu(self);mutable=self.editable_paths(paths);writable=self.folder_writable(folder)
        def action(label,callback,enabled=True):
            a=menu.addAction(label,callback);a.setEnabled(enabled);return a
        if paths:
            action('Open',lambda:[(opener or self.open_item)(p) for p in paths])
            if len(paths)==1 and paths[0].is_dir() and not paths[0].name.endswith('.app'):action('Open in New Window',lambda:self.open_finder(paths[0]))
            menu.addSeparator()
            action('Cut',lambda:self.copy_items(paths,True),mutable);action('Copy',lambda:self.copy_items(paths),mutable)
            action('Copy Path' if len(paths)==1 else 'Copy Paths',lambda:QApplication.clipboard().setText('\n'.join(map(str,paths))))
            action('Paste',lambda:self.paste_items(folder),self.can_paste(folder));menu.addSeparator()
            action('Rename…',lambda:self.rename_item(paths[0]),mutable and len(paths)==1)
            action('Duplicate',lambda:[self.operation(lambda p=p:self.disk.duplicate(p)) for p in paths],mutable)
            action('Move to Trash',lambda:self.trash_paths(paths),mutable);menu.addSeparator()
            action('Properties / Get Info',lambda:[self.get_info(p) for p in paths])
        else:
            action('New Folder…',lambda:self.new_folder_at(folder),writable);action('New Text Document…',lambda:self.new_text_file(folder),writable)
            action('Paste',lambda:self.paste_items(folder),self.can_paste(folder));menu.addSeparator();action('Properties / Get Info',lambda:self.get_info(folder))
        return menu
    def new_folder_at(self,folder):
        name,ok=QInputDialog.getText(self,'New Folder','Name:',text='untitled folder')
        if ok:self.operation(lambda:self.disk.new_folder(folder,name))
    def fixed_icon_menu(self,button,title,callback,pos):
        if title in ('Install Macaque Classic','Terminal'):
            menu=QMenu(self);menu.addAction('Open…',callback)
        elif title=='Trash':
            menu=QMenu(self);menu.addAction('Open Trash',callback);a=menu.addAction('Empty Trash…',self.empty_trash);a.setEnabled(bool(self.disk.trash_items()))
        else:
            path=self.disk.root if title=='Macaque HD' else self.disk.root/title
            menu=self.file_context_menu([path],path if path.is_dir() else path.parent)
        menu.exec(button.mapToGlobal(pos))
