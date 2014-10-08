
import paramiko
import getpass
import os
import socket
import re

from conf import conf

import logging

logger = logging.getLogger(__name__)


class SSH:
    """
    This class is used to connect to remote host and copy files
    """


    def __init__(self):
        logger.setLevel(conf.verbose)
        self._authentication_tries = 0
        self._ssh = paramiko.SSHClient()
        self._ssh.load_system_host_keys()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connect()


    def connect(self, password=""):
        """
        Connect to a remote SSH server. First try to connect using system keys.
        If that fails, then prompts for a password. If that fails, then quit.
        """
        if self.isConnected:
            return
        else:
            try:
                self._ssh.connect(conf.server, username=conf.username, password=password)
                self._ftp = self._ssh.open_sftp()
                print("Connected to " + conf.server)

            except paramiko.AuthenticationException:
                self._ssh.close()

                if self._authentication_tries < 1:
                    password = getpass.getpass('Password: ')
                    self._authentication_tries += 1
                    self.connect(password)
                else:
                    raise Exception("Authentication fail.")
            except paramiko.SSHException:
                logger.info("Cannot connect to remote server. Retrying")
            except socket.gaierror:
                raise Exception("Cannot connect to server {}".format(conf.server))

    def disconnect(self):
        logger.info("Disconnected from " + conf.server)
        self._ssh.close()


    @property
    def isConnected(self):
        return self._ssh.get_transport() and self.ssh.get_transport().is_active()


    def put(self, source, destination):
        """
        Upload a file to the remote server
        """
        file_name = os.path.split(source)[-1]
        try:
            self._ftp.put(source, destination)
            logger.debug("Uploaded file " + file_name)

        except paramiko.SSHException as e:
            logger.error("Error occured while uploading file {}: {}".format(file_name, e), exc_info=True)


    def remove(self, file_name):
        """
        Remove file on the remote server
        """
        try:
            self._ftp.remove(file_name)
            logger.debug("Removed file " + file_name)
        except paramiko.SSHException as e:
            logger.error("Error occured while removing file {}: {}".format(file_name, e), exc_info=True)


    def loadDbConfig(self):
        """
        Obtain and parse database information from Lychee configuration file located in
        data/config.php
        :return True if configuration was read successfully. False otherwise
        """

        config_file = os.path.join(conf.path, "data", "config.php")
        with self._ftp.open(config_file) as f:
            for line in f:
                match = re.match("\$(\w+)\s*=\s*\'(.+)\';.*", line)

                if match:
                    key = match.group(1)
                    value = match.group(2)
                    setattr(conf, key, value)


        # Check that the all database variables were loaded from the configuration file
        keys = ['dbHost', 'dbUser', 'dbPassword', 'dbName']
        return all([key in dir(conf) for key in keys])






