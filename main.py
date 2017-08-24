"""
File name: main.py
Description: Main script that handles user prompting.
"""

import argparse
import os
import exif

# constant strings
ARG_PROG_NAME = 'exif-gps-datetime-fix'
ARG_DESC = 'A tool to fix EXIF GPS date and time stamps.'
ARG_AUTO_APPLY = '--auto-apply'
ARG_AUTO_APPLY_HELP = 'Automatically applies all edits without confirmation. Will automatically backup images as well, unless the "--no-backup" flag is specified.'
ARG_FOLLOW_SYMLINKS = '--follow-symlinks'
ARG_FOLLOW_SYMLINKS_HELP = 'Follows symlinks when using "--recursive".'
ARG_AUTO_NO_BACKUP = '--no-backup'
ARG_AUTO_NO_BACKUP_HELP = 'Disables automatic backup of the original images. Please be careful when using this option.'
ARG_IMAGE_PATH_LIST = 'pathlist'
ARG_IMAGE_PATH_LIST_HELP = 'The folder/file(s) path(s) of the image(s) you want to edit.'
ARG_RECURSIVE = '--recursive'
ARG_RECURSIVE_HELP = 'If any folders are specified/found, then recurse through all the subfolders.'
ERR_NOT_VALID_IAMGE = 'ERROR: The image "{0}" is not a valid image.'
ERR_PATH_DOES_NOT_EXIST = 'ERROR: The path "{0}" does not exist or this program does not have the proper permissions to access the file.'

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
                        if os.path.isfile(tmpfile) and exif.ispicture(tmpfile):
                            tmplist.append(tmpfile)
                        if args.recursive:
                            for dirname in dirnames:
                                tmpdir = os.path.join(root, dirname)
                                tmplist.append(tmpdir)
                        pathlist.extend(tmplist)
                print(pathlist)
            elif os.path.isfile(path) and exif.ispicture(path):
                datetimedict = exif.getdatetime(path)
            else:
                print(ERR_NOT_VALID_IAMGE.format(path))

if __name__ == '__main__':
    main()
