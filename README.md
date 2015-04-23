# Lychee Upload
A command line tool for uploading photos in a directory or from iPhoto/Aperture libraries to a [Lychee](http://github.com/electerious/Lychee) installation on a remote server via SSH.
Based on [lycheesync](https://github.com/GustavePate/lycheesync) by Gustave Paté and [Phoshare](https://code.google.com/p/phoshare/) by Google. 


# Description

Performs a batch image import from a location on hard drive or from an iPhoto/Aperture library to the Lychee installation on a remote server via SSH. When importing from a directory, subdirectories are automatically converted to Lychee albums. As Lychee does not support sub-albums, photos in subsubdirectories are uploaded to the respective album. Photos in the root directory are uploaded to the Unsorted album. In the iPhoto/Aperture mode you can specify what to export. Possible options are events, albums and smart albums.
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
`sudo pip install --allow-external mysql-connector-python mysql-connector-python`
`sudo pip install paramiko Pillow`


# Usage

`python lycheeupload.py [-h] [-d DIR] [-r] [-p] [-v] username@hostname:path`

General options

- `username@hostname:path` Server connection string with a full path to the directory where Lychee is installed. 
-  `-h`, `--help`            Show a help message
-  `-r`, `--replace`         Replace albums in Lychee with local ones
-  `-p`, `--public`          Make uploaded photos public
-  `-P`, `--port`            Alternative SSH port (default 22)
-  `-v`, `--verbose`         Print verbose messages
- `--medium`                 Maximum size for medium sized pictures. 1920px by default.
- `--big`                    Maximum size for big sized pictures. By default pictures are untouched.
- `--originals`              Upload original untouched files. To be used with the --big option, otherwise ignored. Files are place inside import directory. Note that this option is not currently supported by Lychee and is useful if you want to reduce the size of your big pictures, while still preserving originals.

Directory import options

-  `-d DIR`, `--dir DIR`     path to the photo directory where to export photos from.

iPhoto / Aperture options

-  `--iphoto [path]`         Import from iPhoto. If path is not provided, then default location is used.
-  `--aperture [path]`       Import from Aperture. If path is not provided, then default location is used.
-  `-e [pattern]`, `--events [pattern]` Export matching events. The argument is a regular expression. If the argument is omitted, then all events are exported.
-  `-a [pattern]`, `--albums [pattern]` Export matching regular albums. The argument is a regular expression. If the argument is omitted, then all events are exported.
-  `-s [pattern]`, `--smarts [pattern]` Export matching smart albums. The argument is a regular expression. If the argument is omitted, then all events are exported.
-  `-x pattern`, `--exclude pattern` Don't export matching albums or events. The pattern is a regular expression.

At very least you must specify a connection string and a source where photos should be imported from (`--dir`, `--iphoto` or `--aperture` options). 

For example to import photos from the directory */home/user/photos/* to the remote server *example.com* with Lychee installed in the */home/user/mydomain.com/* directory, issue the following command

`python lycheeupload.py -d /home/user/photos/ user@example.com:/home/user/mydomain.com/`

Import all events from the default iPhoto library location (~/Pictures/iPhoto Library)

`python lycheeupload.py --iphoto --events user@example.com:/home/user/mydomain.com/`

Import all the albums starting with the word "Summer" from the Aperture library located in *~/Pictures/My Aperture Library*

`python lycheeupload.py --aperture "~/Pictures/My Aperture Library" --albums "Summer.*" user@example.com:/home/user/mydomain.com/`





# Licence

[MIT License](./LICENSE)

Parts of the program are licensed under the Apache License 2.0
