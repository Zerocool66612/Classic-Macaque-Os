#!/usr/bin/python3
"""Executed by Calamares inside the installed target, before DM configuration."""
import sys
from pathlib import Path

def configure(root):
    root=Path(root)
    # Remove only our live autologin and Debian Live's temporary sudo policy.
    for name in ['etc/macaque-live','etc/systemd/system/greetd.service.d/50-macaque-live.conf','etc/systemd/system/getty@tty2.service.d/50-macaque-live.conf','etc/systemd/system/getty.target.wants/getty@tty2.service','etc/systemd/system/macaque-live-login.service','usr/local/libexec/macaque-live-login','etc/lightdm/lightdm.conf.d/50-macaque.conf','etc/sudoers.d/live','etc/sudoers.d/live-config']:
        p=root/name
        if p.is_file() or p.is_symlink():p.unlink()
    marker=root/'etc/macaque-installed';marker.parent.mkdir(parents=True,exist_ok=True);marker.write_text('Macaque installed target\n')
    config=root/'etc/greetd/config.toml'
    if config.exists():config.write_text(config.read_text().split('[initial_session]')[0])
    unit=root/'etc/systemd/system/display-manager.service'
    unit.parent.mkdir(parents=True,exist_ok=True)
    if unit.is_symlink() or unit.exists():unit.unlink()
    unit.symlink_to('/usr/lib/systemd/system/greetd.service')
if __name__=='__main__':
    if sys.argv[1:]!=['--calamares-target']:raise SystemExit('Only intended for the Calamares target chroot.')
    configure('/')
