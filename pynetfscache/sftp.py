# -*- coding: utf-8 -*-

from __future__ import division, unicode_literals

import datetime
import stat

try:
    import paramiko
    _PARAMIKO = True
except ImportError:
    _PARAMIKO = False

from ._base import FilesystemCache


class SFTPFilesystemCache(FilesystemCache):
    """A cache for files retrieved via SFTP.

    This makes use of the paramiko library

    """

    def __init__(self, sourcepath, hostname, user, port=22, password=None,
                 ssh_id=None, ssh_hostkey=None, ssh_unknown_hosts=False,
                 temppath=None, keep_tmp=False):
        if not _PARAMIKO:
            raise ImportError("Cannot import paramiko, which is needed for "
                              "SFTPFilesystemCache")
        self._hostname = hostname
        self._username = user
        self._password = password
        # TODO: ssh_id checken
        # TODO: ssh_agent
        self._ssh_id = None
        self._port = port
        self._ssh = paramiko.SSHClient()
        self._ssh.load_system_host_keys()
        if ssh_hostkey is not None:
            self._ssh.load_host_keys(ssh_hostkey)
        if ssh_unknown_hosts:
            self._ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
        else:
            self._ssh.set_missing_host_key_policy(paramiko.RejectPolicy())
        # TODO: persistently connect
        super(SFTPFilesystemCache, self).__init__(sourcepath, temppath,
                                                  keep_tmp)

    def __del__(self):
        self._disconnect()
        super(SFTPFilesystemCache, self).__del__()

    def _connect(self):
        # TODO: check if connection already exists
        self._ssh.connect(self._hostname, self._port, self._username,
                          self._password, key_filename=self._ssh_id,
                          compress=True)
        self._sshtransport = self._ssh.get_transport()
        self._sftp = paramiko.SFTPClient.from_transport(self._sshtransport)

    def _disconnect(self):
        try:
            self._sftp.close()
        except:
            pass
        try:
            self._sshtransport.close()
        except:
            pass
        try:
            self._ssh.close()
        except:
            pass

    def _check_init(self):
        self._connect()
        self._sftp.listdir(".")
        self._disconnect()

    def _retrieve(self, path):
        raise NotImplementedError()
        temppath = self._construct_temppath(path)
        self._prepare_targetpath(path)
        self._files[path] = temppath, datetime.datetime.now()

    def glob(self, pathname):
        raise NotImplementedError()

    def isdir(self, dirname):
        self._connect()
        st = self._sftp.stat(self._construct_sourcepath(dirname))
        self._disconnect()
        return stat.S_ISDIR(st.st_mode)

    def isfile(self, filename):
        self._connect()
        st = self._sftp.stat(self._construct_sourcepath(filename))
        self._disconnect()
        return stat.S_ISREG(st.st_mode)

    def listdir(self, dirname):
        self._connect()
        result = self._sftp.listdir(self._construct_sourcepath(dirname))
        self._disconnect()
        return result
