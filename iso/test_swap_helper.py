import importlib.util,copy,stat
from pathlib import Path
from unittest.mock import patch,Mock
spec=importlib.util.spec_from_file_location('swap_helper',Path(__file__).with_name('swap-helper.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def partition(name,parent):return dict(name=name,type='part',pkname=parent)
def disk(name,id,children):return {'name':name,'type':'disk','maj:min':id,'ro':False,'children':children}
data={'disks':[disk('/dev/sda','8:0',[partition('/dev/sda1','/dev/sda')]),disk('/dev/sdb','8:16',[partition('/dev/sdb2','/dev/sdb')]),disk('/dev/sdc','8:32',[partition('/dev/sdc1','/dev/sdc')])],'swaps':[{'name':'/dev/sdb2','type':'partition'},{'name':'/dev/sdc1','type':'partition'},{'name':'/swapfile','type':'file'},{'name':'/dev/mapper/cryptswap','type':'partition'}],'live_source':'/dev/sda1'}
assert m.plan(data,'/dev/sdb','8:16')==['/dev/sdb2']
for target,id in [('/dev/sda','8:0'),('/dev/sdb','8:17'),('/dev/sdb2','8:16')]:
 try:m.plan(data,target,id)
 except ValueError:pass
 else:raise AssertionError('Unsafe selection accepted')
invalid=copy.deepcopy(data);invalid['live_source']='overlay'
try:m.plan(invalid,'/dev/sdb','8:16')
except ValueError:pass
else:raise AssertionError('Unidentified live media accepted')
state=copy.deepcopy(data);commands=[]
def run(args):
 commands.append(args);state['swaps']=[s for s in state['swaps'] if s['name']!=args[-1]];return ''
with patch.object(m.os,'geteuid',return_value=0),patch.object(m.Path,'is_file',return_value=True),patch.object(m.Path,'read_text',return_value='boot=live components'),patch.object(m.os,'stat',return_value=Mock(st_mode=stat.S_IFBLK)):
 assert 'Released /dev/sdb2' in m.release('/dev/sdb','8:16',lambda:state,run)
 assert commands==[['/usr/sbin/swapoff','--','/dev/sdb2']]
 assert len(state['swaps'])==3
 commands.clear();m.release('/dev/sdb','8:16',lambda:state,run);assert not commands
 def fail(args):raise ValueError('Cannot allocate memory')
 try:m.release('/dev/sdb','8:16',lambda:data,fail)
 except ValueError as e:assert 'Cannot allocate memory' in str(e)
 else:raise AssertionError('Failure ignored')
print('Swap selection, boot-device protection, targeted release and failure checks passed (mocked only).')
