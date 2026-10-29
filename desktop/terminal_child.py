#!/usr/bin/env python3
"""Become the controlling process of the supplied PTY, then execute bash."""
import fcntl,os,termios,sys
fcntl.ioctl(0,termios.TIOCSCTTY,0)
command=sys.argv[1:] or ['/bin/bash','--login']
os.execvpe(command[0],command,os.environ)
