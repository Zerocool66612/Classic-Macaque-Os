#!/usr/bin/python3
"""Adapt Debian's packaged installer workflow; fail if expected steps change."""
from pathlib import Path
import yaml,shutil

def configure(root):
    root=Path(root);base=root/'etc/calamares';settings=base/'settings.conf'
    data=yaml.safe_load(settings.read_text());sequence=next(x['exec'] for x in data['sequence'] if 'exec' in x)
    assert all(n in sequence for n in ['users','displaymanager','bootloader','unpackfs','umount']), 'Unexpected Debian Calamares sequence'
    if 'shellprocess' not in sequence:sequence.insert(sequence.index('displaymanager'),'shellprocess')
    # Debian's helper downloads GRUB; use the cached packages in our target job.
    for online_job in ['bootloader-config','sources-media','sources-media-unmount','sources-final']:
        if online_job in sequence:sequence.remove(online_job)
    data['prompt-install']=True;data['branding']='macaque';settings.write_text(yaml.safe_dump(data,sort_keys=False))
    modules=base/'modules'
    (modules/'shellprocess.conf').write_text(yaml.safe_dump({'dontChroot':False,'timeout':300,'script':['/usr/bin/python3 /usr/local/libexec/macaque-installed-setup.py --calamares-target','/usr/bin/python3 /usr/local/libexec/macaque-offline-bootloader.py --calamares-target ${gs[firmwareType]}'],'i18n':{'name':'Configure Macaque login'}}))
    partition=modules/'partition.conf'
    options=yaml.safe_load(partition.read_text()) or {} if partition.exists() else {}
    options.update(userSwapChoices=['none','file'],initialSwapChoice='none')
    partition.write_text(yaml.safe_dump(options,sort_keys=False))
    dm=yaml.safe_load((modules/'displaymanager.conf').read_text());dm['displaymanagers']=['lightdm'];dm['defaultDesktopEnvironment']={'executable':'/usr/local/bin/macaque-session','desktopFile':'macaque'};(modules/'displaymanager.conf').write_text(yaml.safe_dump(dm))
    users=yaml.safe_load((modules/'users.conf').read_text());users['doAutologin']=False;(modules/'users.conf').write_text(yaml.safe_dump(users))
    welcome=yaml.safe_load((modules/'welcome.conf').read_text());welcome['requirements']['requiredStorage']=25;welcome['requirements']['requiredRam']=4.0;(modules/'welcome.conf').write_text(yaml.safe_dump(welcome))
    packages=yaml.safe_load((modules/'packages.conf').read_text());packages['update_db']=False;packages['skip_if_no_internet']=False;(modules/'packages.conf').write_text(yaml.safe_dump(packages))
    boot=yaml.safe_load((modules/'bootloader.conf').read_text());boot['efiBootloaderId']='debian';(modules/'bootloader.conf').write_text(yaml.safe_dump(boot))
    branding=base/'branding/macaque'
    if branding.exists():shutil.rmtree(branding)
    shutil.copytree(root/'usr/share/macaque-installer-branding',branding)
    desc=yaml.safe_load((branding/'branding.desc').read_text())
    assert desc['componentName']=='macaque' and desc['slideshow']=='show.qml'
    for name in desc['images'].values():assert (branding/name).is_file(),name
    assert (branding/desc['slideshow']).is_file()
if __name__=='__main__':configure('/')
