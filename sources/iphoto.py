#!/usr/bin/env python
"""Reads iPhoto library info, and produces a dictionary of albums and image paths."""

#  Copyright 2014 Roman Sirokov
#  Copyright 2010 Google Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import re
from sources.appledata import iphotodata
from conf import *

logger = logging.getLogger(__name__)



class IphotoLibrary(object):
    """The class that represents iPhoto / Aperture library"""

    def __init__(self, aperture, xml_file, exclude, originals):
        self.data = iphotodata.get_iphoto_data(xml_file)
        self.exclude = exclude
        self.originals = originals
        self._abort = False
        self.exported_photos = {}

        if aperture:
            self.data.load_aperture_originals()

        logger.setLevel(conf.verbose)


    def abort(self):
        """Signal that a currently running export should be aborted as soon as possible.
        """
        self._abort = True


    def _check_abort(self):
        if self._abort:
            print "Export cancelled."
            return True
        return False


    def export_events(self, pattern):
        """ Export events according to a regex pattern.
        :param pattern: Regex pattern. Use "." to export all events
        :return: Dictionary of albums and image paths
        """
        return self._process_albums(self.data.root_album.albums, ["Event"], pattern)


    def export_albums(self, pattern):
        """ Export albums according to a regex pattern.
        :param pattern: Regex pattern. Use "." to export all albums
        :return: Dictionary of albums and image paths
        """
        return self._process_albums(self.data.root_album.albums, ["Regular", "Published"], pattern)


   # def export_facealbums(self):
   #     return self._process_albums(self.data.getfacealbums(), ["Face"], ".")


    def export_smartalbums(self, pattern):
        """ Export smart albums according to a regex pattern.
        :param pattern: Regex pattern. Use "." to export all smart albums
        :return: Dictionary of albums and image paths
        """
        return self._process_albums(self.data.root_album.albums, ["Smart"], pattern)



    def _process_albums(self, albums, album_types, include, matched=False):
        """
        The workhorse method of the class. Process iPhoto library files and produce a dictionary of albums and image
        paths. Since albums can contain other albums, this method is called recursively to process all the data in the
        library
        :param albums: The root of data, from which the search of photos begins
        :param album_types: A list of album types to export. Possible values are ["Event", "Regular", "Published",
                            "Smart"]
        :param include: A Regex pattern of album names to match
        :param matched: Flag indicating that the album is matched
        :return: a dictionary of album names and image paths
        """
        exclude_pattern = None
        if conf.exclude:
            exclude_pattern = re.compile(unicode(self.exclude))

        include_pattern = re.compile(include)

         # first, do the sub-albums
        for sub_album in albums:
            if self._check_abort():
                return
            sub_name = sub_album.name
            if not sub_name:
                print "Found an album with no name: " + sub_album.albumid
                sub_name = "{unsorted}"

            # check the album type
            if sub_album.albumtype == "Folder" or sub_album.albums:
                sub_matched = matched
                if include_pattern.match(sub_name):
                    sub_matched = True

                self._process_albums(sub_album.albums, album_types, include, sub_matched)
                continue
            elif (sub_album.albumtype == "None" or
                  not sub_album.albumtype in album_types):
                # print "Ignoring " + sub_album.name + " of type " + \
                # sub_album.albumtype
                continue

            if not matched and not include_pattern.match(sub_name):
                logger.debug(u'Skipping "%s" because it does not match pattern.', sub_name)
                continue

            if exclude_pattern and exclude_pattern.match(sub_name):
                logger.debug(u'Skipping "%s" because it is excluded.', sub_name)
                continue

            logger.debug(u'Loading "%s".', sub_name)

            # first, do the sub-albums
            self._process_albums(sub_album.albums, album_types, include, matched) > 0
            # now the album itself
            if self.originals:
                self.exported_photos[sub_name] = [image.originalpath or image.image_path for image in sub_album.images]
            else:
                self.exported_photos[sub_name] = [image.image_path for image in sub_album.images]

        return self.exported_photos



def get_photos():
    """
    Get images from the iPhoto / Aperture library. Parameters are read from the global configuration
    :return: a dictionary of album names and image paths
    """

    def add_albums(pattern, export_photos):
        """
        A helper function that exports photos from the library and resolves name conflicts before adding albums to the
        export dictionary
        :param pattern: A Regex pattern of album names to match
        :param export_photos: a dictionary, which exported photos are added to
        :return:
        """
        photos = library.export_albums(pattern)

        for key in set(photos) & set(export_photos): # Check that keys do not conflict
            logger.debug("Conflicting album found {}".format(key))
            index = 1
            while True:
                new_key = key + u" ({})".format(index)
                if new_key in export_photos:
                    index += 1
                else:
                    break

            photos[new_key] = photos.pop(key)

        export_photos.update(photos)
        return export_photos

    library = IphotoLibrary(conf.source == "Aperture", conf.xmlsource, conf.exclude, conf.originals)

    print "Scanning iPhoto data for photos to export..."
    export_photos = {}
    if "events" in dir(conf):
        export_photos = library.export_events(conf.events)

    if "albums" in dir(conf):
        export_photos = add_albums(conf.albums, export_photos)

    if "smarts" in dir(conf):
        export_photos = add_albums(conf.smarts, export_photos)

    if "facealbums" in dir(conf):
        photos = library.export_facealbums()
        export_photos.update(photos)

    return export_photos

