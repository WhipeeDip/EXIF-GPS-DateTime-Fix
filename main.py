"""
File name: main.py
Description: Main script that handles user prompting.
"""

import argparse
import os
import shutil
import exif

# message strings
ANSWER_YES = 'Y'
ANSWER_NO = 'N'
MSG_BACKING_UP = 'Backing up all images...\n'
MSG_DISCLAIMER = ('\n--------------------\n'
                  'DISCLAIMER:\n'
                  'This is a tool that replaces the GPS date/time stamp with the original date/time stamp that is in the EXIF data.\n'
                  'I do understand that images capture very important memories, which is why this disclaimer is here before it proceeds to do any edits.\n'
                  'While this tool should not affect the image itself in any way, there is still the unlikely chance that it may still damage your image or even other EXIF data.\n'
                  'This tool automatically creates its own backups. {0}\n'
                  'By continuing on, you agree that you have already made your own proper backups and do not hold the tool creator (me) liable for any damages or loss of any data.\n'
                  '\nPlease type {1} to accept this disclaimer or {2} to decline and exit the program: ')
MSG_DISCLAIMER_AGREE = ('\nYou have agreed to the disclaimer.\n'
                        '--------------------\n')
MSG_DISCLAIMER_DISAGREE = ('\nYou have disagreed to the disclaimer.\n'
                           '--------------------\n'
                           '\nExiting...\n')
MSG_DISCLAIMER_AUTO_AGREE = ('"--auto-apply" was set, automatically agreeing.\n'
                             '--------------------\n')
MSG_DISCLAIMER_NO_BACKUP = 'However, by setting the "--no-backup" flag you have disabled automatic backups. If this was an accident, exit the program and remove the flag.'
MSG_EXIT = 'Exiting...\n'
MSG_IMAGE_DATE = ('Image: {0}\n'
                  'Original date: {1} | GPS date: {2}\n'
                  'Original time: {3}   | GPS time: {4}')
MSG_INVALID_ANSWER_YN = 'Invalid answer, please enter {0} or {1}: '.format(ANSWER_YES, ANSWER_NO)
MSG_PROMPT_APPLY = ('Do you want to replace the GPS date/time with the original date/time? '
                    '({0}/{1}) '.format(ANSWER_YES, ANSWER_NO))
MSG_RESP_REPLACE_Y = 'Replacing GPS date/time...\n'
MSG_RESP_REPLACE_N = 'Skipping replacement of GPS date/time...\n'
MSG_SKIP_BACK_UP = 'Skipping backup of images...\n'

# error strings
ERR_NOT_VALID_IAMGE = 'ERROR: The image "{0}" is not a valid image.'
ERR_PATH_DOES_NOT_EXIST = ('ERROR: The path "{0}" does not exist or this program does not have '
                           'the proper permissions to access the file.')

# arg strings
ARG_PROG_NAME = 'exif-gps-datetime-fix'
ARG_DESC = 'A tool to fix EXIF GPS date and time stamps.'
ARG_AUTO_APPLY = '--auto-apply'
ARG_AUTO_APPLY_HELP = ('Automatically runs the program and applies all edits without confirmation. '
                       'Will automatically backup images as well, unless the '
                       '"--no-backup" flag is specified.')
ARG_FOLLOW_SYMLINKS = '--follow-symlinks'
ARG_FOLLOW_SYMLINKS_HELP = 'Follows symlinks when using "--recursive".'
ARG_AUTO_NO_BACKUP = '--no-backup'
ARG_AUTO_NO_BACKUP_HELP = ('Disables automatic backup of the original images. '
                           ' Please be careful when using this option.')
ARG_IMAGE_PATH_LIST = 'pathlist'
ARG_IMAGE_PATH_LIST_HELP = 'The folder/file(s) path(s) of the image(s) you want to edit.'
ARG_RECURSIVE = '--recursive'
ARG_RECURSIVE_HELP = 'If any folders are specified/found, then recurse through all the subfolders.'

