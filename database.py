# -*- coding: utf-8 -*-

import mysql.connector
import datetime
import traceback
import logging

from conf import conf

logger = logging.getLogger(__name__)

class Database:

    """
    Implements linking with Lychee DB
    """

    def __init__(self):
        """
        Takes a dictionnary of conf as input
        """
        logger.setLevel(conf.verbose)

        try:
            self.albumslist = {}
            self.db = mysql.connector.connect(host=conf.dbHost,
                                              user=conf.dbUser,
                                              passwd=conf.dbPassword,
                                              db=conf.dbName,
                                              charset='utf8',
                                              use_unicode=True)

            logger.info("Connected to database {}".format(conf.dbHost))
            self.loadAlbumList()
        except mysql.connector.Error as e:
            raise Exception("Cannot connect to database server: {}".format(conf.dbHost))


    def getAlbumMinMaxIds(self):
        """
        returns min, max album ids
        """
        min_album_query = "select min(id) from lychee_albums"
        max_album_query = "select max(id) from lychee_albums"
        try:
            min = -1
            max = -1
            cur = self.db.cursor()
            cur.execute(min_album_query)
            rows = cur.fetchall()
            for row in rows:
                min = row[0]

            cur.execute(max_album_query)
            rows = cur.fetchall()
            for row in rows:
                max = row[0]

            res = min, max
        except Exception:
            res = -1, -1
            print "getAlbumMinMaxIds", Exception
            traceback.print_exc()
        finally:
            return res


    def updateAlbumDate(self, albumid, date):
        """
        Update album date to an arbitrary date
        """
        res = True
        query = "update lychee_albums set sysstamp= '" + date.strftime('%s') + "' where id=" + str(albumid)
        try:
            cur = self.db.cursor()
            cur.execute(query)
            self.db.commit()

            logger.debug("Album {} datetime changed to: {}".format(albumid, date))
        except Exception:
            res = False
            logger.error('Failed to update album date', exc_info=True)

        finally:
            return res



    def loadAlbumList(self):
        """
        retrieve all albums in a dictionnary key=title value=id
        and put them in self.albumslist
        returns self.albumlist
        """
        # Load album list
        cur = self.db.cursor()
        cur.execute("SELECT title,id from lychee_albums")
        rows = cur.fetchall()
        for row in rows:
            self.albumslist[row[0]] = row[1]

        logger.debug(self.albumslist)

        return self.albumslist


    def albumExists(self, album_name):
        """
        Check against its name if an album exists
        Parameters:
        None or the albumid if it exists
        :param album: an album object.
        :return: album id or None if the album does not exist
        """

        if album_name and album_name in self.albumslist.keys():
            return self.albumslist[album_name]
        else:
            return None


    def photoExists(self, photo):
        """
        Check if an album exists based on its original name
        Parameter:
        - photo: a valid LycheePhoto object
        Returns a boolean
        """
        res = False
        try:
            query = ("select * from lychee_photos where album='" + str(photo.albumid) +
                     "' and title = '" + photo.originalname + "'")
            cur = self.db.cursor()
            cur.execute(query)
            row = cur.fetchall()
            if len(row) != 0:
                res = True

        except Exception:
            print "ERROR photoExists:", photo.srcfullpath, "won't be added to lychee"
            traceback.print_exc()
            res = True
        finally:
            return res


    def createAlbum(self, album_name):
        """
        Creates an album
        Parameter:
        - album: the album properties list, at least the name should be specified
        Returns the created albumid or None
        """
        id = None
        query = "INSERT INTO lychee_albums (title, sysstamp, public, password) " \
                "VALUES ('{}', '{}', '{}', NULL)".format(album_name,
                                                         datetime.datetime.now().strftime('%s'),
                                                         conf.public)
        try:
            cur = self.db.cursor()
            cur.execute(query)
            self.db.commit()

            query = "select id from lychee_albums where title='" + album_name + "'"
            cur.execute(query)
            row = cur.fetchone()
            self.albumslist['name'] = row[0]
            id = row[0]

            logger.info("Album {} created".format(album_name))

        except Exception:
            logger.error('Failed to create album #{} {}'.format(id, album_name), exc_info=True)
            id = None
        finally:
            return id


    def eraseAlbum(self, id):
        """
        Deletes all photos of an album but don't delete the album itself
        Parameters:
        - album: the album properties list to erase.  At least its id must be provided
        Return list of the erased photo url
        """
        query = "delete from lychee_photos where album = " + id + ''
        selquery = "select url from lychee_photos where album = " + id + ''

        file_list = []
        try:
            cur = self.db.cursor()
            cur.execute(selquery)
            rows = cur.fetchall()
            for row in rows:
                file_list.append(row[0])
            cur.execute(query)
            self.db.commit()
            logger.info("Album #{} deleted.".format(id))

            return file_list
        except Exception:
            logger.error('Failed to delete album #{}'.format(id), exc_info=True)

            return None



    def addFileToAlbum(self, photo):
        """
        Add a photo to an album
        Parameter:
        - photo: a valid LycheePhoto object
        Returns a boolean
        """
        try:
            query = ("insert into lychee_photos " +
                     "(id, url, public, type, width, height, " +
                     "size, star, " +
                     "thumbUrl, album, iso, aperture, make, " +
                     "model, shutter, focal, takestamp, " +
                     "description, title, checksum, medium) " +
                     "values " +
                     "({}, '{}', {}, '{}', {}, {}, " +
                     "'{}', {}, " +
                     "'{}', '{}', '{}', '{}', '{}', " +
                     "'{}', '{}', '{}', '{}', " +
                     "'{}', '{}', '{}', {})"
                     ).format(photo.id, photo.url, conf.public, photo.type, photo.width, photo.height,
                              photo.size, photo.star,
                              photo.url, photo.albumid, photo.exif.iso, photo.exif.aperture, photo.exif.make,
                              photo.exif.model, photo.exif.shutter, photo.exif.focal, photo.datetime.strftime("%s"),
                              photo.description, photo.originalname, photo.checksum, 1)

            cur = self.db.cursor()
            cur.execute(query)
            self.db.commit()

            return True
        except Exception as e:
            logger.error("Inserting photo {} into database failed".format(photo.id), exc_info=True)

            return False


    def close(self):
        """
        Close DB Connection
        Returns nothing
        """
        if self.db:
            self.db.close()

