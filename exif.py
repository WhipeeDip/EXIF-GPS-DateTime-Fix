"""
File name: exif.py
Description: EXIF handling.
"""
import piexif

# constant values
# These EXIF tags are compliant with the standard version 2.31.
EXIF_DATE_TIME_ORIGINAL = 0x9003 # string, 24hr local time | "YYYY:MM:DD HH:MM:SS"
# EXIF_GPS = 0x8825 # Contains GPS tags listed below
EXIF_GPS_DATE = 0x001D # string, UTC | "YYYY:MM:DD"
EXIF_GPS_TIME = 0x0007 # tuple, 24hr UTC | ((H, 1), (M, 1), (S, 1))

def ispicture(path):
    """
    Checks if the file at path is a picture with EXIF data.

    Returns True if it is a picture, False otherwise.
    """

    try:
        piexif.load(path)
        return True
    except piexif.InvalidImageDataError:
        return False

def getdatetime(path):
    """
    Gets the original date time, GPS date, and GPS time EXIF tags of the image
    at path.

    Returns a dictionary with 'datetimeoriginal', 'gpsdate', 'gpstime'.
    - 'originaldate' is a string of the format 'YYYY-MM-DD'
    - 'oritinaltime' is a string of the format 'HH:MM:SS'
    - 'gpsdate' is a string of the format 'YYYY-MM-DD'
    - 'gpstime' is a string of the format 'HH:MM:SS'
    """

    # Load EXIF data and the relevant args
    exifdict = piexif.load(path)
    b_datetimeoriginal = exifdict['Exif'][EXIF_DATE_TIME_ORIGINAL]
    b_gpsdate = exifdict['GPS'][EXIF_GPS_DATE]
    t_gpstime = exifdict['GPS'][EXIF_GPS_TIME]

    # Convert raw data into something more readable
    datetimeoriginal = (b_datetimeoriginal.decode()).split(' ')
    originaldate = datetimeoriginal[0].replace(':', '-') # Change date colon to dash
    originaltime = datetimeoriginal[1]
    gpsdate = b_gpsdate.decode().replace(':', '-') # Change date colon to dash
    gpstime = ':'.join(map('{0:0>2}'.format, (t_gpstime[0][0], t_gpstime[1][0], t_gpstime[2][0]))) # Convert tuple to padded zero str

    retdict = {
        'originaldate': originaldate,
        'originaltime': originaltime,
        'gpsdate': gpsdate,
        'gpstime': gpstime
    }
    print(retdict)
    return retdict
