# circuitpython-repl-tools

A small toolkit for making CircuitPython boards pleasant to work with at the
REPL: a shared `boot.py`, a set of REPL convenience commands, **persistent
boot flags stored in NVM**, and a robust multi-network Wi-Fi connection helper.

These files are used across a fleet of ESP32-S3, ESP32-S2, and RP2040-based
boards. They're deliberately small, CLI-friendly, and self-contained — drop
them onto a board and go.

## Contents

| File                  | Role                                                                 |
|-----------------------|----------------------------------------------------------------------|
| `boot.py`             | Shared boot script. Reads NVM flags to set USB-drive read/write state, autoreload, and display rotation. |
| `repl.py`             | REPL convenience commands: board info, reboot modes, Unix-like `ls`/`cat`/`cd`, one-line Wi-Fi setup. |
| `nvmflags.py`         | Library. Stores persistent boot/REPL flags in the last 8 bytes of microcontroller NVM. |
| `example_settings.toml` | Template for `settings.toml`. Copy, fill in, and **do not commit** the real thing. |

## Requirements

- CircuitPython 9.x or later (developed on 10.x).  Unknown if 8.x works
- For NTP sync in `wifi_connection.py`: Install `adafruit_ntp` from the CircuitPython
  library bundle.
- A board with NVM (most ESP32/RP2040 boards) for the persistent-flag features.
  Boards without usable NVM fall back gracefully to session-only behavior.

## Install

Copy the files onto your `CIRCUITPY` drive:

```
CIRCUITPY/
├── boot.py
├── repl.py
└── lib/
    └── nvmflags.py         # shared library

```

`boot.py` and `repl.py` add `/bin` to `sys.path`, so personal libraries can
live there. `nvmflags.py` can live in `/lib` (or `/bin`).

## Quick start

### Board info

`boardid()`   Display board name, chip UID, Wi-Fi status, memory, disk


### Reboot into other modes

`uf2boot()`           # reboot into UF2 bootloader
`repl.bootloader()`   # reboot into ROM bootloader
`repl.safemode()`     # reboot into safe mode


## The NVM flag system

`nvmflags.py` stores a small block of flags in the last 8 bytes of NVM so
settings survive reboots and deep sleep. `boot.py` reads them early to decide
whether the USB drive is writable and whether autoreload is on.

Two flags ship by default:

- `DISABLE_CIRCUITPY` — when set, the board mounts its filesystem read-only to
  CircuitPython so a host editor (Mac/PyCharm) can write to it.
- `SUPERVISOR_AUTORELOAD` — persists the autoreload on/off state.

Toggle them from the REPL:


`cpro()`          # filesystem read-only to CP, writable from host editor
`cprw()`          # filesystem read/write to CP
`autoreload()`    # toggle autoreload (persists across reboots)
`read_nvm()`      # print current flag states


On boards without NVM, `cpro()`/`cprw()` fall back to renaming `boot.py`.



## Wi-Fi manager features

## Optional: Wi-Fi at the REPL

`setup()` uses the separate **wifi_connection** library if it's present.
`setup(True)` provides verbose logging of wifi connection and ntp time sync

Install it (and optionally `adafruit_ntp` for time sync):

    circup install adafruit_ntp
    curl -O https://raw.githubusercontent.com/grgrant/GRGrant_CircuitPython_wifi_connection/main/wifi_connection.py

Then copy `wifi_connection.py` into `CIRCUITPY/lib/`. Without it, every other
REPL command still works — you just won't get `setup()`'s Wi-Fi convenience or wifi_connection's default ntp
time sync.

See: https://github.com/grgrant/GRGrant_CircuitPython_wifi_connection
`wifi_connection.py` (`WiFiConnection`):

- Priority-based SSID selection from `settings.toml`, with optional
  scan-and-prefer-strongest-signal ordering.
- Three verification levels: connection only, gateway reachable, or full
  internet reachability (ping with HTTP fallback).
- Optional NTP time sync with a configurable resync interval.
- Verbose logging and an optional callback hook system.
- Configurable timeouts, retries, and radio TX power.

See the docstrings in the file for the full constructor argument list.

`setup(verbose=True)`      # connects Wi-Fi and syncs time
`print(wifi.ip_address)`

Or use the library directly:

```python
from wifi_connection import WiFiConnection

wifi = WiFiConnection(verbose=True, tz_offset=-7)
if wifi.connect():
    print("Connected to", wifi.connected_ssid, "IP:", wifi.ip_address)
```

`WiFiConnection` proxies unknown attributes to the built-in `wifi` module, so
you can generally use it as a drop-in stand-in for `wifi` (e.g. `wifi.radio`).

## Security notes

- **Never commit `settings.toml`** — it holds your Wi-Fi passwords and web
  workflow password. Only `example_settings.toml` belongs in the repo. The
  included `.gitignore` blocks it.
- Wi-Fi credentials are read only from `settings.toml`; none are stored in code.

## License

MIT. See individual file headers.
