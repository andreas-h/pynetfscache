#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals

import datetime
import os
import shutil
import tempfile
import time
import unittest
import warnings

from pynetfscache import LocalFilesystemCache


def _touch(path, createdirs=False):
    if createdirs:
        basedir = os.path.dirname(path)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
    with open(path, 'a'):
        os.utime(path, None)


class TestLocalFilesystemCache(unittest.TestCase):
    def setUp(self):
        self.remotebase = tempfile.mkdtemp()
        self.localbase = tempfile.mkdtemp()
        _touch(os.path.join(self.remotebase, "fileA"))
        _touch(os.path.join(self.remotebase, "dirA", "fileA"), createdirs=True)

    def tearDown(self):
        shutil.rmtree(self.remotebase)
        shutil.rmtree(self.localbase)

    def test_initialize(self):
        c = LocalFilesystemCache(self.remotebase)

    def test_do_teardown(self):
        c = LocalFilesystemCache(self.remotebase)
        tmppath = c.temppath
        del c
        self.assertFalse(os.path.isdir(tmppath))

    def test_init_warn_arguments(self):
        # see http://stackoverflow.com/a/3892301 to assert warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")  # always trigger all warnings
            c = LocalFilesystemCache(self.remotebase, self.localbase)
            self.assertTrue(str(w[-1].message).find("I WILL NOT DELETE") > -1)
            self.assertTrue(issubclass(w[-1].category, UserWarning))
        del c

    def test_donot_teardown(self):
        c = LocalFilesystemCache(self.remotebase, keep_tmp=True)
        tmppath = c.temppath
        del c
        self.assertTrue(os.path.isdir(tmppath))
        shutil.rmtree(tmppath)

    def test_retrieve_file(self):
        c = LocalFilesystemCache(self.remotebase)
        tmppath = c.temppath
        t0 = datetime.datetime.now()
        lpath = c.retrieve("fileA")
        t1 = datetime.datetime.now()
        self.assertTrue(t0 < c._files["fileA"][1] < t1)
        del c

    def test_retrieve_file_list(self):
        c = LocalFilesystemCache(self.remotebase)
        tmppath = c.temppath
        c.retrieve(["fileA", os.path.join("dirA", "fileA")])
        self.assertTrue(os.path.isfile(c("fileA")))
        self.assertTrue(os.path.isfile(c(os.path.join("dirA", "fileA"))))
        del c

    def test_retrieve_file_notfound(self):
        c = LocalFilesystemCache(self.remotebase)
        tmppath = c.temppath
        with self.assertRaises(IOError) as cm:
            c.retrieve("fileB")
        self.assertEqual(cm.exception.errno, 2)
        del c

    def test_retrieve_file_call(self):
        c = LocalFilesystemCache(self.remotebase)
        tmppath = c.temppath
        lpath = c.retrieve("fileA")
        self.assertEqual(lpath, c("fileA"))
        del c

    def test_retrieve_file_time(self):
        c = LocalFilesystemCache(self.remotebase)
        tmppath = c.temppath
        lpath = c.retrieve("fileA")
        self.assertTrue(os.path.isfile(os.path.join(tmppath, "fileA")))
        self.assertEqual(lpath, os.path.join(tmppath, "fileA"))
        del c

    def test_retrieve_dir(self):
        c = LocalFilesystemCache(self.remotebase)
        tmppath = c.temppath
        lpath = c.retrieve(os.path.join("dirA", "fileA"))
        self.assertTrue(os.path.isfile(os.path.join(tmppath, "dirA", "fileA")))
        self.assertEqual(lpath, os.path.join(tmppath, "dirA", "fileA"))
        del c

    def test_clean_all(self):
        c = LocalFilesystemCache(self.remotebase)
        tmppath = c.temppath
        c.retrieve(["fileA", os.path.join("dirA", "fileA")])
        c.clean()
        self.assertEqual(os.listdir(c.temppath), [])
        self.assertEqual(c._files, {})
        del c

    def test_clean_pattern(self):
        c = LocalFilesystemCache(self.remotebase)
        tmppath = c.temppath
        c.retrieve(["fileA", os.path.join("dirA", "fileA")])
        c.clean("f*")
        self.assertEqual(os.listdir(c.temppath), ["dirA"])
        self.assertEqual(c._files.keys(), [os.path.join("dirA", "fileA")])
        del c

    def test_clean_datetime(self):
        c = LocalFilesystemCache(self.remotebase)
        tmppath = c.temppath
        t0 = datetime.datetime.now()
        c.retrieve("fileA")
        time.sleep(0.5)
        t1 = datetime.datetime.now()
        c.retrieve(os.path.join("dirA", "fileA"))
        time.sleep(0.5)
        c.clean(time=t0 + datetime.timedelta(microseconds=100))
        self.assertEqual(os.listdir(c.temppath), ["dirA"])
        self.assertEqual(c._files.keys(), [os.path.join("dirA", "fileA")])
        del c

    def test_clean_timedelta(self):
        c = LocalFilesystemCache(self.remotebase)
        tmppath = c.temppath
        t0 = datetime.datetime.now()
        c.retrieve("fileA")
        time.sleep(0.5)
        t1 = datetime.datetime.now()
        c.retrieve(os.path.join("dirA", "fileA"))
        time.sleep(0.5)
        timedelta = ((datetime.datetime.now() - t0) +
                     datetime.timedelta(microseconds=10))
        c.clean(time=timedelta)
        self.assertEqual(os.listdir(c.temppath), ["dirA"])
        self.assertEqual(c._files.keys(), [os.path.join("dirA", "fileA")])
        del c

    def test_glob(self):
        def _abspath(filenames):
            return [os.path.join(self.remotebase, p) for p in filenames]
        c = LocalFilesystemCache(self.remotebase)
        actual = c.glob("*")
        required = _abspath(["fileA", "dirA"])
        actual.sort(), required.sort()
        self.assertEqual(actual, required)
        actual = c.glob("f*")
        required = _abspath(["fileA"])
        self.assertEqual(actual, required)
        actual = c.glob("F*")
        required = _abspath([])
        self.assertEqual(actual, required)
        del c

    def test_isdir(self):
        c = LocalFilesystemCache(self.remotebase)
        self.assertTrue(c.isdir("dirA"))
        self.assertFalse(c.isdir("fileA"))
        self.assertFalse(c.isdir(os.path.join("dirA", "fileA")))
        del c

    def test_isdir(self):
        c = LocalFilesystemCache(self.remotebase)
        self.assertFalse(c.isfile("dirA"))
        self.assertTrue(c.isfile("fileA"))
        self.assertTrue(c.isfile(os.path.join("dirA", "fileA")))
        del c

    def test_listdir(self):
        c = LocalFilesystemCache(self.remotebase)
        actual = c.listdir("")
        required = ["fileA", "dirA"]
        actual.sort(), required.sort()
        self.assertEqual(actual, required)
        del c


if __name__ == '__main__':
    unittest.main()
