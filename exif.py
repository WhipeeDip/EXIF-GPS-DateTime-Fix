"""
File name: exif.py
Description: EXIF handling.
"""

import time
import piexif

# constant values
# These EXIF tags are compliant with the standard version 2.31.
EXIF_DATE_TIME_ORIGINAL = 0x9003 # string, 24hr local time | "YYYY:MM:DD HH:MM:SS"
# EXIF_GPS = 0x8825 # Contains GPS tags listed below
EXIF_GPS_DATE = 0x001D # string, UTC | "YYYY:MM:DD"
EXIF_GPS_TIME = 0x0007 # tuples of tuples of ints, 24hr UTC | ((H, 1), (M, 1), (S, 1))
TIME_FORMAT = '%Y-%m-%d %H:%M:%S' # YYYY-MM-DD HH:MM:SS

def isimage(path):
    """
    Checks if the file is a picture with EXIF data.

    Paramters:
    path - String of the path to the image.

    Returns:
    True if it is a picture, False otherwise.
    """

    try:
        piexif.load(path)
        return True
    except piexif.InvalidImageDataError:
        return False

def getdatetime(path): # FIXME: UTC time zone
    """
    Gets the original date time, GPS date, and GPS time EXIF tags of the image

    Parameters:
    path - String of the path to the image.

    Returns:
    A dictionary with 'originaltime' and 'gpstime'.
    """

    # Load EXIF data and the relevant args
    exifdict = piexif.load(path)
    b_datetimeoriginal = exifdict['Exif'][EXIF_DATE_TIME_ORIGINAL]
    b_gpsdate = exifdict['GPS'][EXIF_GPS_DATE]
    t_gpstime = exifdict['GPS'][EXIF_GPS_TIME]

    # Convert raw data into something more readable
    # The string form is "YYYY-MM-DD HH:MM:SS"
    datetimeoriginal = (b_datetimeoriginal.decode()).split(' ')
    originald = datetimeoriginal[0].replace(':', '-') # Change date colon to dash
    originalt = datetimeoriginal[1]
    gpsd = b_gpsdate.decode().replace(':', '-') # Change date colon to dash
    gpst = ':'.join(map('{0:0>2}'.format, # Convert tuple to padded zero str
                           (t_gpstime[0][0], t_gpstime[1][0], t_gpstime[2][0])))

    originaltime = time.strptime(originald + ' ' + originalt, TIME_FORMAT)
    gpstime = time.strptime(gpsd + ' ' + gpst, TIME_FORMAT)

    retdict = {
        'originaltime': originaltime,
        'gpstime': gpstime
    }
    return retdict

def setgpsdatetime(path, newtime): # FIXME: UTC time zone
    """
    Sets the GPS date and time with the passed in parameters.

    Parameters:
    path - Path to the image to write to.
    newtime - Time specified in the Python time class. 

    Returns:
    The new EXIF data in dict form.
    """

    # Convert parameters to format required for EXIF
    timestr = newtime.strftime(TIME_FORMAT)
    datetimestr = timestr.split(' ')
    datestr = datetimestr[0]
    timestr = datetimestr[1]
    gpsdate = datestr.replace('-', ':').encode()
    gpstime = tuple(map(int, timestr.split(':'))) # See EXIF_GPS_TIME comment above
    gpstime = ((gpstime[0], 1), (gpstime[1], 1), (gpstime[2], 1))

    # Load EXIF data
    newexifdict = piexif.load(path)
    newexifdict['GPS'][EXIF_GPS_DATE] = gpsdate
    newexifdict['GPS'][EXIF_GPS_TIME] = gpstime

    # Prepare new EXIF data and insert
    newexifbytes = piexif.dump(newexifdict)
    piexif.insert(newexifbytes, path)

    return newexifdict
