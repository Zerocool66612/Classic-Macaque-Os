"""Exercise package caching, failure receipts, privileged install guards and recovery."""
import os,tempfile,subprocess,json,types
from pathlib import Path
from unittest.mock import Mock,patch
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['MACAQUE_SILENT']='1'
from PySide6.QtWidgets import QApplication,QMessageBox
import maintenance,update_store,recovery_mode
from update_backend import releases,PREFIX
from update_panel import Updates
app=QApplication([])
def package(folder,version):
 root=folder/('src-'+version);(root/'DEBIAN').mkdir(parents=True)
 (root/'DEBIAN/control').write_text('Package: macaque-classic\nVersion: '+version+'\nArchitecture: amd64\nMaintainer: Test <test@example.org>\nDescription: test fixture\n')
 dest=folder/('macaque-classic_'+version+'_amd64.deb');subprocess.run(['dpkg-deb','--build',str(root),str(dest)],check=True,capture_output=True);return dest
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp);old=package(root,'0.40.1');new=package(root,'0.41');store=root/'cache';version={'value':'0.40.1'}
 # Isolate the simulated installed-system fixture from the ISO chroot live marker.
 real_exists=Path.exists
 with patch.object(Path,'exists',autospec=True,side_effect=lambda p:False if p==Path('/etc/macaque-live') else real_exists(p)),patch.object(update_store,'STORE',store),patch.object(update_store,'installed_version',side_effect=lambda:version['value']):
  saved=update_store.cache_package(old);assert maintenance.digest(saved)==maintenance.digest(old)
  assert not update_store.status()['packages'][0]['rollback']
  realrun=subprocess.run;calls=[]
  def run(args,**kwargs):
   if args[0]=='/usr/bin/apt-get':
    calls.append(args);version['value']=maintenance.metadata(args[-1])['version'];return types.SimpleNamespace(returncode=0)
   return realrun(args,**kwargs)
  with patch.object(maintenance.os,'geteuid',return_value=0),patch.object(maintenance,'installed_target',return_value=True),patch.object(maintenance.subprocess,'run',side_effect=run):
   maintenance.main(['install-desktop',str(new),maintenance.digest(new)])
   status=update_store.status();assert len(status['packages'])==2 and status['history'][-1]['result']=='installed'
   previous=next(x for x in status['packages'] if x['rollback']);assert previous['version']=='0.40.1'
   maintenance.main(['rollback-desktop',previous['path'],previous['sha256']]);assert '--allow-downgrades' in calls[-1] and version['value']=='0.40.1'
   count=len(calls)
   try:maintenance.main(['install-desktop',str(new),'0'*64])
   except ValueError:pass
   else:raise AssertionError('Changed package accepted')
   assert len(calls)==count
   try:maintenance.main(['rollback-desktop',str(old),maintenance.digest(old)])
   except ValueError:pass
   else:raise AssertionError('Uncached rollback accepted')
  def fail(args,**kwargs):
   if args[0]=='/usr/bin/apt-get':raise subprocess.CalledProcessError(1,args)
   return realrun(args,**kwargs)
  with patch.object(maintenance.os,'geteuid',return_value=0),patch.object(maintenance,'installed_target',return_value=True),patch.object(maintenance.subprocess,'run',side_effect=fail):
   try:maintenance.main(['install-desktop',str(new),maintenance.digest(new)])
   except subprocess.CalledProcessError:pass
   else:raise AssertionError('APT failure ignored')
  assert update_store.status()['history'][-1]['result']=='failed or cancelled'
 # One-login recovery requests are consumed, and cancelling leaves normal startup.
 recovery_mode.schedule(folder=root);env={};assert recovery_mode.consume(env,root) and env['MACAQUE_SAFE_SESSION']=='1'
 assert not recovery_mode.consume({},root)
 recovery_mode.schedule(folder=root);recovery_mode.schedule(False,root);assert not recovery_mode.consume({},root)
 # Recovery does not mutate persistent startup preferences.
 from desktop import Desktop
 d=types.SimpleNamespace(arrange_icons=Mock(),update_icon_visibility=Mock(),sound_theme=types.SimpleNamespace(suspended=True),launch=Mock(),state={'startup_apps':['Teapot Studio']})
 before=json.dumps(d.state)
 with patch.dict(os.environ,MACAQUE_SAFE_SESSION='1'):Desktop.initial(d)
 d.launch.assert_called_once_with('Recovery & Diagnostics');assert json.dumps(d.state)==before
 # Notes are plain text, and rollback still requires an explicit user confirmation.
 panel=Updates(Mock());panel.history_loaded({'installed_version':'0.41','packages':[{'version':'0.40.1','path':str(saved),'sha256':'a'*64,'rollback':True}],'history':[]})
 with patch.object(panel,'native_installed',return_value=True),patch.object(panel,'terminal') as terminal,patch('update_panel.classic_question',return_value=QMessageBox.No):panel.rollback();terminal.assert_not_called()
 with patch.object(panel,'native_installed',return_value=True),patch.object(panel,'terminal') as terminal,patch('update_panel.classic_question',return_value=QMessageBox.Yes):panel.rollback();assert terminal.call_args.args[1][-3]=='rollback-desktop'
 # Downloaded newer package must open themed confirmation and launch installer.
 with patch.object(panel,'native_installed',return_value=True),patch.object(panel,'terminal') as terminal,patch('update_panel.classic_question',return_value=QMessageBox.Yes) as confirm:
  panel.offer_install({'version':'99.0.0','path':'/tmp/new.deb','sha256':'b'*64})
  confirm.assert_called_once()
  assert confirm.call_args.args[-1]==QMessageBox.No
  assert terminal.call_args.args[1][-3:]==['install-desktop','/tmp/new.deb','b'*64]
 with patch.object(panel,'native_installed',return_value=True),patch.object(panel,'terminal') as terminal,patch('update_panel.classic_question',return_value=QMessageBox.No):
  panel.offer_install({'version':'99.0.0','path':'/tmp/new.deb','sha256':'b'*64})
  terminal.assert_not_called()
 panel.releases.clear()
 with patch.object(panel,'check') as refresh:
  panel.download();refresh.assert_called_once()
 assert 'Checking for available desktop updates' in panel.status.text()
 with patch('update_store.installed_version',return_value='0.40.1'),patch.object(panel,'native_installed',return_value=True),patch.object(panel,'terminal') as terminal,patch('update_panel.classic_question',return_value=QMessageBox.Yes):
  panel.offer_install({'version':'0.42.13','path':'/tmp/new.deb','sha256':'b'*64})
  terminal.assert_called_once()
 panel.checked({'releases':[{'version':'0.41','tag':'test','prerelease':True,'notes':'<script>plain text</script>'}]});assert panel.notes.toPlainText()=='<script>plain text</script>'
 panel.deleteLater();app.processEvents()
print('PASS: real .deb cache/hash/metadata, install and rollback command guards (APT mocked), failure receipts, consent, release notes, one-login recovery and unchanged preferences.')
