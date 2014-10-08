__author__ = 'roman'

import json
import logging


class Conf:
    pass

conf = Conf()
conf.verbose = logging.ERROR


def load_conf(conf_file):
    loaded_conf = json.load(open(conf_file, 'r'))

    for key, value in loaded_conf.items():
        setattr(conf, key, value)


