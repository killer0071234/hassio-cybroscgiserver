#!/usr/bin/env python3
import os
import runpy
import sys
import urllib.error
import urllib.request
from pathlib import Path

import psutil

SCGI_PORT = 4000
MODULE_NAME = 'scgi_server'


def server_running():
    try:
        with urllib.request.urlopen("http://localhost:" + str(SCGI_PORT) + "/?sys.scgi_status", timeout=0.5) as response:
            return 'active' in response.read().decode()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return False


def kill_process(name):
    for proc in psutil.process_iter(['pid', 'cmdline']):
        cmdline = proc.info['cmdline']
        if cmdline and any(name in arg for arg in cmdline):
            if proc.info['pid'] not in {os.getpid(), os.getppid()}: # don't kill yourself
                # print(f"Killing process with PID: {proc.info['pid']} {cmdline}")
                proc.kill()


if __name__ == '__main__' and not server_running():
    kill_process(MODULE_NAME)
    # print(f"Starting process with PID: {os.getpid()}")
    sys.path.append(str(Path(__file__).parent.parent.resolve()))
    runpy.run_module(MODULE_NAME, run_name='__main__')
