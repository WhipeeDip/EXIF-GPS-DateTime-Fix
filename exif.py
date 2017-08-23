# File name: exif.py
# Description: EXIF handling.

from PIL import Image

def ispicture(path):
    try:
        image = Image.open(path)
        image.close()
        return True
    except IOError:
        return False
