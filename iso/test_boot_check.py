"""Test boot gating without claiming a real ISO was booted."""
import importlib.util,tempfile
from pathlib import Path
from unittest.mock import patch,Mock
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('bootcheck',ROOT/'iso/boot-check.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as temp:
 r=Path(temp);image=r/'test.iso';image.write_bytes(b'fixture');log=r/'boot.log'
 args=m.command(image,log)
 assert args[args.index('-accel')+1]=='tcg' and '-nic' in args and '-no-reboot' in args
 assert not any(x in args for x in ('-hda','-hdb','-drive','-enable-kvm'))
 assert not m.reached(log);log.write_bytes(b'Loading /live/initrd.img...');assert not m.reached(log)
 log.write_bytes(b'prefix\n'+m.MARKER+b'\n');assert m.reached(log)
 process=Mock();process.poll.return_value=None
 def start(*a,**kw):log.write_bytes(m.MARKER);return process
 with patch.object(m.subprocess,'Popen',side_effect=start):assert m.check(image,log,1)
 process.terminate.assert_called_once()
 process=Mock();process.poll.return_value=1
 with patch.object(m.subprocess,'Popen',return_value=process):assert not m.check(image,log,1)
 assert not m.reached(log) # Old successful marker was cleared.
 process=Mock();process.poll.return_value=None
 with patch.object(m.subprocess,'Popen',return_value=process):assert not m.check(image,log,0)
 process.terminate.assert_called_once()
print('Diskless boot command, marker/failure/timeout gates and stale-log rejection passed (QEMU mocked).')
