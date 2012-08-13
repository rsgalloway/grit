Grit
====

1 Overview
----------

Grit is a simple and light-weight git repository manager or git-compatible digital asset management 
system with limited remote object proxying, a http back-end and easy to use command line, python and 
cli user interfaces.

.. note:: This is early prototype code, is missing many important features and probably won't work for you.

Documentation: http://rsgalloway.github.com/grit

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

  $ easy_install grit

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


4 License
---------

See file named LICENSE for license terms governing over the entire project.

Some, explisitely labeled so constituent files/works are licensed under separate, more-permissive 
terms. See disclaimers at the start of the files for details.
