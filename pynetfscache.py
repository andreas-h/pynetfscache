# -*- coding: utf-8 -*-

from __future__ import division, unicode_literals

import datetime
import glob
import os
import shutil
import tempfile
import warnings


class FilesystemCache(object):

    def __init__(self, sourcepath, temppath=None, keep_tmp=False):
        if temppath is not None and not keep_tmp:
            warnings.warn("You specified the temppath '{}', but you also "
                          "told me to remove the temppath when we're done. "
                          "For security reasons, I assume you're wrong and I "
                          "WILL NOT DELETE the temppath.".format(temppath))
        if temppath is None:
            self.temppath = tempfile.mkdtemp()
        else:
            self.temppath = temppath
            keep_tmp = True
        self.keep_tmp = keep_tmp
        self._files = {}
        self.sourcepath = sourcepath
        self._check_init()

    def __del__(self):
        if not self.keep_tmp:
            shutil.rmtree(self.temppath)

    def __call__(self, path):
        # TODO: support path as glob
        return self._files.get(path, self.retrieve(path))[0]

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
        return os.path.join(self.temppath, os.path.dirname(path))

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
        if isinstance(path, basestring):
            self._retrieve(path)
            retval = self._files[path][0]
        elif isinstance(path, list):
            retval = []
            for p in path:
                self._retrieve(p)
                retval.append(self._files[p][0])
        else:
            raise ValueError("You passed an object of class '{}' as "
                             "path".format(path.__class__))
        return retval

    def _retrieve_single(self, path):
        pass

    def clean(self, pattern=None, time=None):
        """Selectively clean local storage

        This method selectively purges the local storage from all
        files whose relative paths match *pattern*, matching an
        additional time constraint *time* (which can be either a
        datetime.datetime or a datetime.timedelta object).

        """
        if pattern is None:
            pattern = "*"
        files_to_clean = glob.glob(os.path.join(self.temppath, pattern))

        if isinstance(time, datetime.datetime):
            t_constraint = lambda t: t < time
        elif isinstance(time, datetime.timedelta):
            t_constraint = lambda t: datetime.datetime.now() - t > time
        else:
            t_constraint = lambda t: False

        def _remove_file(relpath, abspath):
            os.remove(abspath)
            self._files.pop(relpath)
            if len(os.listdir(os.path.dirname(abspath))) == 0:
                shutil.rmtree(os.path.dirname(abspath))

        def _check_time_constraint(time, t):
            return time is None or (t_constraint(t) and time is not None)

        # iterate over local files and delete if necessary
        for relpath, (abspath, t) in self._files.items():
            if abspath in files_to_clean:
                if _check_time_constraint(time, t):
                    _remove_file(relpath, abspath)

        # iterate over files_to_clean; if it's a directory, delete this
        for f in files_to_clean:
            if os.path.isdir(f):
                for relpath, (abspath, t) in self._files.items():
                    if abspath.startswith(f):
                        if _check_time_constraint(time, t):
                            _remove_file(relpath, abspath)

    def autoclean(self):
        pass

    def glob(self, pathname):
        raise NotImplementedError()

    def isdir(self, dirname):
        raise NotImplementedError()

    def isfile(self, filename):
        raise NotImplementedError()

    def listdir(self, dirname):
        raise NotImplementedError()


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

    def glob(self, pathname):
        return glob.glob(os.path.join(self.sourcepath, pathname))

    def isdir(self, dirname):
        return os.path.isdir(self._construct_sourcepath(dirname))

    def isfile(self, filename):
        return os.path.isfile(self._construct_sourcepath(filename))

    def listdir(self, dirname):
        return os.listdir(self._construct_sourcepath(dirname))
