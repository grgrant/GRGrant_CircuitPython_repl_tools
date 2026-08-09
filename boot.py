# SPDX-FileCopyrightText: Copyright (c) 2026 Bob Grant for grgrant
#
# SPDX-License-Identifier: MIT

"""
boot.py -- implements switching R/O R/W CircuitPython and saves state
"""
VERSION = 0.7
DEBUG = False
DISPLAY_ROTATION = 0

import sys
import board
import storage
import supervisor

sys.path.append('/bin') # Add a user directory for imports

DISABLE_CIRCUITPY = False
SUPERVISOR_AUTORELOAD = False

print(f"boot.py V{VERSION}")

# Check if NVM exists and is a decent size
try:
    from microcontroller import nvm
    HAVE_NVM = len(nvm) > 512
except:
    HAVE_NVM = False

if HAVE_NVM:
    try:
        import nvmflags as nf
        DISABLE_CIRCUITPY = nf.is_set(nvm, nf.DISABLE_CIRCUITPY)
        SUPERVISOR_AUTORELOAD = nf.is_set(nvm, nf.SUPERVISOR_AUTORELOAD)
    except ImportError:
        print("nvmflags not found -- using defaults")

if DEBUG:
    print("DISABLE_CIRCUITPY", DISABLE_CIRCUITPY,
          "SUPERVISOR_AUTORELOAD", SUPERVISOR_AUTORELOAD)

# Not all systems support usb drive
if hasattr(storage, 'disable_usb_drive'):
    if DISABLE_CIRCUITPY:
        storage.disable_usb_drive()
    else:
        storage.enable_usb_drive()
supervisor.runtime.autoreload = SUPERVISOR_AUTORELOAD

# Fail board rotation gracefully if not exists
if hasattr(board, 'DISPLAY') and hasattr(board.DISPLAY, 'rotation'):
    board.DISPLAY.rotation = DISPLAY_ROTATION
