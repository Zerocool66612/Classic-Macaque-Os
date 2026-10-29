#!/usr/bin/python3
"""Executed by Calamares inside the installed target, before DM configuration."""
import sys
from pathlib import Path

def configure(root):
    root=Path(root)
    # Remove only our live autologin and Debian Live's temporary sudo policy.
    for name in ['etc/macaque-live','etc/lightdm/lightdm.conf.d/50-macaque.conf','etc/sudoers.d/live','etc/sudoers.d/live-config']:
        p=root/name
        if p.is_file() or p.is_symlink():p.unlink()
    main=root/'etc/lightdm/lightdm.conf'
    if main.is_file():
        main.write_text(''.join(line for line in main.read_text().splitlines(keepends=True) if not line.lstrip().startswith(('autologin-user=', 'autologin-user-timeout=', 'autologin-session='))))
    dest=root/'etc/lightdm/lightdm.conf.d/60-macaque-installed.conf';dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text('[Seat:*]\nuser-session=macaque\n')
if __name__=='__main__':
    if sys.argv[1:]!=['--calamares-target']:raise SystemExit('Only intended for the Calamares target chroot.')
    configure('/')
