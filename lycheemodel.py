# -*- coding: utf-8 -*-

import time
import tempfile
import hashlib
import os
import mimetypes
import logging
import datetime

from PIL import Image
from PIL.ExifTags import TAGS

from conf import conf

logger = logging.getLogger(__name__)


class ExifData:
    """
    Use to store ExifData
    """

    @property
    def takedate(self):
        """I'm the 'x' property."""
        return self._takedate.replace(':', '-')

    @takedate.setter
    def takedate(self, value):
        self._takedate = value.replace(':', '-')

    iso = ""
    aperture = ""
    make = ""
    model = ""
    shutter = ""
    focal = ""
    _takedate = ""
    taketime = ""
    orientation = 0

    def __str__(self):
        res = ""
        res += "iso: " + str(self.iso) + "\n"
        res += "aperture: " + str(self.aperture) + "\n"
        res += "make: " + str(self.make) + "\n"
        res += "model: " + str(self.model) + "\n"
        res += "shutter: " + str(self.shutter) + "\n"
        res += "focal: " + str(self.focal) + "\n"
        res += "_takedate: " + str(self._takedate) + "\n"
        res += "takedate: " + str(self.takedate) + "\n"
        res += "taketime: " + str(self.taketime) + "\n"
        res += "orientation: " + str(self.orientation) + "\n"
        return res


