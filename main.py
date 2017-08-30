"""
File name: main.py
Description: Main script that handles user prompting.
"""

import argparse
import os
import re
import shutil
import sys
import time
import utils

# message strings
ANSWER_YES = 'Y'
ANSWER_NO = 'N'
ANSWER_REPEAT = 'R'
MSG_BACKING_UP = 'Backing up all images to {0}...\n'
MSG_DISCLAIMER = ('\n--------------------\n'
                  'DISCLAIMER:\n'
                  'This is a tool that replaces the GPS date/time stamp with the original date/time '
                  'stamp that is in the EXIF data.\n'
                  'I do understand that images capture very important memories, which is why this '
                  'disclaimer is here before it proceeds to do any edits.\n'
                  'While this tool should not affect the image itself in any way, there is still '
                  'the unlikely chance that it may still damage your image or even other EXIF data.\n'
                  'This tool automatically creates its own backups. {0}\n'
                  'By continuing on, you agree that you have already made your own proper backups '
                  'and do not hold the tool creator (me) liable for any damages or loss of any data.\n')
MSG_PROMPT_DISCLAIMER = '\nPlease type Y to accept this disclaimer or N to decline and exit the program: '
MSG_DISCLAIMER_AGREE = ('\nYou have agreed to the disclaimer.\n'
                        '--------------------\n')
MSG_DISCLAIMER_DISAGREE = ('\nYou have disagreed to the disclaimer.\n'
                           '--------------------\n'
                           '\nExiting...\n')
MSG_DISCLAIMER_AUTO_AGREE = ('"--auto-apply" was set, automatically agreeing.\n'
                             '--------------------\n')
MSG_DISCLAIMER_NO_BACKUP = ('However, by setting the "--no-backup" flag you have disabled automatic backups. '
                            'If this was an accident, exit the program and remove the flag.')
MSG_GPS_DATETIME_NEW = ('New GPS date in UTC: {0}\n'
                        'New GPS time in UTC: {1}')
MSG_FINISH = '\n\nFinished, exiting...\n'
MSG_IMAGE_DATE = ('Image: {0}\n'
                  'Original date: {1} | GPS date in UTC: {2}\n'
                  'Original time: {3}   | GPS time in UTC: {4}')
MSG_INVALID_ANSWER_YN = 'Invalid answer, please enter {0} or {1}: '
MSG_PROMPT_REPLACE = ('Do you want to replace the GPS date/time with the original date/time? '
                    '([Y]es/[N]o/[R]epeat): ')
MSG_PROMPT_TIMEZONE = ('Time zone of the original date/time that this photo was taken '
                       '(in the format {{+|-}}HH:MM) [{0}]: ')
MSG_PROMPT_TIMEZONE_INVALID = ('Invalid time zone. '
                               'Must be in the format {{+|-}}HH:MM. For example, "-0800" [{0}]: ')
MSG_RESP_REPLACE_Y = 'Replacing GPS date/time...\n'
MSG_RESP_REPLACE_N = 'Skipping replacement of GPS date/time...\n'
MSG_SKIP_BACK_UP = 'Skipping backup of images...\n'
MSG_USER_EXIT = '\n\nUser exit...\n'

# error strings
ERR_NOT_VALID_IAMGE = 'ERROR: The image "{0}" is not a valid image.'
ERR_PATH_DOES_NOT_EXIST = ('ERROR: The path "{0}" does not exist or this program does not have '
                           'the proper permissions to access the file/folder.')
ERR_TIMEZONE_INVALID = 'The timezone must be in the format {{+|-}}HHMM. For example, "-0800": '
ERR_TIMEZONE_NOT_SET = '"--timezone" must be set when using "--auto".'

# arg strings
ARG_PROG_NAME = 'exif-gps-datetime-fix'
ARG_DESC = 'A tool to fix EXIF GPS date and time stamps.'
ARG_AUTO = '--auto'
ARG_AUTO_HELP = ('Automatically runs the program and applies all edits without confirmation. '
                 'Will automatically backup images as well, unless the "--no-backup" flag is '
                 'specified. Requires "--timezone" to be set. '
                 'Please note this auto agrees to the disclaimer.')
ARG_BACKUP_PATH = '--backup-path'
ARG_BACKUP_PATH_HELP = ('Specifies the image backup path. '
                        'Default backup path is "/script_path/backup/". '
                        'This arg is not allowed if "--no-backup" is specified.')