def main():
    """
    Main method to run the program.
    """

    # Create argument parser.
    # File/Folder argument(s): Folder(s)/file(s) to run the program on.
    # --auto-apply: Automatically apply changes without user confirmation.
    # --no-backup: Disables automatic backup of the original images.
    # --recursive: If a directory path is specified, recurse through all subfolders.
    # pathlist: List of paths to file/folders.
    parser = argparse.ArgumentParser(prog=ARG_PROG_NAME, description=ARG_DESC)
    parser.add_argument(ARG_AUTO_APPLY, help=ARG_AUTO_APPLY_HELP, action='store_true')
    parser.add_argument(ARG_AUTO_NO_BACKUP, help=ARG_AUTO_NO_BACKUP_HELP, action='store_true')
    parser.add_argument(ARG_FOLLOW_SYMLINKS, help=ARG_FOLLOW_SYMLINKS_HELP, action='store_true')
    parser.add_argument(ARG_RECURSIVE, help=ARG_RECURSIVE_HELP, action='store_true')
    parser.add_argument(ARG_IMAGE_PATH_LIST, nargs='*', help=ARG_IMAGE_PATH_LIST_HELP)
    args = parser.parse_args()

    # Disclaimer
    backupmsg = ''
    if args.no_backup:
        backupmsg = MSG_DISCLAIMER_NO_BACKUP
    if args.auto_apply:
        print(MSG_DISCLAIMER.format(backupmsg, ANSWER_YES, ANSWER_NO))
        print(MSG_DISCLAIMER_AUTO_AGREE)
    else:
        agreement = input(MSG_DISCLAIMER.format(backupmsg, ANSWER_YES, ANSWER_NO))
        while True:
            if agreement.upper() == ANSWER_YES:
                print(MSG_DISCLAIMER_AGREE)
                break
            elif agreement.upper() == ANSWER_NO:
                print(MSG_DISCLAIMER_DISAGREE)
                exit()
            else:
                agreement = input(MSG_INVALID_ANSWER_YN)

    # iterate through all path args
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
                        if os.path.isfile(tmpfile) and exif.ispicture(tmpfile): # get all images
                            tmplist.append(tmpfile)
                        if args.recursive: # go through subdirs if recrusive enabled
                            for dirname in dirnames:
                                tmpdir = os.path.join(root, dirname)
                                tmplist.append(tmpdir)
                        pathlist.extend(tmplist) # add files/subdirs to the list
            elif os.path.isfile(path) and exif.ispicture(path): # valid image file
                # backup before editing
                #if not args.no_backup:
                #    shutil.copy2(path, 'backup/')

                # get EXIF date/time
                datetimedict = exif.getdatetime(path)
                originaldate = datetimedict['originaldate']
                originaltime = datetimedict['originaltime']
                gpsdate = datetimedict['gpsdate']
                gpstime = datetimedict['gpstime']

                # print original and GPS date/time, prompt for replacement
                print(MSG_IMAGE_DATE.format(path, originaldate, gpsdate, originaltime, gpstime))
                if args.auto_apply:
                    replace = True
                else:
                    replaceinput = input(MSG_PROMPT_APPLY)
                    replace = False

                # check for invalid input
                while not replace: 
                    if replaceinput.upper() == ANSWER_YES:
                        replace = True
                        break
                    elif replaceinput.upper() == ANSWER_NO:
                        replace = False
                        break
                    else:
                        replaceinput = input(MSG_INVALID_ANSWER_YN)

                if not replace: # no replace, move on
                    print(MSG_RESP_REPLACE_N)
                    continue
                else: # replace
                    print(MSG_RESP_REPLACE_Y)
                    #exif.setgpsdatetime(path, originaldate, originaltime)
            else: # not a file and/or image
                print(ERR_NOT_VALID_IAMGE.format(path))

# Check for main function execution
if __name__ == '__main__':
    try:
        main()
    except EOFError:
        print(MSG_EXIT)
        exit()
    except KeyboardInterrupt:
        print(MSG_EXIT)
        exit()
