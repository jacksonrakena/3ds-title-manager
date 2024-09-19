
from os.path import join

from pyctr.crypto import CryptoEngine
from pyctr.type.sd import SDFilesystem



def get_app_title(title_id: str, fs: SDFilesystem):
    return fs.open_title(title_id).contents[0].exefs.icon.get_app_title()

def test():
    root_sd_path = '/Users/jackson/Desktop/3ds sdcard backup'
    boot9 = '/Users/jackson/Desktop/3ds sdcard backup/gm9/out/boot9.bin'
    movable = '/Users/jackson/Desktop/3ds sdcard backup/gm9/out/movable.sed'
    crypto = CryptoEngine(boot9=boot9)
    crypto.setup_sd_key_from_file(movable)
    d = SDFilesystem(join(root_sd_path, 'Nintendo 3DS'),
                     crypto=crypto)
    title = d.open_title('0004000000105a00')
    app_title = title.contents[0].exefs.icon.get_app_title()
    print(app_title)


if __name__ == '__main__':
    test()