class LycheePhoto:
    """
    Use to store photo data
    """

    SMALL_THUMB_SIZE = (200, 200)
    BIG_THUMB_SIZE = (400, 400)

    originalname = ""  # import_name
    originalpath = ""
    id = ""
    albumname = ""
    albumid = ""
    thumbnailfullpath = ""
    thumbnailx2fullpath = ""
    title = ""
    description = ""
    url = ""
    public = 0  # private by default
    type = ""
    width = None
    height = None
    size = None
    star = 0  # no star by default
    thumb2xUrl = ""
    srcfullpath = ""
    destfullpath = ""
    exif = None
    datetime = None
    checksum = None

    def __init__(self, photoname, album):
        logger.setLevel(conf["verbose"])

        # Parameters storage
        self.originalname = photoname
        self.originalpath = album['path']
        self.albumid = album['id']
        self.albumname = album['name']

        # if star in file name, photo is starred
        if ('star' in self.originalname) or ('cover' in self.originalname):
            self.star = 1

        # Compute Photo ID
        self.id = str(time.time())
        self.id = self.id.replace('.', '')
        self.id = self.id.ljust(14, '0')

        # Compute file storage url
        m = hashlib.md5()
        m.update(self.id)
        crypted = m.hexdigest()

        ext = os.path.splitext(photoname)[1]
        self.url = ''.join([crypted, ext]).lower()
        self.thumb2xUrl = ''.join([crypted, "@2x", ext]).lower()


        # src and dest fullpath
        self.srcfullpath = os.path.join(self.originalpath, self.originalname)
        self.destfullpath = os.path.join(conf["path"], "uploads", "big", self.url)

        # Auto file some properties
        self.type = mimetypes.guess_type(self.originalname, False)[0]
        self.size = os.path.getsize(self.srcfullpath)
        self.size = str(self.size/1024) + " KB"
        self.datetime = datetime.datetime.now()

        # Exif Data Parsing
        self.exif = ExifData()
        try:

            img = Image.open(self.srcfullpath)
            self.width, self.height = img.size
            if hasattr(img, '_getexif'):
                exifinfo = img._getexif()
                if exifinfo is not None:
                    for tag, value in exifinfo.items():
                        decode = TAGS.get(tag, tag)
                        #print tag, decode, value
                        #if decode != "MakerNote":
                        #    print decode, value
                        if decode == "Orientation":
                            self.exif.orientation = value
                        if decode == "Make":
                            self.exif.make = value
                        if decode == "MaxApertureValue":
                            self.exif.aperture = value
                        if decode == "FocalLength":
                            self.exif.focal = value
                        if decode == "ISOSpeedRatings":
                            self.exif.iso = value
                        if decode == "Model":
                            self.exif.model = value
                        if decode == "ExposureTime":
                            self.exif.shutter = value
                        if decode == "DateTime":
                            self.datetime = datetime.datetime.strptime(value, '%Y:%m:%d %H:%M:%S')

                    self.description = self.datetime

        except IOError:
            logger.error("IOError", )

        self.thumbnailfullpath = self.generateThumbnail(self.SMALL_THUMB_SIZE)
        self.thumbnailx2fullpath = self.generateThumbnail(self.BIG_THUMB_SIZE)

        # Generate SHA1 hash
        self.checksum = self.generateHash(self.srcfullpath)


    def generateThumbnail(self, res):
        """
        Create the thumbnail of a given photo
        Parameters:
        - res: should be a set of h and v res (640, 480)
        Returns the fullpath of the thuumbnail
        """

        if self.width > self.height:
            delta = self.width - self.height
            left = int(delta / 2)
            upper = 0
            right = self.height + left
            lower = self.height
        else:
            delta = self.height - self.width
            left = 0
            upper = int(delta / 2)
            right = self.width
            lower = self.width + upper

        tempimage = tempfile.NamedTemporaryFile(delete=False)
        destimage = tempimage.name
        tempimage.close()

        img = Image.open(self.srcfullpath)
        img = img.crop((left, upper, right, lower))
        img.thumbnail(res, Image.ANTIALIAS)
        img.save(destimage, "JPEG", quality=99)
        return destimage

    def cleanup(self):
        """
        Delete thumbnail files
        """
        os.remove(self.thumbnailfullpath)
        os.remove(self.thumbnailx2fullpath)


    def rotatephoto(self, photo, rotation):
        # rotate main photo
        img = Image.open(photo.destfullpath)
        img2 = img.rotate(rotation)
        img2.save(photo.destfullpath, quality=99)
        # rotate Thumbnails
        img = Image.open(photo.thumbnailx2fullpath)
        img2 = img.rotate(rotation)
        img2.save(photo.thumbnailx2fullpath, quality=99)
        img = Image.open(photo.thumbnailfullpath)
        img2.rotate(rotation)
        img2.save(photo.thumbnailfullpath, quality=99)

    def adjustRotation(self, photo):
        """
        Rotates photos according to the exif orienttaion tag
        Returns nothing
        """
        if photo.exif.orientation not in (0, 1):
            # There is somthing to do
            if photo.exif.orientation == 6:
                # rotate 90° clockwise
                # AND LOOSE EXIF DATA
                self.rotatephoto(photo, -90)
            if photo.exif.orientation == 8:
                # rotate 90° counterclockwise
                # AND LOOSE EXIF DATA
                self.rotatephoto(photo, 90)


    def generateHash(self, filePath):
        sha1 = hashlib.sha1()

        with open(filePath, 'rb') as f:
            sha1.update(f.read())
            return sha1.hexdigest()


    def __str__(self):
            res = ""
            res += "originalname:" + str(self.originalname) + "\n"
            res += "originalpath:" + str(self.originalpath) + "\n"
            res += "id:" + str(self.id) + "\n"
            res += "albumname:" + str(self.albumname) + "\n"
            res += "albumid:" + str(self.albumid) + "\n"
            res += "thumbnailfullpath:" + str(self.thumbnailfullpath) + "\n"
            res += "thumbnailx2fullpath:" + str(self.thumbnailx2fullpath) + "\n"
            res += "title:" + str(self.title) + "\n"
            res += "description:" + str(self.description) + "\n"
            res += "url:" + str(self.url) + "\n"
            res += "public:" + str(self.public) + "\n"
            res += "type:" + str(self.type) + "\n"
            res += "width:" + str(self.width) + "\n"
            res += "height:" + str(self.height) + "\n"
            res += "size:" + str(self.size) + "\n"
            res += "star:" + str(self.star) + "\n"
            res += "thumbUrl:" + str(self.thumbUrl) + "\n"
            res += "srcfullpath:" + str(self.srcfullpath) + "\n"
            res += "destfullpath:" + str(self.destfullpath) + "\n"
            res += "datetime:" + self.datetime + "\n"
            res += "Exif: \n" + str(self.exif) + "\n"
            return res
