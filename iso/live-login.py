#!/usr/bin/python3
"""Initialize credentials only in the disposable live boot, never an installed OS."""
import os,pwd,subprocess
from pathlib import Path

def prepare(root='/',run=subprocess.run,lookup=pwd.getpwnam):
    root=Path(root)
    if not (root/'etc/macaque-live').is_file() or 'boot=live' not in (root/'proc/cmdline').read_text().split():raise ValueError('Live boot only; refusing account changes.')
    try:user=lookup('macaque')
    except KeyError:
        run(['useradd','--create-home','--shell','/bin/bash','macaque'],check=True);user=lookup('macaque')
    if user.pw_uid<1000 or user.pw_dir!='/home/macaque':raise ValueError('Unexpected live account; refusing changes.')
    run(['chpasswd'],input='macaque:live\n',text=True,check=True)
    run(['usermod','--append','--groups','sudo','macaque'],check=True)
if __name__=='__main__':
    if os.geteuid()!=0:raise SystemExit('Live account setup requires root.')
    prepare()
