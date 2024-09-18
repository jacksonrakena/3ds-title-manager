import subprocess
import sys
from os import environ, scandir
from os.path import abspath, basename, dirname, isfile, join
from pprint import pformat
from sys import executable, platform
from tempfile import TemporaryDirectory

from pyctr.crypto import CryptoEngine, Keyslot, get_seed, load_seeddb
from pyctr.type.cdn import CDNError, CDNReader
from pyctr.type.cia import CIAError, CIAReader
from pyctr.type.ncch import NCCHSection
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


def get_existing_title_ids(boot9, movable, root_sd_path):
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
    # TODO: Move a lot of these into their own methods
    print("Finding path to install to...")
    [sd_path, id1s] = get_sd_path(root_sd_path, crypto)
    if len(id1s) > 1:
        raise RuntimeError(f'There are multiple id1 directories for id0 {crypto.id0.hex()}, '
                           f'please remove extra directories')
    elif len(id1s) == 0:
        raise RuntimeError(f'Could not find a suitable id1 directory for id0 {
            crypto.id0.hex()}')
    id1 = id1s[0]
    sd_path = join(sd_path, id1)

    # if self.cifinish_out:
    #     cifinish_path = self.cifinish_out
    # else:
    #     cifinish_path = join(self.sd, 'cifinish.bin')

    # try:
    #     cifinish_data = load_cifinish(cifinish_path)
    # except InvalidCIFinishError as e:
    #     self.log(f'{type(e).__qualname__}: {e}')
    #     self.log(f'{cifinish_path} was corrupt!\n'
    #              f'This could mean an issue with the SD card or the filesystem. Please check it for errors.\n'
    #              f'It is also possible, though less likely, to be an issue with custom-install.\n'
    #              f'Exiting now to prevent possible issues. If you want to try again, delete cifinish.bin from the SD card and re-run custom-install.')
    #     return None, False, 0

    db_path = join(sd_path, 'dbs')
    titledb_path = join(db_path, 'title.db')
    importdb_path = join(db_path, 'import.db')

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
            # hide console window
            extra_kwargs['creationflags'] = 0x08000000  # CREATE_NO_WINDOW

        # extract the title database to add our own entry to
        print('Extracting Title Database...')
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
        return titles
