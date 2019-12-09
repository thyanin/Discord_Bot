import os
from PIL import Image
import json

def read_json():
    return json.load(open('./config/configuration.json', 'r'))

config = read_json()

def get_files(champs):
    files = []
    for champ in champs:
        files.append(f'./{config["FOLDER_CHAMP_ICON"]}/{champ}.png')
    return files

def create_new_image(champs):
    files = get_files(champs)
    result = Image.new("RGB", (600, 120))
    for index, file in enumerate(files):
        path = os.path.expanduser(file)
        img = Image.open(path)
        img.thumbnail((120, 120), Image.ANTIALIAS)
        x = index * 120
        y = index %  120
        w, h = img.size
        result.paste(img, (x, y, x + w, y + h))
    result.save(os.path.expanduser(f'./{config["FOLDER_CHAMP_SPLICED"]}/image.jpg'))
    return 0


# === TEST === #
def testModule():
    assert(config["TOGGLE_AUTO_DELETE"] == True)
    assert(len(get_files(['Pyke', 'Blitzcrank', 'Annie', 'Ahri', 'Nautilus'])) == 5)
    assert(create_new_image(['Pyke', 'Blitzcrank', 'Annie', 'Ahri', 'Nunu']) == 0)

#testModule()
# === TEST END === #