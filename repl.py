# SPDX-FileCopyrightText: Copyright (c) 2026 Bob Grant for grgrant
#
# SPDX-License-Identifier: MIT
"""
repl.py to setup certain things before entering repl
"""
__repo__ = "https://github.com/grgrant/CircuitPython_repl_utils.git"
VERSION = "0.9.1"
print("REPL init (repl.py)", VERSION)

import os
from time import localtime, sleep
import time
import storage
import microcontroller
from microcontroller import reset
import board
import sys
import gc

UNIXCMDS=True # This adds ls() cd() pwd() cat() at the expense of some REPL ram
DATETIMECMDS=True # Adds date(), clock() for time, datetime() cmds
TZ_OFFSET=None # Put your TZ Offset here (e.g. -5)
TZ_OFFSET=2

sys.path.append('/bin') # A place for .py utilities to run via import

# Check if NVM exists and is a decent size
try:
    from microcontroller import nvm
    _HAVE_NVM = len(nvm) > 512
except:
    _HAVE_NVM = False
if _HAVE_NVM:
    try:
        import nvmflags as _nf
        def read_nvm():
            _nf.flag_status(nvm)
    except:
        print("missing library nvmflags -- disabling NVM")
        _HAVE_NVM = False

_SETUP_RUN=False
def setup(verbose=False, **kwargs):
    # Setup some useful stuff
    global _SETUP_RUN
    if _SETUP_RUN: print("Setup previously ran")
    # WiFi setup
    if True: # not _SETUP_RUN:
        global wifi
        try:
            from wifi_connection import WiFiConnection
            kwargs.setdefault('tz_offset', TZ_OFFSET)
            wifi = WiFiConnection(verbose=verbose, **kwargs)
            wifi.connect()
            print("IP Address:",wifi.ip_address)
        except Exception as e:
            print("Unable to init wifi_connection:", e)
            wifi = None
    _SETUP_RUN=True

# Quick restart to uf2, bootloader or safemode
def uf2boot():
    microcontroller.on_next_reset(microcontroller.RunMode.UF2)
    print("Resetting to UF2 boot")
    sleep(2)
    microcontroller.reset()


def bootloader():
    microcontroller.on_next_reset(microcontroller.RunMode.BOOTLOADER)
    print("Resetting to Bootloader")
    sleep(2)
    microcontroller.reset()


def safemode():
    microcontroller.on_next_reset(microcontroller.RunMode.SAFE_MODE)
    print("Resetting to Safe Mode")
    sleep(2)
    microcontroller.reset()


# Switch between mounted CP Drive or writable via Web Workflow
def cpro():
    """Make R/O for CircuitPython, R/W for host editor (Mac/PyCharm)."""
    if _HAVE_NVM:
        if not _nf.is_set(nvm, _nf.DISABLE_CIRCUITPY):
            print("Already set to R/O -- skipping reset. Manually reset if necessary")
            return
        _nf.clear_flag(nvm, _nf.DISABLE_CIRCUITPY)
    else:
        os.rename('boot.py', 'boot_dis.py')
        storage.umount('/')
    sleep(2)
    microcontroller.reset()


def cprw():
    """Make R/W for CircuitPython."""
    if _HAVE_NVM:
        if _nf.is_set(nvm, _nf.DISABLE_CIRCUITPY):
            print("Already set to R/W -- skipping reset. Manually reset if necessary")
            return
        _nf.set_flag(nvm, _nf.DISABLE_CIRCUITPY)
    else:
        # Need user to eject CIRCUITPY for this to succeed
        remount_success = False
        while not remount_success:
            try:
                storage.remount('/', False)
                remount_success = True
            except:
                input("Please eject CIRCUITPY and then press enter")
        os.rename('boot_dis.py', 'boot.py')
        storage.umount('/')
    sleep(2)
    microcontroller.reset()


