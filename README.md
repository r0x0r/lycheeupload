# Lychee Upload
A command line tool for uploading photos on a hard drive to a [Lychee](http://github.com/electerious/Lychee) installation on a remote server via SSH.
Based on [lycheesync](https://github.com/GustavePate/lycheesync) by Gustave Paté


# Description

Performs a batch image import from a location on hard drive to the Lychee installation on a remote server via SSH. Subdirectories are automatically converted to Lychee albums. As Lychee does not support sub-albums, photos in subsubdirectories are uploaded to the respective album. Photos in the root directory are uploaded to the Unsorted album.
If you want to replace albums in the Lychee database, then you can use *-r* option. All photos in the existing album will be deleted in the Lychee database and replaced with new ones from the hard drive location.

# Installation

First retrieve project either by downloading it from here or if you have git installed, then checkout the project

`git clone https://github.com/r0x0r/lycheeupload`

Install the following 

- Python 2.7
- mysql-connector-python
- paramiko
- Pillow

## Debian based Linux

`sudo apt-get install imagemagick python python-paramiko python-imaging python-mysql.connector git`

## OSX

Installing dependencies on OSX is a bit trickier.

First you have to have Command Line Tools for Xcode installed. Go to [Downloads for Apple developers](http://developer.apple.com/downloads/index.action), download and install Command Line Tools for Xcode.

Install *pip* if you do not have it already

`sudo easy_install pip`

Finally install dependencies using *pip*

`sudo pip install mysql-connector-python paramiko Pillow`


# Usage

`python lycheeupload.py [-h] [-d DIR] [-r] [-p] [-v] username@hostname:path 

- `username@hostname:path` Server connection string with a full path to the directory where Lychee is installed. 
-  `-h`, `--help`            show a help message
-  `-d DIR`, `--dir DIR`     path to the photo directory where to export photos from.
-  `-r`, `--replace`         replace albums in Lychee with local ones
-  `-p`, `--public`          make uploaded photos public
-  `-v`, `--verbose`         print verbose messages

For example to import photos from the directory */home/user/photos/* to the remote server *example.com* with Lychee installed in the */home/user/mydomain.com/* directory, issue the following command

`python lycheeupload.py -d /home/user/photos/ user@example.com:/home/user/mydomain.com/`



# Licence

[MIT License](./LICENSE)
