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


    def albumExists(self, album):
        """
        Takes an album properties list  as input. At least the relpath sould be specified (relative albumpath)
        Returns an albumid or None if album does not exists
        """

    def createAlbum(self, album_name):
        """
        Creates an album
        Inputs:
        - album: an album properties list. at least path should be specified (relative albumpath)
        Returns an albumid or None if album does not exists
        """
        album_id = None
        if album_name != "":
            album_id = self.dao.createAlbum(album_name)

        return album_id


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


    def upload(self, albums):
        print("Uploading photos...")

        createdalbums, discoveredphotos, importedphotos = 0, 0, 0

        for album, files in albums.items():
            album_date = None
            if album == "{unsorted}":
                album_id = 0
            else:
                album_id = self.dao.albumExists(album)

            if album_id is None: # create album
                album_id = self.createAlbum(album)
                createdalbums += 1
            elif conf.replace: # drop album photos
                filelist = self.dao.eraseAlbum(album)
                self.deleteFiles(filelist)

            for full_path in files:
                discoveredphotos += 1
                photo = LycheePhoto(full_path, album_id)

                if album_date is None or album_date < photo.datetime:
                    album_date = photo.datetime

                if not self.dao.photoExists(photo):
                    if self.uploadPhoto(photo):
                        importedphotos += 1
                else:
                    file_name = os.path.basename(photo.srcfullpath)
                    logger.info("Photo {}/{} already exists".format(album, file_name))

                if album_id:  # set correct album date
                    self.dao.updateAlbumDate(album_id, album_date)

        self.dao.close()

        # Final report
        print "{} out of {} photos imported".format(importedphotos, discoveredphotos)


