# -*- coding: utf-8 -*-

from __future__ import division, unicode_literals

import datetime
import glob
import os
import shutil
import tempfile


class FilesystemCache(object):

    def __init__(self, sourcepath, temppath=None, keep_tmp=False):
        if temppath is None:
            self.temppath = tempfile.mkdtemp()
        else:
            self.temppath = temppath
        self.keep_tmp = keep_tmp
        self.files = {}
        self.sourcepath = sourcepath

    def __del__(self):
        if self.keep_tmp:
            shutil.rmtree(self.temppath)

    def __call__(self, path):
        # TODO: support path as glob
        return self.files.get(path, self.retrieve(path))[0]

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_type is not None:
            self.keep_tmp = True  # don't cleanup in case of Exception

    def _construct_sourcepath(self, filename):
        return os.path.join(self.sourcepath, filename)

    def _construct_temppath(self, filename):
        return os.path.join(self.temppath, filename)

    def _construct_temptargetdir(self, path):
        return os.path.join(self.temppath, os.path.split(path)[0])

    def _prepare_targetpath(self, path):
        targetdir = self._construct_temptargetdir(path)
        try:
            os.makedirs(targetdir)
        except OSError as err:
            if err.errno == 17:
                pass
            else:
                raise

    def retrieve(self, path):
        """Retrieve files from remote storage

        This method retrieves the file with relative path *path* from
        the remote storage and returns the filename to local storage

        """
        raise NotImplementedError("Method must be implemented in child class")

    def clean(self, pattern):
        """Selectively clean local storage

        This method selectively purges the local storage from all files whose
        relative paths match *pattern*.

        .. note:: Currently, this will only delete files, not directories

        """
        raise NotImplementedError()

    def autoclean(self):
        pass

    def glob(self, dirname):
        raise NotImplementedError()

    def isdir(self, dirname):
        raise NotImplementedError()

    def isfile(self, filename):
        raise NotImplementedError()

    def listdir(self, filename):
        raise NotImplementedError()


class LocalFilesystemCache(FilesystemCache):
    """A cache for files from the local filesystem hierarchy

    Useful for NFS mounts

    """

    def __init__(self, sourcepath, temppath=None, keep_tmp=False):
        FilesystemCache.__init__(self, sourcepath, temppath, keep_tmp)

    def retrieve(self, path):
        temppath = self._construct_temppath(path)
        self._prepare_targetpath(path)
        shutil.copy2(self._construct_sourcepath(path), temppath)
        self.files[path] = temppath, datetime.datetime.now()
        return self.files[path]

    #def glob(self, pathname):
    #    return glob.glob(self._construct_sourcepath(pathname))

    def isdir(self, dirname):
        return os.path.isdir(self._construct_sourcepath(dirname))

    def isfile(self, filename):
        return os.path.isfile(self._construct_sourcepath(filename))

    def listdir(self, dirname):
        return os.listdir(self._construct_sourcepath(dirname))