def autoreload(enable=None):
    """Toggle or explicitly set SUPERVISOR_AUTORELOAD.

    autoreload()       - toggle current state
    autoreload(True)   - enable
    autoreload(False)  - disable

    Takes effect immediately AND persists via NVM for next boot.
    """
    import supervisor

    if not _HAVE_NVM:
        if enable is None:
            enable = not supervisor.runtime.autoreload
        supervisor.runtime.autoreload = enable
        print(f"Autoreload {'enabled' if enable else 'disabled'} (session only, no NVM)")
        return

    if enable is None:
        # Toggle
        new_state = _nf.toggle_flag(nvm, _nf.SUPERVISOR_AUTORELOAD)
    elif enable:
        _nf.set_flag(nvm, _nf.SUPERVISOR_AUTORELOAD)
        new_state = True
    else:
        _nf.clear_flag(nvm, _nf.SUPERVISOR_AUTORELOAD)
        new_state = False

    supervisor.runtime.autoreload = new_state
    print(f"Autoreload {'enabled' if new_state else 'disabled'} (now and on next boot)")


def boardid():
    # What board are we running
    chip_id = microcontroller.cpu.uid.hex()
    print("\nAdafruit CircuitPython", os.uname().version)
    print(sys.implementation._machine)  # Pretty print of board name
    print(f"Board: {board.board_id}")
    print(f"Platform: {sys.platform}")
    print(f"Chip Family: {os.uname().sysname}")
    print(f"Chip UID: {chip_id}")

    try:
        import wifi
        wifi_available = True
    except:
        wifi_available = False

    if wifi_available and wifi.radio.connected:
        print(f"WiFi Connected SSID: {wifi.radio.ap_info.ssid} ",
              f"RSSI: {wifi.radio.ap_info.rssi}  ")
        print("IP:", wifi.radio.ipv4_address, "\n")
    elif wifi_available:
        print("WiFi not currently connected")
    else:
        print("Board doesn't support WiFi")

    # Free Memory in K or M autosize
    mem_size = round((gc.mem_free() + gc.mem_alloc()) / 1024, 1)
    mem_free = round(gc.mem_free() / 1024, 1)
    if mem_size < 1024:
        print("Free memory in KB", mem_free)
        print("Memory size (approx) in KB", mem_size, "\n")
    else:
        print("Free memory in MB", round(mem_free / 1024, 1))
        print("Memory size (approx) in MB", round(mem_size / 1024, 1), "\n")

    # Disk space
    fs_stat = os.statvfs('/')
    print("Disk size in MB", round(fs_stat[0] * fs_stat[2] / 1024 / 1024, 1))
    print("Free space in MB", round(fs_stat[0] * fs_stat[3] / 1024 / 1024, 1), "\n")

if UNIXCMDS:
    def cat(filename=None):
        if filename is None:
            print("Please provide a filename to cat.")
            return
        try:
            with open(filename,'r') as f:
                l = f.readline()
                while len(l):
                    print(l,end="")
                    l = f.readline()
                print("")
        except:
            print("Can't find or open:", filename)
        return

    def ls(directory=None, flags=None):
        import re
        ign_p1 = r"^\." # Ignore dot files
        cwd=os.getcwd()
        if directory is not None:
            try:
                os.chdir(directory)
            except:
                print("Unable to change to directory:",directory)
                return
        d = os.listdir()
        d = [f for f in d if not re.match(ign_p1, f)]
        for f in d:
            if os.stat(f)[0] & 0x4000: f+='/'
        # Do 2 column listing
        if len(d) % 2 != 0:
            d.append('')
        mid = len(d) // 2
        for i in range(mid):
            print(f"{d[i]:30.30s}  {d[mid+i]:30.30s}")
        try:
            os.chdir(cwd)
        except:
            pass
        return

    def cd(directory=None):
        if directory is None or directory == "":
            os.chdir("/")
        else:
            try:
                os.chdir(directory)
            except Exception as e:
                print("Unable to change to directory:", directory)
                return

    def pwd():
        print(os.getcwd())

if DATETIMECMDS:
    def date():
        lt = localtime()
        return f"{lt.tm_year}-{lt.tm_mon}-{lt.tm_mday}"

    def clock(): # Can't reuse imported time name
        lt=localtime()
        return f"{lt.tm_hour}:{lt.tm_min:02d}:{lt.tm_sec:02d}"

    def datetime():
        return date()+" "+clock()
