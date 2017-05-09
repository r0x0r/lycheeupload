#!/bin/python
# -*- coding: utf-8 -*-
"""
lychee upload v1.3
(C) 2014-2015 Roman Sirokov

Imports images from a location on hard drive to the Lychee installation on a remote server via SSH.

Based on lycheesync by Gustave Paté
https://github.com/GustavePate/lycheesync

"""


import argparse
import os
import sys
import re
import logging

import sources.directory as directory
import upload
from conf import *


logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    try:
        if conf.source == "directory":
            albums = directory.get_photos()
        elif conf.source == "iPhoto" or conf.source == "Aperture":
            albums = iphoto.get_photos()

        u = upload.Upload()
        u.upload(albums)

    except Exception as e:
        logger.error(e, exc_info=True)
        sys.exit(1)


def parse_arguments():
    """
    Specify and parse command line arguments common to all the platforms
    """

    parser = argparse.ArgumentParser(description=("Upload all the photos in the local photo directory and its "
                                                  "sub-directories to Lychee. Directories are converted to albums."))
    parser.add_argument('server', metavar='username@hostname:path', type=str, nargs=1,
                        help='Server connection string with a full path to the directory where Lychee is installed.')

    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument('-d', '--dir', help="path to the photo directory where to export photos from.", type=str)

    parser.add_argument('-r', '--replace', help="replace albums in Lychee with local ones", action='store_true')
    parser.add_argument('-P', '--port', help="alternative SSH port", type=int)
    parser.add_argument('-p', '--public', help="make uploaded photos public", action='store_true')
    parser.add_argument('-v', '--verbose', help='print verbose messages', action='store_true')
    parser.add_argument('-q', '--quality', help='JPEG quality 0-99 for resized pictures', type=int)
    parser.add_argument('--medium', help='Maximum size for medium sized pictures. 1920px by default', type=int)
    parser.add_argument('--big', help='Maximum size for big sized pictures. By default pictures are untouched ',
                        type=int)
    parser.add_argument('--originals',
                        help='Upload original untouched files. To be used with the --big option, otherwise ignored.',
                        action='store_true')

    if conf.osx:
        add_mac_arguments(parser, source_group)

    args = parser.parse_args()

    conf.replace = args.replace
    conf.public = args.public

    if args.verbose:
        conf.verbose = logging.DEBUG

    if args.server:
        if not parse_server_string(args.server[0]):
            logger.error("Server string must be in the username@hostname:path format")
            return False

    if args.dir:
        if not os.path.exists(args.dir):
            logger.error("Photo directory does not exist:" + args.dir)
            return False
        conf.dir = args.dir
        conf.source = "directory"
    elif not conf.osx:
        logger.error("Please specify a directory to export photos from")
        return False

    if args.port:
        conf.port = args.port
    else:
        conf.port = 22

    if args.quality:
        conf.quality = args.quality
    else:
        conf.quality = 70

    if args.medium:
        conf.medium_size = args.medium
    else:
        conf.medium_size = 1920

    if args.big:
        conf.big_size = args.big

    if args.originals and args.big:
        conf.upload_originals = True

    if conf.osx:
        if not parse_mac_arguments(args):
            return False

    return True


def parse_server_string(server_string):
    """
    Parse a server string and store values in the global configuration
    :param server_string: Server string in the form of user@host:path
    :return: True if successful, False if parsing fails
    """
    match = re.match("(.+)@([\w\d\-\.]+):(.+)", server_string)

    if match:
        conf.username = match.group(1)
        conf.server = match.group(2)
        conf.path = match.group(3)

        return True
    else:
        return False


def parse_mac_arguments(args):
    """
    Parse command line arguments specific to OSX (iPhoto / Aperture stuff)
    :param args:
    :return:
    """
    conf.originals = args.originals

    library_dir = None

    if args.iphoto:
        conf.source = "iPhoto"
        library_dir = args.iphoto
        library_file = "AlbumData.xml"
        library_suffix = ".photolibrary" # iPhoto library directory extension

    if args.aperture:
        conf.source = "Aperture"
        library_dir = args.aperture
        library_file = "ApertureData.xml"
        library_suffix = ".aplibrary" # Aperture library directory extension

    if library_dir: # Check that the library exists
        library_dir = os.path.expanduser(library_dir)

        if not os.path.exists(library_dir):
            # Aperture / iPhoto Library directory has an extension, which is hidden in Finder. So we check for that
            # as well
            if library_dir.endswith("/"):
                library_dir = library_dir[:-1]
            library_dir += library_suffix
            if not os.path.exists(library_dir):
                # Remove .photolibrary prefix for the error message
                logger.error("{} library is not found in {}".format(conf.source, library_dir[:-13]))
                return False

        conf.xmlsource = os.path.join(library_dir, library_file)

        #Check one more time that the actual library file exist
        if not os.path.exists(conf.xmlsource):
            logger.error("{} library file does not exist: {}".format(conf.source, conf.xmlsource))

    if args.events: conf.events = args.events
    if args.albums: conf.albums = args.albums
    if args.smarts: conf.smarts = args.smarts
    if args.exclude:
        conf.exclude = args.exclude
    else:
        conf.exclude = ""

    return True


def add_mac_arguments(parser, group):
    """
    Add command line arguments specific to OSX
    :param parser: the command line parser object
    :param group: the mutually exclusive photos source group (directory, iphoto, aperture)
    :return:
    """
    group.add_argument('--iphoto', metavar="path",
                       help='Import from iPhoto. If path is not provided, then default location is used.',
                       nargs="?", const=conf.IPHOTO_DEFAULT_PATH)

    group.add_argument('--aperture', metavar="path",
                       help='Import from Aperture. If path is not provided, then default location is used.',
                       nargs='?', const=conf.APERTURE_DEFAULT_PATH, type=str, action="store")

    parser.add_argument('-e', '--events', const=".", type=str, nargs="?", metavar="pattern",
                        help="Export matching events. The argument is a regular expression. "
                             "If the argument is omitted, then all events are exported.")
    parser.add_argument('-a', '--albums', const=".", type=str, nargs="?", metavar="pattern",
                        help="Export matching regular albums. The argument is a regular expression. "
                             "If the argument is omitted, then all events are exported.")
    parser.add_argument('-s', '--smarts', const=".", type=str, nargs="?", metavar="pattern",
                        help="Export matching smart albums. The argument is a regular expression. "
                             "If the argument is omitted, then all events are exported.")

    parser.add_argument('-x', '--exclude', metavar="pattern", type=str,
                        help="Don't export matching albums or events. The pattern is a regular expression.")


if __name__ == '__main__':
    conf.osx = (sys.platform == 'darwin')

    if conf.osx:
        import sources.iphoto as iphoto

    if parse_arguments():
        main()
    else:
        sys.exit(1)
