"""
File name: main.py
Description: Main script that handles user prompting.
"""

import argparse
import os
import shutil
import stat
import sys
import exif

# message strings
ANSWER_YES = 'Y'
ANSWER_NO = 'N'
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
                  'and do not hold the tool creator (me) liable for any damages or loss of any data.\n'
                  '\nPlease type {1} to accept this disclaimer or {2} to decline and exit the program: ')
MSG_DISCLAIMER_AGREE = ('\nYou have agreed to the disclaimer.\n'
                        '--------------------\n')
MSG_DISCLAIMER_DISAGREE = ('\nYou have disagreed to the disclaimer.\n'
                           '--------------------\n'
                           '\nExiting...\n')
MSG_DISCLAIMER_AUTO_AGREE = ('"--auto-apply" was set, automatically agreeing.\n'
                             '--------------------\n')
MSG_DISCLAIMER_NO_BACKUP = ('However, by setting the "--no-backup" flag you have disabled automatic backups. '
                            'If this was an accident, exit the program and remove the flag.')
MSG_EXIT = 'Exiting...\n'
MSG_FINISH = 'Finished, exiting...\n'
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
                           'the proper permissions to access the file/folder.')

# arg strings
ARG_PROG_NAME = 'exif-gps-datetime-fix'
ARG_DESC = 'A tool to fix EXIF GPS date and time stamps.'
ARG_AUTO_APPLY = '--auto-apply'
ARG_AUTO_APPLY_HELP = ('Automatically runs the program and applies all edits without confirmation. '
                       'Will automatically backup images as well, unless the '
                       '"--no-backup" flag is specified.')
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
            and not exif.isimage(os.path.join(dirpath, file))]

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

def main():
    """
    Main method to run the program.
    """

    # Create argument parser.
    # File/Folder argument(s): Folder(s)/file(s) to run the program on.
    # --auto-apply: Automatically apply changes without user confirmation.
    # --backup-path: Backup path for images.
    # --follow-symlinks: Follows symlinks when using --recursive.
    # --no-backup: Disables automatic backup of the original images.
    # --recursive: If a directory path is specified, recurse through all subfolders.
    # pathlist: List of paths to file/folders.
    parser = argparse.ArgumentParser(prog=ARG_PROG_NAME, description=ARG_DESC)
    parser.add_argument(ARG_AUTO_APPLY, help=ARG_AUTO_APPLY_HELP, action='store_true')
    backupgroup = parser.add_mutually_exclusive_group()
    backupgroup.add_argument(ARG_AUTO_NO_BACKUP, help=ARG_AUTO_NO_BACKUP_HELP, action='store_true')
    backupgroup.add_argument(ARG_BACKUP_PATH, help=ARG_BACKUP_PATH_HELP, action='store')
    parser.add_argument(ARG_FOLLOW_SYMLINKS, help=ARG_FOLLOW_SYMLINKS_HELP, action='store_true')
    parser.add_argument(ARG_RECURSIVE, help=ARG_RECURSIVE_HELP, action='store_true')
    parser.add_argument(ARG_IMAGE_PATH_LIST, nargs='*', help=ARG_IMAGE_PATH_LIST_HELP)
    args = parser.parse_args()
    print(args)

    # disclaimer
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
                copytree_existing(path, backuppath, symlinks=not args.follow_symlinks,
                                  ignore=ignore_non_images, copy_function=shutil.copy2,
                                  recursive=args.recursive)
            elif os.path.isfile(path) and exif.isimage(path):
                shutil.copy2(path, backuppath, follow_symlinks=not args.follow_symlinks)

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
                        if os.path.isfile(tmpfile) and exif.isimage(tmpfile): # get all images
                            tmplist.append(tmpfile)
                        if args.recursive: # go through subdirs if recrusive enabled
                            for dirname in dirnames:
                                tmpdir = os.path.join(root, dirname)
                                tmplist.append(tmpdir)
                        pathlist.extend(tmplist) # add files/subdirs to the list
            elif os.path.isfile(path) and exif.isimage(path): # valid image file

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

    print(MSG_FINISH)
    exit()

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
