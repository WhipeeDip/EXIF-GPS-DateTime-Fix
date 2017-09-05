# EXIF-GPS-DateTime-Fix

A small Python program that fixes incorrect GPS date/time stamps in image EXIF data.

## Details
I honestly have no idea what's causing the bug itself, but on my phone (OnePlus 3T on LineageOS 14.1 official weeklies) some images are being saved with a GPS time stamp with the date January 18, 2038. It appears many Android apps sort images by this GPS timestamp, not the original picture taken timestamp. This results in some images staying on the top when sorted by time, which kind of gets annoying.

There are multiple places in the EXIF data the date/time is stored. The three this program is concerned with are in tags called `DateTimeOriginal` (0x9003), `GPSTimeStamp` (0x0007 under `GPSInfo` 0x8825), and `GPSDateStamp` (0x001D under `GPSInfo` 0x8825). The GPS info is stored in UTC time, while the `DateTimeOriginal` tag does not necessarily have an attached timestamp. To be more specific, there are various non GPS tags that store time zone offsets, but none of my images have them stored. Hence why probably most Android apps sort by GPS date/time.

There are a few limitations to this program. First, I cannot retrieve what `GPSTimeStamp` and `GPSDateStamp` are really supposed to be. Unfortunately, there is no way to retrieve the original GPS lock time. However, matching it with `DateTimeOriginal` gets my intended effect to sort by time properly. Second, I have not implemented the ability to auto detect time zones based off of GPS coordinates. While there are certainly online and offline libraries/APIs to do this, I felt implementing an online API could raise privacy concerns of transmitting GPS coordinates to third party sources and keeping up to date with changing time standards offline could be an issue. Third, this is only guaranteed to comply with properly implemented EXIF v2.2 standards. While I don't expect the standards to change drastically between older/newer, there is always the chance it may. I also do not attempt to detect different tags and fix them appropriately.

## Setup
1. Download and install Python 3.6.2. I cannot guarantee this will work on any other version.
2. Download this repository as a zip (or really, just `main.py` and `utils.py`) and extract it somewhere.
3. Run the program with `python main.py [image_dir]`. Check out the [arguments](#arguments) section below for more details.

## Arguments
### <a name="arguments"></a>
You can see these at any time with `-h` or `--help`.
* `--auto`: Automatically runs the program and applies all edits without confirmation. Will automatically backup images as well, unless the `--no-backup` flag is specified. Requires `--timezone` to be set. Please note this auto agrees to the disclaimer.
* `--no-backup`: Disables automatic backup of the original images. Please be careful when using this option.
* `--backup-path [BACKUP_PATH]`: Specifies the image backup path. Default backup path is `/script_path/backup/`. This arg is not allowed if `--no-backup` is specified.
* `--follow-symlinks`: Follows symlinks when using `--recurisve`.
* `--recursive`: If any folders are specified/found, then recurse through all subfolders.
* `--timezone [TIMEZONE]`: Automatically applies the time zone used in calculating the new GPS date/time. Must be in the format {+|-}HHMM. For example, "-0800". If you are using "--auto", this arg must be specified.

## Credits
* [piexif](https://pypi.python.org/pypi/piexif) (MIT License)
