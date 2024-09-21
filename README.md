[![License](https://img.shields.io/badge/License-MIT-blue.svg)]() ![Releases](https://img.shields.io/github/downloads/ihaveamac/custom-install/total.svg)

# Jackson's 3DS Title Manager
*The authors of this program do not condone piracy. This program is intended to be used with legitimate copies of games and software.*
![alt text](image-3.png)

A fork of [ihaveamac's custom-install](https://github.com/ihaveamac/custom-install) that allows users to download and install titles directly from [HShop](https://hshop.erista.me/) to their Nintendo 3DS system's SD card.

It features the following improvements over the original `custom-install` program:
- Allows users to search and download titles directly from HShop, including the automatic detection and download of Downloadable Content (DLC) and title updates.
![alt text](image-1.png)

- The user can then, with one click, install these downloaded titles directly to their SD card, bypassing the need to use a program like FBI to install the CIA file.
![alt text](image-2.png)

- Includes a feature allowing users to quickly download all available updates and DLC packs for all the games installed on their SD card, that are not already installed.
![alt text](image.png)

### Feature roadmap
- [x] Query, download, and install from HShop
- [x] Auto-update all installed titles + install available DLC
- [ ] Delete, move, edit titles on SD card

## Summary
You're gonna need a copy of [seeddb.bin](https://github.com/ihaveamac/3DS-rom-tools/wiki/SeedDB-list), and your [boot9.bin and movable.sed files](https://ihaveamac.github.io/dump.html), regardless of installation method.

1. Download a copy of 3DS Title Manager from the 

### Windows standalone
1. [Dump boot9.bin and movable.sed](https://ihaveamac.github.io/dump.html) from a 3DS system.
2. Download the [latest releases](https://github.com/ihaveamac/custom-install/releases).
3. Extract and run ci-gui. Read `windows-quickstart.txt`.

### With installed Python
Note for Windows users: Enabling "Add Python 3.X to PATH" is **NOT** required! Python is installed with the `py` launcher by default.



1. [Dump boot9.bin and movable.sed](https://ihaveamac.github.io/dump.html) from a 3DS system.
2. Download the repo ([zip link](https://github.com/ihaveamac/custom-install/archive/safe-install.zip) or `git clone`)
3. Install the packages:
  * Windows: Double-click `windows-install-dependencies.py`
    * Alternate manual method: `py -3 -m pip install --user -r requirements-win32.txt`
  * macOS/Linux: `python3 -m pip install --user -r requirements.txt`
4. Run `custominstall.py` with boot9.bin, movable.sed, path to the SD root, and CIA files to install (see Usage section).
5. Download and use [custom-install-finalize](https://github.com/ihaveamac/custom-install/releases) on the 3DS system to finish the install.

## Setup
Linux users must build [wwylele/save3ds](https://github.com/wwylele/save3ds) and place `save3ds_fuse` in `bin/linux`. Install [rust using rustup](https://www.rust-lang.org/tools/install), then compile with: `cargo build --release --no-default-features`. The compiled binary is located in `target/release/save3ds_fuse`, copy it to `bin/linux`.

movable.sed is required and can be provided with `-m` or `--movable`.

boot9 is needed:
* `-b` or `--boot9` argument (if set)
* `BOOT9_PATH` environment variable (if set)
* `%APPDATA%\3ds\boot9.bin` (Windows-specific)
* `~/Library/Application Support/3ds/boot9.bin` (macOS-specific)
* `~/.3ds/boot9.bin`
* `~/3ds/boot9.bin`

A [SeedDB](https://github.com/ihaveamac/3DS-rom-tools/wiki/SeedDB-list) is needed for newer games (2015+) that use seeds.  
SeedDB is checked in order of:
* `-s` or `--seeddb` argument (if set)
* `SEEDDB_PATH` environment variable (if set)
* `%APPDATA%\3ds\seeddb.bin` (Windows-specific)
* `~/Library/Application Support/3ds/seeddb.bin` (macOS-specific)
* `~/.3ds/seeddb.bin`
* `~/3ds/seeddb.bin`

## custom-install-finalize
custom-install-finalize installs a ticket, plus a seed if required. This is required for the title to appear and function.

This can be built as most 3DS homebrew projects [with devkitARM](https://www.3dbrew.org/wiki/Setting_up_Development_Environment).

## Usage
Use `-h` to view arguments.

Examples:
```
py -3 custominstall.py -b boot9.bin -m movable.sed --sd E:\ file.cia file2.cia
python3 custominstall.py -b boot9.bin -m movable.sed --sd /Volumes/GM9SD file.cia file2.cia
python3 custominstall.py -b boot9.bin -m movable.sed --sd /media/GM9SD file.cia file2.cia
```

## GUI
A GUI is provided to make the process easier.

### GUI Setup
Linux users may need to install a Tk package:
- Ubuntu/Debian: `sudo apt install python3-tk`
- Manjaro/Arch: `sudo pacman -S tk`

Install the requirements listed in "Summary", then run `ci-gui.py`.

## Development

### Building Windows standalone

Using a 32-bit version of Python is recommended to build a version to be distributed.

A [virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment) is recommended to isolate the packages from system directories. The build script `make-standalone.bat` assumes that the dependencies are in PATH.

Install the dependencies, plus cx-Freeze. In a virtual environment, the specific Python version doesn't need to be requested.
```batch
pip install cx-freeze -r requirements-win32.txt
```

Copy `custom-install-finalize.3dsx` to the project root, this will be copied to the build directory and included in the final archive.

Run `make-standalone.bat`. This will run cxfreeze and make a standalone version at `dist\custom-install-standalone.zip`

## License/Credits
The original `custom-install`, which does most of the legwork for this program, is &copy; 2019-2021 Ian Burgwin under the MIT License.

[save3ds by wwylele](https://github.com/wwylele/save3ds) is used to interact with the Title Database (details in `bin/README`).

Thanks to @nek0bit for redesigning `custominstall.py` to work as a module, and for implementing an earlier GUI.

Thanks to @LyfeOnEdge from the [brewtools Discord](https://brewtools.dev) for designing the second version of the GUI. Special thanks to CrafterPika and archbox for testing.

Thanks to @BpyH64 for [researching how to generate the cmacs](https://github.com/d0k3/GodMode9/issues/340#issuecomment-487916606).

Remaining code and contributions &copy; 2024 Jackson Rakena under the MIT License.