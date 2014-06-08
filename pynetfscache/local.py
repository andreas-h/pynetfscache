# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals

import datetime
import glob
import os
import shutil

from ._base import FilesystemCache


class LocalFilesystemCache(FilesystemCache):
    """A cache for files from the local filesystem hierarchy

    Useful for NFS mounts

    """

    def _check_init(self):
        if not os.path.isdir(self.sourcepath):
            raise ValueError("The given source path '{}' doesn't "
                             "exist".format(self.sourcepath))
        if not os.listdir(self.sourcepath):
            raise ValueError("The given source path '{}' is "
                             "empty".format(self.sourcepath))

    def _retrieve(self, path):
        temppath = self._construct_temppath(path)
        self._prepare_targetpath(path)
        shutil.copy2(self._construct_sourcepath(path), temppath)
        self._files[path] = temppath, datetime.datetime.now()
        # TODO: mote self._files[path] = ... to base class

    def glob(self, pathname):
        return glob.glob(os.path.join(self.sourcepath, pathname))

    def isdir(self, dirname):
        return os.path.isdir(self._construct_sourcepath(dirname))

    def isfile(self, filename):
        return os.path.isfile(self._construct_sourcepath(filename))

    def listdir(self, dirname):
        return os.listdir(self._construct_sourcepath(dirname))
