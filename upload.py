# -*- coding: utf-8 -*-

import os
import logging
import ssh

from database import Database
from photo import LycheePhoto
from conf import conf

logger = logging.getLogger(__name__)


class Upload:
    """
    This class contains the logic behind this program
    It consist mainly in filesystem operations
    It relies on:
    - LycheeDAO for dtabases operations
    - LycheePhoto to store (and compute) photos propreties
    """

    def __init__(self):
        logger.setLevel(conf.verbose)
        self.ssh = ssh.SSH()

        if self.ssh.loadDbConfig():
            self.dao = Database()
        else:
            raise Exception("Lychee configuration file not found. Please check the path to Lychee installation")


    def getAlbumNameFromPath(self, album):
        """
        build a lychee compatible albumname from an albumpath (relative to the srcdir main argument)
        Takes an album properties list  as input. At least the path sould be specified (relative albumpath)
        Returns a string, the lychee album name
        """

        album['name'] = album['relpath'].split(os.sep)[-1]
        return album['name']

    def isAPhoto(self, file):
        """
        Determine if the filename passed is a photo or not based on the file extension
        Takes a string  as input (a file name)
        Returns a boolean
        """
        validimgext = ['.jpg', '.jpeg', '.gif', '.png']
        ext = os.path.splitext(file)[-1].lower()
        return (ext in validimgext)

    def albumExists(self, album):
        """
        Takes an album properties list  as input. At least the relpath sould be specified (relative albumpath)
        Returns an albumid or None if album does not exists
        """

    def createAlbum(self, album):
        """
        Creates an album
        Inputs:
        - album: an album properties list. at least path should be specified (relative albumpath)
        Returns an albumid or None if album does not exists
        """
        album['id'] = None
        album['name'] = self.getAlbumNameFromPath(album)
        if album['name'] != "":
            album['id'] = self.dao.createAlbum(album)

        return album['id']


    def uploadPhoto(self, photo):
        """
        add a file to an album, the albumid must be previously stored in the LycheePhoto parameter
        Parameters:
        - photo: a valid LycheePhoto object
        Returns True if everything went ok
        """
        album_name = os.path.dirname(photo.srcfullpath).split(os.sep)[-1]
        file_name = os.path.basename(photo.srcfullpath)

        try:
            thumbnailPath = os.path.join(conf.path, "uploads", "thumb")

            # upload photo
            self.ssh.put(photo.srcfullpath, photo.destfullpath)
            self.ssh.put(photo.thumbnailfullpath, os.path.join(thumbnailPath, photo.url))
            self.ssh.put(photo.thumbnailx2fullpath, os.path.join(thumbnailPath, photo.thumb2xUrl))

            if self.dao.addFileToAlbum(photo):
                logger.info("Uploaded file {}/{}".format(album_name, file_name))
                return True
            else:
                self.ssh.remove(photo.destfullpath)
                self.ssh.remove(os.path.join(thumbnailPath, photo.url))
                self.ssh.remove(os.path.join(thumbnailPath, photo.thumb2xUrl))

                return False

            # delete thumbnails
            photo.cleanup()

            return True
        except Exception:
            logger.error("Uploading photo {}/{} failed".format(album_name, file_name))

            return False


    def deleteFiles(self, filelist):
        """
        Delete files in the Lychee file tree (uploads/big and uploads/thumbnails)
        Give it the file name and it will delete relatives files and thumbnails
        Parameters:
        - filelist: a list of filenames
        Returns nothing
        """

        for url in filelist:
            if self.isAPhoto(url):
                thumbpath = os.path.join(conf.path, "uploads", "thumb", url)
                filesplit = os.path.splitext(url)
                thumb2path = ''.join([filesplit[0], "@2x", filesplit[1]]).lower()
                thumb2path = os.path.join(conf.path, "uploads", "thumb", thumb2path)
                bigpath = os.path.join(conf.path, "uploads", "big", url)

                self.ssh.remove(thumbpath)
                self.ssh.remove(thumb2path)
                self.ssh.remove(bigpath)


    def sync(self):
        """
        Program main loop
        Scans files to add in the sourcedirectory and add them to Lychee
        according to the conf file and given parameters
        Returns nothing
        """

        print("Uploading photos...")

        # Load db
        createdalbums = 0
        discoveredphotos = 0
        importedphotos = 0
        album = {}
        # walkthrough each file / dir of the srcdir
        for root, dirs, files in os.walk(conf.srcdir):

            # Init album data
            album['id'] = None
            album['name'] = None
            album['path'] = None
            album['relpath'] = None  # path relative to srcdir
            album['date'] = None

            # if a there is at least one photo in the files
            if any([self.isAPhoto(f) for f in files]):
                album['path'] = root
                album['relpath'] = os.path.relpath(album['path'], conf.srcdir)
                album['name'] = self.getAlbumNameFromPath(album)

                if album['path'] == conf.srcdir:
                    album['id'] = 0  # photos in the root, go to unsorted
                else:
                    album['id'] = self.dao.albumExists(album)

                if album['id'] is None:
                    # create album
                    album['id'] = self.createAlbum(album)
                    createdalbums += 1
                elif album['id'] and conf.replace:
                    # drop album photos
                    filelist = self.dao.eraseAlbum(album)
                    self.deleteFiles(filelist)

                # Albums are created or emptied, now take care of photos
                for f in files:
                    if self.isAPhoto(f):

                        discoveredphotos += 1
                        photo = LycheePhoto(f, album)

                        if album['date'] is None or album['date'] < photo.datetime:
                            album['date'] = photo.datetime

                        if not self.dao.photoExists(photo):
                            if self.uploadPhoto(photo):
                                importedphotos += 1
                        else:
                            file_name = os.path.basename(photo.srcfullpath)
                            logger.info("Photo {}/{} already exists".format(album['name'], file_name))

                if album['id']:  # set correct album date
                    self.dao.updateAlbumDate(album['id'], album["date"])

        self.dao.close()

        # Final report
        print "{} out of {} photos imported".format(importedphotos, discoveredphotos)
