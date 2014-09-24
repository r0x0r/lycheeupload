#!/bin/python
# -*- coding: utf-8 -*-
"""
lychee upload
v0.9
2014 Roman Sirokov

Imports images from a location on hard drive to the Lychee installation on a remote server via SSH.

Based on lycheesync by Gustave Paté
https://github.com/GustavePate/lycheesync

"""


import argparse
import os
import sys
import logging

import lycheesyncer
from conf import *


logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    try:
        s = lycheesyncer.LycheeSyncer()
        s.sync()
    except Exception as e:
        logger.error(e)
        sys.exit(1)


if __name__ == '__main__':
    #Parse arguments
    parser = argparse.ArgumentParser(description=("Export all photos in the local photo directory" +
                                                  " recursively to Lychee. Directories are converted to albums."))
    parser.add_argument('srcdir', help='Path to photo directory', type=str)
    parser.add_argument('-c', '--conf', help='Path to configuration file. If not provided, then conf.json is used.', type=str)
    parser.add_argument('-r', '--replace', help="Replace albums in Lychee with local ones", action='store_true')
    parser.add_argument('-v', '--verbose', help='Increase output verbosity', action='store_true')
    args = parser.parse_args()

    error = False

    if not os.path.exists(args.srcdir):
        error = True
        logger.error("Photo directory does not exist:" + args.dir)

    conf_file = CONF_FILE
    if args.conf is not None:
        conf_file = args.conf

    if not os.path.exists(conf_file):
        error = True
        logger.error("Configuration file does not exist: " + conf_file)
    else:
        load_conf(conf_file)

    if conf["server"] == "ssh_server_address":
        logger.error("Please edit the configuration file {} first".format(conf_file))
        error = True

    if args.verbose:
        conf["verbose"] = logging.INFO

    if error:
        sys.exit(1)

    conf["srcdir"] = args.srcdir
    conf["replace"] = args.replace

    main()
