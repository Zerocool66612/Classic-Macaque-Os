"""Verify About This Computer uses current machine values, not target hardware."""
import os
from unittest.mock import patch
from pathlib import Path
from classic_utilities import local_hardware
cpu='processor : 0\nmodel name : Example Test CPU 9000\n'
mem='MemTotal:       8388608 kB\n'
real_read=Path.read_text
def read(path,*args,**kwargs):
    if str(path)=='/proc/cpuinfo':return cpu
    if str(path)=='/proc/meminfo':return mem
    return real_read(path,*args,**kwargs)
with patch.object(Path,'read_text',autospec=True,side_effect=read),patch('classic_utilities.safe_command',return_value='00:02.0 VGA compatible controller: Example Graphics 1234'):
    data=local_hardware()
    assert data['processor']=='Example Test CPU 9000',data
    assert data['graphics']=='Example Graphics 1234',data
    assert data['memory']=='8.0 GiB',data
    assert data['architecture']
print('PASS: About hardware follows current CPU, GPU and memory')
