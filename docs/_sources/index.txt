.. Grit documentation master file, created by
   sphinx-quickstart on Sat Mar 12 19:28:34 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=======================
Grit v0.1 documentation
=======================

Grit is a simple and light-weight git repository manager or git-compatible digital 
asset management system with limited remote object proxying, a http back-end and
easy to use command line, python and web user interfaces. 

.. note:: This is early prototype code, is missing many important features and probably won't work for you

*Features*

- Python WSGI "Smart HTTP" server
- Limited remote object proxying
- Stream blob data from remote repositories
- Hierarchical repos with top-down inheritance
- Check out individual blobs
- Python and HTTP+JSON read/write API
- Supports a centralized workflow
- Command line, Python and web UIs
- Git not required

*Some noted differences from git*

- A branch in grit is different from a branch in git in that a branch is a child of a repo and inherits its files automatically. Files can be overwritten at the branch level. 
- Grit supports (limited) remote object proxying, so you can browse and get information about an object without checking it out.
- Checkouts in grit are different in that you can check out a given version (latest by default) of a repo, or a single file.

*Known issues as of this release*

- Currently no support for diff, status, submodule or tag
- Renaming a repo breaks external references
- Items tab shows flat list of items, not heirarchical
- Checking in files over HTTP is broken (use git instead)
- Poor performance with large binary files
- Can only checkout repos and blobs, not trees
- Blobs lack icons in the web UI
- Parent links in web UI are broken

Get Grit
========

Installing Grit is easily done using
`setuptools`_. Assuming it is
installed, just run the following from the command-line:

.. sourcecode:: none

    $ easy_install grit

- `setuptools`_
- `install setuptools <http://peak.telecommunity.com/DevCenter/EasyInstall#installation-instructions>`

.. _setuptools: http://peak.telecommunity.com/DevCenter/setuptools

Alternatively, you can install from the distribution using the ``setup.py``
script:

.. sourcecode:: none

    $ git clone https://github.com/rsgalloway/grit.git
    $ python setup.py install

Requirements
************

Python and the following Python packages are required for Grit to work. Currently, git is required for 
checking in files and some operations like clone.

- Python (2.6.5)
- Dulwich (0.7.0)
- Git (optional)

Tutorial
========

This is a simple tutorial using the command line interface for grit. The Python API is documented below. 
Note that grit is git-compatible, so you can also use git for many operations albiet with different
syntax. 

Create a new repo
*****************

The `new` command creates the equivalent of a bare git repository. This "projects" repo will act as a
starting point for creating branches later.  ::

    $ grit new /tmp/projects

Serving repos
*************

Start the grit server on localhost port 80 and serve the "projects" repository.
::

    $ grit serve /tmp/projects -p 80

Creating branches
*****************

Let's branch some repositories off of the main "projects" repository. You can use either URLs or local paths here. ::

    $ grit new http://localhost/animal
    $ grit new http://localhost/animal/mammal
    $ grit new http://localhost/animal/mammal/wolf

To override any files inherited from a branch parent, simply check in a file to the branch with the same name. 
To get thumbnails in the web UI, check in an appropriate png file called "thumb.png".

Adding files
************

Using grit, checkin a file to a remote repo ::

    $ grit ci http://locahost/animal/mammal/wolf thumb.png

... or to a local repo ::

    $ grit ci /tmp/projects/animal/mammal/wolf thumb.png

Using Python ::

    >>> from grit import Repo
    >>> r = Repo('/tmp/projects/animal/mammal/wolf')
    >>> r.addFile('/path/to/thumb.png', 'Publishing thumbnail')

Adding multiple items to the same version ::

    >>> from grit import Repo, Item
    >>> v = r.addVersion()
    >>> v.addFile(path='/path/to/fileA')
    >>> v.addFile(path='/path/to/fileB')
    >>> v.save('Publishing files')

Using git ::

    $ git clone http://localhost/animal/mammal/wolf
    $ cd wolf
    $ git add thumb.png
    $ git commit thumb.png "adding thumb"
    $ git push


Checking out repos
******************

You can use grit to checkout the latest version of a repo (with revision depth=0), including all of the automatically inherited files from its branch parents. ::

    $ grit co http://localhost/animal/mammal/wolf

Checking out files
******************

Also with grit, you can check out a single file if you wish. ::

    $ grit co http://localhost/animal/mammal/wolf/thumb.png


API Reference
=============

The following API docs cover the major classes.

.. toctree::
   :maxdepth: 2

.. automodule:: grit
   :members:

Repo
****

.. autoclass:: Repo
   :members: __init__, new, clone

Local
*****

.. autoclass:: Local
   :members:

Proxy
*****

.. autoclass:: Proxy
   :members:

Item
****

.. autoclass:: Item
   :members:

Version
*******

.. autoclass:: Version
   :members:

Server
******

.. autoclass:: Server
   :members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`

