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

First you have to have Command Line Tools for Xcode installed. Go to [Downloads for Apple developers](http://developer.apple.com/downloads/index.action). Download and install Command Line Tools for Xcode.

Install *pip* if you do not have it already

`sudo easy_install pip`

Finally install dependencies using *pip*

`sudo pip install mysql-connector-python paramiko Pillow`

# Configuration

Add configuration details in *conf.json*

```json
{
    "server":"ssh_server_address",
    "username":"username",
    "password":"ssh_password_can_be_left_blank",
    "path":"/remote_path_to_lychee_installation/",
    "db":"db_name",
    "dbUser":"db_username",
    "dbPassword":"db_password",
    "dbHost":"db_host_name",
    "thumbQuality":80,
    "publicAlbum": 0
}
```

SSH password can be left blank, as LycheeUpload tries to use SSH keys present in the system for authentication. If that fails, it will prompt to enter a password upon connecting.

To make albums public, change publicAlbum to 1.


# Usage


`python main.py src_dir [-r] [-c alternative_conf_file] [-v]`

- `src_dir` - source directory with photos you want to upload to Lychee
- `-r` - Replace mode. Albums that already exist in Lychee will be replaced with local ones
- `-c alternative_conf_file` - Path to an alternative configuration file. By default *conf.json* is used.
- `-v` - Verbose mode. LycheeUpload will report that it is doing. By default only errors are displayed.


# Changelog

## 0.9
- First version


# Licence

[MIT License](./LICENSE)
