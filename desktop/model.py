"""Persistent desktop preferences and a managed, reversible classic disk."""
import ast,json,math,operator,os,shutil,uuid
from pathlib import Path

CONTROL_PANELS=['Appearance','Date & Time','Memory','Desktop Disk','Sound & Devices','Screen Saver']
APP_NAMES=['Macaque Text','Macaque Notes','Calculator','Macaque Search','Macaque Tiles','Macaque Clips','Date & Time','Appearance','Help Center','Macaque Files','Network','Sound','Display','Storage','System Monitor','GIMP','Audacity','OBS Studio','Chess','Macaque Paint','Tasks','Clockwork','Media Player','Archive Viewer','Character Map','Teapot Studio','Wallpapers','Mouse','Settings','Notifications','Classic Sounds','Backup & Recovery','Classic Mac Apps','Flatpak Apps','Downloads','Macaque Web','Workspaces','Welcome Center','Terminal']
class Disk:
    def __init__(self,base):
        self.base=Path(base).resolve();self.base.mkdir(parents=True,exist_ok=True);self.root=self.base/'Macaque HD';self.trash=self.base/'Trash';self.index=self.base/'trash.json';self.migrations=[]
        legacy=self.base/'Macintosh HD';migration_file=self.base/'disk-migration-0.6.json'
        try:mapping=json.loads(migration_file.read_text())
        except (OSError,ValueError):mapping={}
        if legacy.exists():
            destination=self.root if not self.root.exists() else self.unused(self.root/'Recovered previous disk')
            legacy.rename(destination);mapping[str(legacy)]=str(destination);self.write_json(migration_file,mapping)
        for old,new in mapping.items():
            destination=Path(new)
            if old==str(legacy) and destination.resolve().is_relative_to(self.root.resolve()):self.migrations.append((legacy,destination))
        for p in [self.root,self.trash,self.root/'Documents',self.root/'Desktop',self.root/'Downloads',self.root/'Pictures',self.root/'Applications',self.root/'System Folder'/'Control Panels']:p.mkdir(parents=True,exist_ok=True)
        welcome=self.root/'Documents'/'Welcome to Macaque.txt'
        if not (self.base/'.initialized').exists() and not welcome.exists():welcome.write_text('Welcome to Macaque Classic 0.24\n\nA classic desktop for your modern Linux computer.\n\nExplore the Macaque menu, open Applications, customize Appearance,\nand try your actual Classic Control Strip 2.0.6.\n\nFiles on Macaque HD are stored in your application data directory.\nThis desktop is an application, not a bootable operating system yet.\n')
        aliases={'SimpleText':'Macaque Text','Finder':'Macaque Files','Sherlock':'Macaque Search','Stickies':'Macaque Notes','Puzzle':'Macaque Tiles','Scrapbook':'Macaque Clips'}
        for folder in [self.root/'Applications',self.root/'System Folder'/'Control Panels']:
            for old,new in aliases.items():
                before,after=folder/(old+'.app'),folder/(new+'.app')
                if before.is_dir() and not after.exists():before.rename(after)
        old_blender=self.root/'Applications'/'Blender.app'
        if old_blender.is_dir() and not any(old_blender.iterdir()):old_blender.rmdir()
        for name in APP_NAMES:
            p=self.root/'Applications'/(name+'.app');p.mkdir(exist_ok=True)
        for name in CONTROL_PANELS:(self.root/'System Folder'/'Control Panels'/(name+'.app')).mkdir(exist_ok=True)
        if not self.index.exists():self.write_json(self.index,{})
        (self.base/'.initialized').touch()
        self.protected={self.root,self.root/'Applications',self.root/'System Folder',self.root/'System Folder'/'Control Panels'}
    def migrated_path(self,path):
        path=Path(path)
        for old,new in self.migrations:
            if path.is_relative_to(old):return str(new/path.relative_to(old))
        return str(path)
    @staticmethod
    def write_json(path,value):
        tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2));tmp.replace(path)
    def inside(self,p):
        p=Path(p).resolve()
        if not p.is_relative_to(self.root.resolve()):raise ValueError('This operation is limited to Macaque HD.')
        return p
    def editable(self,p):
        p=self.inside(p)
        if p in self.protected or (self.root/'Applications') in p.parents or (self.root/'System Folder') in p.parents:raise ValueError('This system item is protected.')
        return p
    @staticmethod
    def valid_name(name):
        if not name.strip() or name in ('.','..') or '/' in name or '\\' in name:raise ValueError('Choose a name without slashes.')
        return name.strip()
    @staticmethod
    def unused(p):
        original=p;i=2
        while p.exists():p=original.with_name(original.stem+f' {i}'+original.suffix);i+=1
        return p
    def new_folder(self,parent,name='untitled folder'):
        parent=self.inside(parent)
        if parent!=self.root:self.editable(parent)
        p=self.unused(parent/self.valid_name(name));p.mkdir();return p
    def rename(self,path,name):
        path=self.editable(path);target=path.with_name(self.valid_name(name))
        if target==path:return path
        if target.exists():raise ValueError('An item already has that name.')
        path.rename(target);return target
    def duplicate(self,path):
        path=self.editable(path);target=self.unused(path.with_name(path.stem+' copy'+path.suffix))
        if path.is_dir():shutil.copytree(path,target,symlinks=True)
        else:shutil.copy2(path,target,follow_symlinks=False)
        return target
    def copy_to(self,path,parent):
        path=self.inside(path);parent=self.inside(parent)
        if parent!=self.root:self.editable(parent)
        if path.is_dir() and (parent==path or parent.is_relative_to(path)):raise ValueError('A folder cannot be copied inside itself.')
        target=self.unused(parent/path.name)
        if path.is_dir():shutil.copytree(path,target,symlinks=True)
        else:shutil.copy2(path,target,follow_symlinks=False)
        return target
    def move_to(self,path,parent):
        path=self.editable(path);parent=self.inside(parent)
        if parent!=self.root:self.editable(parent)
        if not parent.is_dir():raise ValueError('Choose a destination folder.')
        if path.parent==parent:return path
        if path.is_dir() and (parent==path or parent.is_relative_to(path)):raise ValueError('A folder cannot be moved inside itself.')
        target=self.unused(parent/path.name);path.rename(target);return target
    def trash_item(self,path):
        path=self.editable(path);key=uuid.uuid4().hex;items=json.loads(self.index.read_text());items[key]={'name':path.name,'original':str(path.relative_to(self.root))}
        path.rename(self.trash/key)
        try:self.write_json(self.index,items)
        except Exception:(self.trash/key).rename(path);raise
        return key
    def trash_items(self):return json.loads(self.index.read_text())
    def restore(self,key):
        items=self.trash_items();info=items[key];target=self.inside(self.root/info['original']);target=self.unused(target);target.parent.mkdir(parents=True,exist_ok=True)
        (self.trash/key).rename(target);del items[key];self.write_json(self.index,items);return target
    def empty_trash(self):
        for p in self.trash.iterdir():
            if p.is_dir() and not p.is_symlink():shutil.rmtree(p)
            else:p.unlink()
        self.write_json(self.index,{})

OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Mod:operator.mod,ast.Pow:operator.pow}
FUNCTIONS={n:getattr(math,n) for n in ('sqrt','sin','cos','tan','log','log10','floor','ceil')}
def calculate(expression):
    if len(expression)>200:raise ValueError('Expression is too long.')
    tree=ast.parse(expression,mode='eval')
    if sum(1 for _ in ast.walk(tree))>80:raise ValueError('Expression is too complex.')
    def visit(node):
        if isinstance(node,ast.Expression):return visit(node.body)
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):value=node.value
        elif isinstance(node,ast.Name) and node.id in ('pi','e'):value=getattr(math,node.id)
        elif isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):value=visit(node.operand)*(1 if isinstance(node.op,ast.UAdd) else -1)
        elif isinstance(node,ast.BinOp) and type(node.op) in OPS:
            left,right=visit(node.left),visit(node.right)
            if isinstance(node.op,ast.Pow) and abs(right)>12:raise ValueError('Exponent must be between −12 and 12.')
            value=OPS[type(node.op)](left,right)
        elif isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in FUNCTIONS and len(node.args)==1 and not node.keywords:value=FUNCTIONS[node.func.id](visit(node.args[0]))
        else:raise ValueError('Use numbers, arithmetic, pi, e, or a supported math function.')
        if isinstance(value,complex) or not math.isfinite(value) or abs(value)>1e100:raise ValueError('Result is out of range.')
        return value
    return visit(tree)
