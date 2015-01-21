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
    High-level logic for uploading images to the remote server. The class is responsible for initiating SSH and
    database connections, checking whether albums exist and creating if needed and uploading photos to appropriate
    albums.
    """

    def __init__(self):
        logger.setLevel(conf.verbose)
        self.ssh = ssh.SSH()

        if self.ssh.loadDbConfig():
            self.dao = Database()
        else:
            raise Exception("Lychee configuration file not found. Please check the path to Lychee installation")



    def createAlbum(self, album_name):
        """
        Create a new album
        :param album_name: The name of an album to create
        :return: Album id. None if the album cannot be created
        """
        album_id = None
        if album_name != "":
            album_id = self.dao.createAlbum(album_name)

        return album_id


    def uploadPhoto(self, photo):
        """
        Upload a photo to the remote server and add it to the album it belongs to in the database. If database update
        fails for some reason, photos are deleted from the server.

        :param photo: a valid LycheePhoto object
        :return: True if everything went ok
        """
        album_name = os.path.dirname(photo.srcfullpath).split(os.sep)[-1]
        file_name = os.path.basename(photo.srcfullpath)

        try:
            thumbnail_path = os.path.join(conf.path, "uploads", "thumb")
            medium_path = os.path.join(conf.path, "uploads", "medium", photo.url)
            import_path = os.path.join(conf.path, "uploads", "import", photo.url)

            # if the big flag is set, upload the resized photo to the big directory and the original photo into the
            # import directory
            if "big_size" in dir(conf):
                self.ssh.put(photo.big_path, photo.destfullpath)

            if "upload_originals" in dir(conf):
                self.ssh.put(photo.srcfullpath, import_path)

            self.ssh.put(photo.medium_path, medium_path)
            self.ssh.put(photo.thumbnailfullpath, os.path.join(thumbnail_path, photo.url))
            self.ssh.put(photo.thumbnailx2fullpath, os.path.join(thumbnail_path, photo.thumb2xUrl))

            if self.dao.addFileToAlbum(photo):
                logger.info("Uploaded file {}/{}".format(album_name, file_name))
                return True
            else:
                self.ssh.remove(photo.destfullpath)
                self.ssh.remove(os.path.join(medium_path, photo.url))
                self.ssh.remove(os.path.join(thumbnail_path, photo.url))
                self.ssh.remove(os.path.join(thumbnail_path, photo.thumb2xUrl))

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
        :param filelist: a list of filenames to delte
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
        """
        Upload photos stored in the provided dictionary, create albums. Accept a dictionary of album names and image
        paths as input parameter and convert each image path into a LycheePhoto object, which is passed to the
        uploadPhoto funciton.
        :param albums: a dictionary with albums and path names
        """
        print("Uploading photos...")

        createdalbums, discoveredphotos, importedphotos = 0, 0, 0

        for album_name, files in albums.items():
            album_date = None
            if album_name == "{unsorted}":
                album_id = 0
            else:
                album_id = self.dao.albumExists(album_name)

            if album_id is None: # create album
                album_id = self.createAlbum(album_name)
                createdalbums += 1
            elif conf.replace: # drop album photos
                filelist = self.dao.eraseAlbum(album_id)
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
                    logger.info("Photo {}/{} already exists".format(album_name, file_name))

                if album_id:  # set correct album date
                    self.dao.updateAlbumDate(album_id, album_date)

        self.dao.close()

        # Final report
        print "{} out of {} photos imported".format(importedphotos, discoveredphotos)


