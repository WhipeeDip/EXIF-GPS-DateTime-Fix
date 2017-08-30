"""
File name: utils.py
Description: Contains various functions that help this program run.
"""

from datetime import datetime, timedelta
import os
import re
import shutil
import stat
import piexif

# errors
ERR_TIMEZONE_INVALID_FORMAT = ('Timezone is in an invalid format. '
                               'It should be {{+|-}}HHMM.')

# constant values
# These EXIF tags are compliant with the standard version 2.31.
EXIF_DATE_TIME_ORIGINAL = 0x9003 # string, 24hr local time | "YYYY:MM:DD HH:MM:SS"
# EXIF_GPS = 0x8825 # Contains GPS tags listed below
EXIF_GPS_DATE = 0x001D # string, UTC | "YYYY:MM:DD"
EXIF_GPS_TIME = 0x0007 # tuples of tuples of ints, 24hr UTC | ((H, 1), (M, 1), (S, 1))
REGEX_TIMEZONE = '^[+-][0-2][0-9][0-5][0-9]$' # Timezone format is {+|-}HHMM
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S' # YYYY-MM-DD HH:MM:SS

def copytree_existing(src, dst, symlinks=False, ignore=None, copy_function=shutil.copy2, recursive=True):
    """
    A shutil.copytree clone that handles dst directory already existing.
    Credits to Cyrille Pontvieux on Stack Overflow for this implementation:
    https://stackoverflow.com/a/22331852/1993267
    I've added some comments and changed some variables for readability on my end.

    Parameters:
    src - The source path.
    dst - The destination path.
    symlinks - True to copy symlinks, False to copy the file pointed to at symlink.
    ignore - A list of files to ignore.
    copy_function - The copy function to copy files with.

    Returns:
    Nothing.
    """

    # if dest path doesn't exist, make it and copy stat
    if not os.path.exists(dst):
        os.makedirs(dst)
        shutil.copystat(src, dst)

    # begin going through file list
    filelist = os.listdir(src)
    if ignore: # remove ignored files
        excl = ignore(src, filelist)
        filelist = [file for file in filelist if file not in excl]
    for file in filelist:
        srcfile = os.path.join(src, file)
        dstfile = os.path.join(dst, file)
        if symlinks and os.path.islink(srcfile): # handle symlinks as needed
            if os.path.lexists(dstfile):
                os.remove(dstfile)
            os.symlink(os.readlink(srcfile), dstfile)
            try:
                srcstat = os.lstat(srcfile)
                srcmode = stat.S_IMODE(srcstat.st_mode)
                os.lchmod(dstfile, srcmode)
            except:
                pass # no lchmod
        elif recursive and os.path.isdir(srcfile): # recurse on directories
            copytree_existing(srcfile, dstfile, symlinks, ignore, copy_function)
        else:
            copy_function(srcfile, dstfile)

def datetime_to_str(dt):
    """
    Converts a Python datetime to a dictionary.

    Parameters:
    dt - A Python datetime.

    Returns:
    A dictionary with:
    - 'date': "YYYY-MM-DD"
    - 'time': "HH:MM:SS"
    """
    dtarr = dt.strftime(DATETIME_FORMAT).split(' ')
    datestr = dtarr[0]
    timestr = dtarr[1]
    dtdict = {
        'date': datestr,
        'time': timestr
    }
    return dtdict

def getdatetime(path):
    """
    Gets the original date time, GPS date, and GPS time EXIF tags of the image

    Parameters:
    path - String of the path to the image.

    Returns:
    A dictionary with 'originaltime' and 'gpstime' which are both in Python datetime format.
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

    originaldatetime = datetime.strptime(originald + ' ' + originalt, DATETIME_FORMAT)
    gpsdatetime = datetime.strptime(gpsd + ' ' + gpst, DATETIME_FORMAT)
    retdict = {
        'originaldatetime': originaldatetime,
        'gpsdatetime': gpsdatetime
    }
    return retdict

def ignore_non_images(dirpath, filenames):
    """
    Generates ignores for shutil.copytree(). Ignores non images and follows dirs.

    Parameters:
    dirpath - The path of the directory itself.
    filenames - A list of filenames in the directory.

    Returns:
    A list of filenames to ignore.
    """
    return [file for file in filenames
            if not os.path.isdir(os.path.join(dirpath, file))
            and not isimage(os.path.join(dirpath, file))]

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


def setgpsdatetime(path, newdatetime):
    """
    Sets the GPS date and time with the passed in parameters.

    Parameters:
    path - Path to the image to write to.
    newdatetime - Time specified in the Python datetime class.

    Returns:
    The new EXIF data in dict form.
    """

    # Convert parameters to format required for EXIF
    timestr = newdatetime.strftime(DATETIME_FORMAT)
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

def tzoffset_to_timedelta(timezone):
    """
    Converts a timezone into a Python timedelta.
    Raises a ValueError if timezone is not the proper format.

    Parameters:
    timezone - A string timezone in the format "{+|-}HHMM".

    Returns:
    timedelta of the timezone.
    """
    if not re.search(REGEX_TIMEZONE, timezone):
        raise ValueError(ERR_TIMEZONE_INVALID_FORMAT)

    timearr = timezone.strip('+').strip('-')
    hours = int(timearr[0:2])
    minutes = int(timearr[2:4])
    offset = (hours * 60 * 60) + (minutes * 60)
    if timezone[0] == '-':
        offset = -offset
    delta = timedelta(seconds=offset)

    return delta
