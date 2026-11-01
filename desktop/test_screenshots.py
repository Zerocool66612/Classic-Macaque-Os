"""Screenshot file lifecycle and native command boundaries, without screen access."""
import os,tempfile,subprocess,types,unittest
from pathlib import Path
from unittest.mock import patch
import screenshot_backend as b
PNG=b'\x89PNG\r\n\x1a\nfixture'
class Checks(unittest.TestCase):
 def test_region_capture_no_shell_and_no_overwrite(self):
  with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'MACAQUE_WAYLAND_SESSION':'1','WAYLAND_DISPLAY':'fixture'}):
   old=Path(temp)/'existing.png';old.write_bytes(b'keep');commands=[]
   def run(args,**kw):
    commands.append(args)
    if args[0]=='slurp':return types.SimpleNamespace(returncode=0,stdout='-20,30 400x300\n')
    kw['stdout'].write(PNG);return types.SimpleNamespace(returncode=0)
   with patch.object(b.subprocess,'run',side_effect=run):
    first=b.capture({'directory':temp,'region':True,'cursor':True});second=b.capture({'directory':temp})
   self.assertNotEqual(first['path'],second['path']);self.assertEqual(old.read_bytes(),b'keep');self.assertEqual(Path(first['path']).read_bytes(),PNG)
   self.assertEqual(commands[1],['grim','-t','png','-c','-g','-20,30 400x300','-'])
   self.assertEqual(Path(first['path']).stat().st_mode&0o777,0o600)
 def test_cancel_and_failure_cleanup(self):
  with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'MACAQUE_WAYLAND_SESSION':'1','WAYLAND_DISPLAY':'fixture'}):
   with patch.object(b.subprocess,'run',return_value=types.SimpleNamespace(returncode=1,stdout='')):self.assertEqual(b.capture({'directory':temp,'region':True}),{'cancelled':True})
   self.assertEqual(list(Path(temp).iterdir()),[])
   with patch.object(b.subprocess,'run',side_effect=subprocess.CalledProcessError(1,['grim'])):
    with self.assertRaises(subprocess.CalledProcessError):b.capture({'directory':temp})
   self.assertEqual(list(Path(temp).iterdir()),[])
 def test_invalid_region_and_session(self):
  with patch.dict(os.environ,{'MACAQUE_WAYLAND_SESSION':'0'}):
   with self.assertRaises(ValueError):b.capture({})
  with patch.dict(os.environ,{'MACAQUE_WAYLAND_SESSION':'1','WAYLAND_DISPLAY':'fixture'}),patch.object(b.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout='; touch /tmp/no')):
   with self.assertRaises(ValueError):b.capture({'region':True})
if __name__=='__main__':unittest.main()