ARG_FOLLOW_SYMLINKS = '--follow-symlinks'
ARG_FOLLOW_SYMLINKS_HELP = 'Follows symlinks when using "--recursive".'
ARG_AUTO_NO_BACKUP = '--no-backup'
ARG_AUTO_NO_BACKUP_HELP = ('Disables automatic backup of the original images. '
                           ' Please be careful when using this option.')
ARG_IMAGE_PATH_LIST = 'pathlist'
ARG_IMAGE_PATH_LIST_HELP = 'The folder/file(s) path(s) of the image(s) you want to edit.'
ARG_RECURSIVE = '--recursive'
ARG_RECURSIVE_HELP = 'If any folders are specified/found, then recurse through all the subfolders.'
ARG_TIMEZONE = '--timezone'
ARG_TIMEZONE_HELP = ('Automatically applies the timezone used in calculating the new GPS date/time. '
                     'Must be in the format {+|-}HHMM. For example, "-0800". '
                     'If you are using "--auto", this arg must be specified.')

def main():
    """
    Main method to run the program.
    """

    # Create argument parser.
    # File/Folder argument(s): Folder(s)/file(s) to run the program on.
    # --auto: Automatically apply changes without user confirmation. Requires --timezone
    # --backup-path: Backup path for images.
    # --follow-symlinks: Follows symlinks when using --recursive.
    # --no-backup: Disables automatic backup of the original images.
    # --recursive: If a directory path is specified, recurse through all subfolders.
    # --timezone: Specifies timezone.
    # pathlist: List of paths to file/folders.
    parser = argparse.ArgumentParser(prog=ARG_PROG_NAME, description=ARG_DESC)
    parser.add_argument(ARG_AUTO, help=ARG_AUTO_HELP, action='store_true')
    backupgroup = parser.add_mutually_exclusive_group()
    backupgroup.add_argument(ARG_AUTO_NO_BACKUP, help=ARG_AUTO_NO_BACKUP_HELP, action='store_true')
    backupgroup.add_argument(ARG_BACKUP_PATH, help=ARG_BACKUP_PATH_HELP, action='store')
    parser.add_argument(ARG_FOLLOW_SYMLINKS, help=ARG_FOLLOW_SYMLINKS_HELP, action='store_true')
    parser.add_argument(ARG_RECURSIVE, help=ARG_RECURSIVE_HELP, action='store_true')
    parser.add_argument(ARG_IMAGE_PATH_LIST, nargs='+', help=ARG_IMAGE_PATH_LIST_HELP)
    parser.add_argument(ARG_TIMEZONE, help=ARG_TIMEZONE_HELP)
    args = parser.parse_args()

    # arg parse checking
    if args.auto and not args.timezone:
        parser.error(ERR_TIMEZONE_NOT_SET)
    if args.timezone:
        if not re.search(utils.REGEX_TIMEZONE, args.timezone):
            parser.error(ERR_TIMEZONE_INVALID)

    # disclaimer
    backupmsg = ''
    if args.no_backup:
        backupmsg = MSG_DISCLAIMER_NO_BACKUP
    if args.auto:
        print(MSG_DISCLAIMER.format(backupmsg))
        print(MSG_PROMPT_DISCLAIMER)
        print(MSG_DISCLAIMER_AUTO_AGREE)
    else:
        print(MSG_DISCLAIMER.format(backupmsg))
        agreement = input(MSG_PROMPT_DISCLAIMER)
        while True:
            if agreement.upper() == ANSWER_YES:
                print(MSG_DISCLAIMER_AGREE)
                break
            elif agreement.upper() == ANSWER_NO:
                print(MSG_DISCLAIMER_DISAGREE)
                exit()
            else:
                agreement = input(MSG_INVALID_ANSWER_YN)

    # backup
    if args.no_backup:
        print(MSG_SKIP_BACK_UP)
    else:
        # check for backup path if speified
        # if none, then /script_path/backup_images
        backuppath = os.path.dirname(os.path.realpath(sys.argv[0]))
        if args.backup_path:
            backuppath = os.path.normcase(args.backup_path)
        else:
            backuppath = os.path.join(backuppath, 'backup_images')
        if not os.path.exists(backuppath):
            os.makedirs(backuppath)

        print(MSG_BACKING_UP.format(backuppath))

        for path in args.pathlist:
            if os.path.isdir(path):
                # from python 3.6.2 shutil docs: symlinks param - (which the function above mimics)
                # "if false or omitted, the contents and metadata of the linked files are copied to the new tree"
                # therefore, if follow_symlinks is set, we should negate it to copy symlinked files
                utils.copytree_existing(path, backuppath, symlinks=not args.follow_symlinks,
                                  ignore=utils.ignore_non_images, copy_function=shutil.copy2,
                                  recursive=args.recursive)
            elif os.path.isfile(path) and utils.isimage(path):
                shutil.copy2(path, backuppath, follow_symlinks=not args.follow_symlinks)

    # iterate through all path args
    lasttz = args.timezone or time.strftime('%z', time.localtime()) # get set or current tz
    pathlist = list(args.pathlist)
    while pathlist:
        path = pathlist.pop(0)
        if not os.path.exists(path): # check to make sure path exists and we can open
            print(ERR_PATH_DOES_NOT_EXIST.format(path))
        else:
            if os.path.isdir(path): # if dir, get all files in dir
                for (root, dirnames, filenames) in os.walk(path, topdown=True, followlinks=args.follow_symlinks):
                    for filename in filenames:
                        tmplist = []
                        tmpfile = os.path.join(root, filename)
                        if os.path.isfile(tmpfile) and utils.isimage(tmpfile): # get all images
                            tmplist.append(tmpfile)
                        if args.recursive: # go through subdirs if recrusive enabled
                            for dirname in dirnames:
                                tmpdir = os.path.join(root, dirname)
                                tmplist.append(tmpdir)
                        pathlist.extend(tmplist) # add files/subdirs to the list
            elif os.path.isfile(path) and utils.isimage(path): # valid image file

                # get EXIF date/time
                datetimedict = utils.getdatetime(path)
                originaldatetime = datetimedict['originaldatetime']
                odtdict = utils.datetime_to_str(originaldatetime)
                odatestr = odtdict['date']
                otimestr = odtdict['time']
                gpsdatetime = datetimedict['gpsdatetime']
                gdtdict = utils.datetime_to_str(gpsdatetime)
                gdatestr = gdtdict['date']
                gtimestr = gdtdict['time']
                print(MSG_IMAGE_DATE.format(path, odatestr, gdatestr, otimestr, gtimestr))

                # calculate time zone since GPS time is in UTC
                tzstr = lasttz
                if args.timezone:
                    print(MSG_PROMPT_TIMEZONE.format(lasttz))
                else:
                    tzstr = input(MSG_PROMPT_TIMEZONE.format(lasttz)) or lasttz
                    while True:
                        if re.match(utils.REGEX_TIMEZONE, tzstr):
                            break
                        else:
                            tzstr = input(MSG_PROMPT_TIMEZONE_INVALID.format(lasttz)) or lasttz
                lasttz = tzstr
                tzdelta = utils.tzoffset_to_timedelta(tzstr)
                utcdatetime = originaldatetime - tzdelta
                utcdict = utils.datetime_to_str(utcdatetime)
                utcdatestr = utcdict['date']
                utctimestr = utcdict['time']
                print(MSG_GPS_DATETIME_NEW.format(utcdatestr, utctimestr))

                # replace auto/prompt
                repeat = False
                if args.auto:
                    replace = True
                else:
                    replaceinput = input(MSG_PROMPT_REPLACE)
                    replace = False
                while not replace:
                    if replaceinput.upper() == ANSWER_YES:
                        replace = True
                        break
                    elif replaceinput.upper() == ANSWER_NO:
                        replace = False
                        break
                    elif replaceinput.upper() == ANSWER_REPEAT:
                        repeat = True
                        break
                    else:
                        replaceinput = input(MSG_INVALID_ANSWER_YN)
                if repeat:
                    pathlist.insert(0, path)
                    print()
                    continue

                if not replace: # no replace, move on
                    print(MSG_RESP_REPLACE_N)
                    continue
                else: # replace
                    print(MSG_RESP_REPLACE_Y)
                    #setgpsdatetime(path, newdatetime)
            else: # not a file and/or image
                print(ERR_NOT_VALID_IAMGE.format(path))

    print(MSG_FINISH)
    exit()

# Check for main function execution
if __name__ == '__main__':
    try:
        main()
    except EOFError:
        print(MSG_USER_EXIT)
        exit()
    except KeyboardInterrupt:
        print(MSG_USER_EXIT)
        exit()
