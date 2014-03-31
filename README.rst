Grit
====

1 Overview
----------

Grit is a simple and light-weight git repository manager or git-compatible digital asset management 
system with limited remote object proxying, a http back-end and easy to use command line, python and 
cli user interfaces.

This is early prototype code, is missing many important features and probably won't work for you.


1.1 Features
~~~~~~~~~~~~

- Python WSGI "Smart HTTP" server
- Limited remote object proxying
- Stream blob data from remote repositories
- Hierarchical repos with top-down inheritance
- Check out individual blobs
- Python and HTTP+JSON read/write API
- Supports a centralized workflow
- Command line, Python and web UIs
- Git not required


1.2 Known Issues
~~~~~~~~~~~~~~~~

Known issues as of this release:

- Currently no support for diff, status, submodule or tag
- Poor performance with large binary files
- Can only checkout repos and blobs, not trees


1.3 Requirements
~~~~~~~~~~~~~~~~

- Python (2.6.5)
- Dulwich (0.7.0)
- Git (optional)


1.4 Noted differences from git
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- A branch in grit is different from a branch in git in that a branch is a child of a repo and inherits its files automatically. Files can be overwritten at the branch level. 
- Grit supports (limited) remote object proxying, so you can browse and get information about an object without checking it out.
- Checkouts in grit are different in that you can check out a given version (latest by default) of a repo, or a single file.


2 Installation
--------------

::

  $ pip install grit

or, download the source and ::

  $ sudo python setup.py install


2.1 Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~

The following environment variables are used, but not required. ::

  GRIT_LOG_LEVEL     logging level (default is 20)
  GRIT_SERVER_PORT   default port to run the grit server on (default is 8080)
  GRIT_STATIC_DIR    filesystem location for serving web UI elements


3 Basic Usage
-------------

::

  grit COMMAND [OPTIONS]

  Commands:

  new     make new repo at url
  co      check out files from repo at url
  ci      check in files to repo at url
  serve   serve a repo or directory of repos
  

Create a new repo
~~~~~~~~~~~~~~~~~

The “new” command creates the equivalent of a bare git repository. This “projects” repo will act as a 
starting point for creating branches later. ::

    $ grit new /tmp/projects

Using the Python API ::

    >>> from grit import Repo
    >>> r = Repo.new('/var/tmp/myrepo')
    >>> r
    <grit.Repo "/var/tmp/myrepo">
    >>> r.name
    'myrepo'
    >>> r.items()
    []
    

Serving repos
~~~~~~~~~~~~~

Start the grit server on localhost port 80 and serve the “projects” repository. ::

    $ grit serve /tmp/projects -p 80


Creating branches
~~~~~~~~~~~~~~~~~

Let’s branch some repositories off of the main “projects” repository. You can use either URLs or local 
paths here. ::

    $ grit new http://localhost/animal
    $ grit new http://localhost/animal/mammal
    $ grit new http://localhost/animal/mammal/wolf

To override any files inherited from a branch parent, simply check in a file to the branch with the same 
name. To get thumbnails in the web UI, check in an appropriate png file called “thumb.png”.


Adding files
~~~~~~~~~~~~

Currently, adding files is only supported on local repositories using grit or git itself. This is a known issue and will be addressed in a near future release. Let’s check out the “wolf” branch with git and add a file called “thumb.png”. You can also use the Python API to do this using the addItem method.

Using grit ::

    $ grit ci /tmp/projects/animal/mammal/wolf thumb.png

Using git ::

    $ git clone http://localhost/animal/mammal/wolf
    $ cd wolf
    $ git add thumb.png
    $ git commit thumb.png "adding thumb"
    $ git push

Using the Python API ::

    >>> from grit import Repo, Item
    >>> r = Repo('/tmp/projects/animal/mammal/wolf')
    >>> v = r.addVersion()
    >>> i = Item.from_path(repo=r, path='/path/to/thumb.png')
    >>> v.addItem(i)
    >>> v.save('Publishing thumbnail')
    >>> v.items()
    [<grit.Item "thumb.png">]
    >>> r.versions()
    [<grit.Version "0">, <grit.Version "1">]


Checking out repos
~~~~~~~~~~~~~~~~~~

You can use grit to checkout the latest version of a repo (with revision depth=0), including all 
of the automatically inherited files from its branch parents. ::

    $ grit co http://localhost/animal/mammal/wolf


Checking out files
~~~~~~~~~~~~~~~~~~

Also with grit, you can check out a single file if you wish. ::

    $ grit co http://localhost/animal/mammal/wolf/thumb.png


4 License
---------

See file named LICENSE for license terms governing over the entire project.

Some, explisitely labeled so constituent files/works are licensed under separate, more-permissive 
terms. See disclaimers at the start of the files for details.
