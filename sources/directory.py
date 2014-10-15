import os

from conf import *


def get_photos():
    """
    Scan photos in the provided directory and create a dictionary dict[albumname] = [photo_paths,], where
    album names correspond to folders. Sub-folders are converted to regular albums, as Lychee does not support
    sub-albums. Files in the root directory are put into the Unsorted album ("{unsorted}" is the key name).

    :return: dictionary with album names and image paths.
    """

    albums = {}
    # walk through each file / dir of the srcdir
    for root, dirs, files in os.walk(conf.dir):

        # if a there is at least one photo in the files
        if any([_isphoto(f) for f in files]):
            rel_path = os.path.relpath(root, conf.dir)

            if root == conf.dir:
                album_name = "{unsorted}"
            else:
                album_name = _get_album_name(rel_path)

            albums[album_name] = []

            for f in files:
                if _isphoto(f):
                    full_path = os.path.join(root, f)
                    albums[album_name].append(full_path)

    return albums


def _get_album_name(rel_path):
    """
    Convert folder a file resides in into an album name
    :param
    """
    return rel_path.split(os.sep)[-1]


def _isphoto(file):
    """
    Determine if a provided file is an image based on its extension
    :return: True if the file is an image. False otherwise
    """
    validimgext = ['.jpg', '.jpeg', '.gif', '.png']
    ext = os.path.splitext(file)[-1].lower()
    return (ext in validimgext)


