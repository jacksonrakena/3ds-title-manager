import subprocess
import sys
from dataclasses import dataclass
from os import environ, scandir
from os.path import abspath, basename, dirname, isfile, join
from pprint import pformat
from sys import executable, platform
from tempfile import TemporaryDirectory
from typing import Literal

from pyctr.crypto import CryptoEngine, Keyslot, get_seed, load_seeddb
from pyctr.type.cdn import CDNError, CDNReader
from pyctr.type.cia import CIAError, CIAReader
from pyctr.type.ncch import NCCHSection
from pyctr.type.sd import SDFilesystem
from pyctr.type.smdh import AppTitle
from pyctr.type.tmd import TitleMetadataError
from pyctr.util import roundup

frozen = getattr(sys, 'frozen', None)
is_windows = sys.platform == 'win32'
script_dir: str
if frozen:
    script_dir = dirname(executable)
else:
    script_dir = dirname(__file__)
if platform == 'msys':
    platform = 'win32'

is_windows = platform == 'win32'


def get_app_title(title_id: str, fs: SDFilesystem):
    title = fs.open_title(title_id)
    # print(title.contents)
    if title.contents is None or 0 not in title.contents:
        return None
    if title.contents[0].exefs is None:
        return None
    if title.contents[0].exefs.icon is None:
        return None
    return title.contents[0].exefs.icon.get_app_title()


def get_sd_path(sd_path, crypto):
    sd_path = join(sd_path, 'Nintendo 3DS', crypto.id0.hex())
    id1s = []
    for d in scandir(sd_path):
        if d.is_dir() and len(d.name) == 32:
            try:
                # check if the name can be converted to hex
                # I'm not sure what the 3DS does if there is a folder that is not a 32-char hex string.
                bytes.fromhex(d.name)
            except ValueError:
                continue
            else:
                id1s.append(d.name)
    return [sd_path, id1s]


@dataclass
class InstalledTitle():
    id: str
    title: AppTitle
    update_installed: bool
    dlc_installed: bool


def collect_existing_titles(boot9, movable, root_sd_path):
    crypto = CryptoEngine(boot9=boot9)
    crypto.setup_sd_key_from_file(movable)
    d = SDFilesystem(join(root_sd_path, 'Nintendo 3DS'), crypto=crypto)
    dlc_byte = '8C'
    update_byte = '0E'
    game_byte = '00'
    title_ids = get_existing_title_ids(boot9, movable, root_sd_path)

    BYTE_RANGE_START = 6
    BYTE_RANGE_END = 8
    game_ids = [
        x for x in title_ids if x[BYTE_RANGE_START:BYTE_RANGE_END] == game_byte]
    update_ids = [
        x for x in title_ids if x[BYTE_RANGE_START:BYTE_RANGE_END] == update_byte]
    dlc_ids = [
        x for x in title_ids if x[BYTE_RANGE_START:BYTE_RANGE_END] == dlc_byte]

    titles: dict[str, InstalledTitle] = {}
    for game in game_ids:
        titles[game] = InstalledTitle(
            game, get_app_title(game, d), False, False)

    for update in update_ids:
        related_game = update
        related_game = related_game[:BYTE_RANGE_START] + \
            game_byte + related_game[BYTE_RANGE_START + 2:]
        if related_game not in titles.keys():
            print(f'update {update} {get_app_title(update, d)
                                     } installed, but game {related_game} is not')
        else:
            titles[related_game].update_installed = True

    for dlc in dlc_ids:
        related_game = dlc
        related_game = related_game[:BYTE_RANGE_START] + \
            game_byte + related_game[BYTE_RANGE_START + 2:]
        if related_game not in titles.keys():
            print(f'dlc {dlc} {get_app_title(dlc, d)
                               } installed, but game {related_game} is not')
        else:
            titles[related_game].dlc_installed = True

    return titles.values()


def get_existing_title_ids(boot9, movable, root_sd_path) -> list[str]:
    if frozen:
        save3ds_fuse_path = join(script_dir, 'bin', 'save3ds_fuse')
    else:
        save3ds_fuse_path = join(script_dir, 'bin', platform, 'save3ds_fuse')
    if is_windows:
        save3ds_fuse_path += '.exe'
    if not isfile(save3ds_fuse_path):
        print("Couldn't find " + save3ds_fuse_path, 2)
        return []

    crypto = CryptoEngine(boot9=boot9)
    crypto.setup_sd_key_from_file(movable)

    d = SDFilesystem(join(root_sd_path, 'Nintendo 3DS'),
                     crypto=crypto)

    with TemporaryDirectory(suffix='-custom-install') as tempdir:
        # set up the common arguments for the two times we call save3ds_fuse
        save3ds_fuse_common_args = [
            save3ds_fuse_path,
            '-b', crypto.b9_path,
            '-m', movable,
            '--sd', root_sd_path,
            '--db', 'sdtitle',
            tempdir
        ]

        extra_kwargs = {}
        if is_windows:
            extra_kwargs['creationflags'] = 0x08000000  # CREATE_NO_WINDOW

        out = subprocess.run(save3ds_fuse_common_args + ['-x'],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             encoding='utf-8',
                             **extra_kwargs)
        titles = []
        for l in out.stdout.split('\n'):
            if len(l) != 17:
                continue

            titles.append(l[1:].upper())
        return list(set(titles))
