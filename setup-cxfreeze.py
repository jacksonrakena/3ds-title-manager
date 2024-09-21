import sys

from cx_Freeze import Executable, setup

if sys.platform == 'win32':
    executables = [
        Executable('main.py', target_name='titlemanager', base='Win32GUI'),
    ]
else:
    executables = [
        Executable('main.py', target_name='titlemanager'),
    ]

setup(
    name="Jackson's 3DS Title Manager",
    version="3.0",
    description="Easily download, update, and manage games on your 3DS SD card",
    executables=executables
)
