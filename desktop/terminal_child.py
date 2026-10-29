#!/usr/bin/env python3
"""Become the controlling process of the supplied PTY, then execute bash."""
import fcntl,os,termios
fcntl.ioctl(0,termios.TIOCSCTTY,0)
os.execvpe('/bin/bash',['bash','--login'],os.environ)
