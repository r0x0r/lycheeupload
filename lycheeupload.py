#!/bin/python
# -*- coding: utf-8 -*-
"""
lychee upload v1.0
(C) 2014 Roman Sirokov

Imports images from a location on hard drive to the Lychee installation on a remote server via SSH.

Based on lycheesync by Gustave Paté
https://github.com/GustavePate/lycheesync

"""


import argparse
import os
import sys
import re
import logging

import upload
from conf import *


logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    try:
        u = upload.Upload()
        u.sync()
    except Exception as e:
        logger.error(e, exc_info=(conf.verbose == logging.INFO))
        sys.exit(1)


def parse_arguments():
    parser = argparse.ArgumentParser(description=("Upload all the photos in the local photo directory and its "
                                                  "sub-directories to Lychee. Directories are converted to albums."))
    parser.add_argument('server', metavar='username@hostname:path', type=str, nargs=1,
                        help='Server connection string with a full path to the directory where Lychee is installed.')
    parser.add_argument('-d', '--dir', help='path to the photo directory where to export photos from.', type=str)
    parser.add_argument('-r', '--replace', help="replace albums in Lychee with local ones", action='store_true')
    parser.add_argument('-p', '--public', help="make uploaded photos public", action='store_true')
    parser.add_argument('-v', '--verbose', help='print verbose messages', action='store_true')
    args = parser.parse_args()

    if args.dir:
        if not os.path.exists(args.dir):
            logger.error("Photo directory does not exist:" + args.dir)
            return False
        conf.srcdir = args.dir
    else:
        logger.error("Please specify a directory to export photos from")
        return False

    if args.server:
        if not parse_server_string(args.server[0]):
            logger.error("Server string must be in the username@hostname:path format")
            return False

    conf.replace = args.replace
    conf.public = args.public

    if args.verbose:
        conf.verbose = logging.INFO

    return True


def parse_server_string(server_string):
    match = re.match("(.+)@([\w\d\.]+):(.+)", server_string)

    if match:
        conf.username = match.group(1)
        conf.server = match.group(2)
        conf.path = match.group(3)

        return True
    else:
        return False


if __name__ == '__main__':
    if parse_arguments():
        main()
    else:
        sys.exit(1)
