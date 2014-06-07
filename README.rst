pynetfscache
============

A Python module to cache remote files locally.


What is *pynetfscache*?
-----------------------

*pynetfscache* is an implementation of a simple local cache for
network filesystems.  Currently, only a ``LocalFilesystemCache`` is
implemented, caching files which are accessible with regular
filesystem calls, but potentially via network (e.g., NFS) mounts.  In
the future, the possibility to add filesystem caches for ssh/rsync and
FTP connections are planned.



Why *pynetfscache*?
-------------------

I regularly have to run expensive calculations, on data stored in lots
of large files.  Most often, these files are not stored on the same
machine I'm running the calculations on.  Sometimes, the files can be
accessed via NFS mounts, other times the remote filesystem is not
reachable directly.

Directly accessing data files via NFS mounts is prohibiting speedwise
(plus, your network administrator will probably tell you it's a bad
idea to do so), and it is advisable to cache the files locally in
order to perform calculations with the data.


A word of caution
-----------------

While I'm using the ``LocalFilesystemCache`` class in my everyday
work, its test coverage is pretty good, and I haven't been running
into serious problems yet, you should be careful when using this
module.  *pynetfscache* is still very young, and potentially
disastrous bugs cannot be totally ruled out (and messing with the
filesystem can easily become disastrous).


Future directions
-----------------

Your critique, ideas, and contributions are very welcome!  Ultimately,
it might be nice to extend this litte project with a FUSE_ filesystem
wrapper, via fusepy_.  This_ post might be a good starting point.

.. _FUSE: http://fuse.sourceforge.net/
.. _fusepy: https://github.com/terencehonles/fusepy
.. _This: http://www.stavros.io/posts/python-fuse-filesystem/
