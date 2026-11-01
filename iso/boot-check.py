#!/usr/bin/python3
"""Boot the actual ISO in a disposable, diskless QEMU BIOS VM.
Reaching the live-account marker verifies initramfs -> systemd -> live setup.
It does not certify Wayland, UEFI firmware, USB hardware or installation.
"""
import argparse,json,os,subprocess,time
from pathlib import Path
MARKER=b'MACAQUE_LIVE_USER_READY_V1'
def command(iso,log):
 return ['qemu-system-x86_64','-machine','pc','-accel','tcg','-m','2048','-smp','2','-boot','order=d,menu=off','-cdrom',str(Path(iso).resolve()),'-display','none','-serial','file:'+str(Path(log).resolve()),'-monitor','none','-nic','none','-no-reboot']
def reached(log):
 try:return MARKER in Path(log).read_bytes()
 except FileNotFoundError:return False
def check(iso,log,timeout=300):
 iso=Path(iso);log=Path(log)
 if not iso.is_file():raise ValueError('ISO is missing.')
 log.parent.mkdir(parents=True,exist_ok=True);log.write_bytes(b'')
 with log.with_suffix('.qemu.log').open('wb') as errors:
  process=subprocess.Popen(command(iso,log),stdout=errors,stderr=subprocess.STDOUT)
  try:
   deadline=time.monotonic()+timeout
   while time.monotonic()<deadline:
    if reached(log):return True
    if process.poll() is not None:return False
    time.sleep(.5)
   return False
  finally:
   if process.poll() is None:
    process.terminate()
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:process.kill();process.wait()
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('iso');parser.add_argument('log');args=parser.parse_args()
 ok=check(args.iso,args.log)
 Path(args.log+'.result.json').write_text(json.dumps({'bios_live_userspace_reached':ok,'wayland_tested':False,'uefi_tested':False,'physical_usb_tested':False},indent=2)+'\n')
 if not ok:raise SystemExit('ISO boot check failed or timed out. Keep boot-check.log and boot-check.qemu.log; do not flash this candidate.')
 print('ISO BIOS boot check passed: kernel, live filesystem and live user setup reached. Graphics/UEFI/hardware are not covered.')
