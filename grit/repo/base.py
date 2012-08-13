#!/usr/bin/env python
#
# Copyright (C) 2011-2012 Ryan Galloway (ryan@rsgalloway.com)
#
# This module is part of Grit and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php

import os
import sys
from datetime import datetime

from dulwich.errors import NotGitRepository

from grit.repo import Local, Proxy
from grit.repo import Item, Version
from grit.cmd import Git
from grit.exc import *
from grit.log import log

class Repo(object):

    def __init__(self, url):
        """
        Creates a new Repo instance. Most method and attribute calls are passed
        to the underlying repo object, which is either an instance of repo.Local
        or repo.Proxy, which is a proxy representation of a Local object served
        by the wsgi server.

        :param url: HTTP URL or file path.

        :returns: New repo.Repo instance.

        For example:

            >>> r = Repo('http://localhost/projects/myrepo')

        or

            >>> r = Repo('/tmp/myrepo')

        Either way, you can make the same method and attribute calls:

            >>> r.name
            'myrepo'
            >>> r.setDescription(desc='my project repository')
            >>> r.versions()
            >>> r.items()
            >>> f = r.items(path='relative/path/to/file')

        """
        self.url = url
        self.git = Git()
        self._set_repo(url)

    def __str__(self):
        return str(self.url)

    def __repr__(self):
        return '<grit.Repo "%s">' %(self.url)

    def __eq__(self, other):
        return str(self.repo.id) == str(other.repo.id)

    def __getattr__(self, key, *args, **kwargs):
        if hasattr(self.repo, key):
            try:
                return getattr(self.repo, key)
            except RepoError, e:
                raise GritError(e)
            except ProxyError, e:
                raise GritError(e)

    def _set_repo(self, url):
        """sets the underlying repo object"""
        if url.startswith('http'):
            try:
                self.repo = Proxy(url)
            except ProxyError, e:
                log.exception('Error setting repo: %s' % url)
                raise GritError(e)
        else:
            try:
                self.repo = Local(url)
            except NotGitRepository:
                raise GritError('Invalid url: %s' % url)
            except Exception, e:
                log.exception('Error setting repo: %s' % url)
                raise GritError(e)

    @classmethod
    def new(self, url, clone_from=None, bare=True):
        """
        Creates a new Repo instance.

        :param url: Path or remote URL of new repo.
        :param clone_from: Path or URL of repo to clone from.
        :param bare: Create as bare repo.

        :returns: grit.Repo instance.

        For example:

            >>> r = Repo.new('/tmp/projects')
            >>> r
            <grit.Repo "/tmp/projects">

        """
        #note to self: look into using templates (--template)
        if clone_from:
            self.clone(path=url, bare=bare)
        else:
            if url.startswith('http'):
                proxy = Proxy(url)
                proxy.new(path=url, bare=bare)
            else:
                local = Local.new(path=url, bare=bare)
        return Repo(url)

    def clone(self, path=None, bare=False):
        """
        Clone the repository to path (requires git).

        :param path: Destination filesystem path.
        :param bare: Make this a bare repo.

        :returns: grit.Repo instance.

        For example:

            >>> r = Repo("http://localhost/projects/a/b/c")
            >>> c = r.clone('/tmp')
            >>> c
            <grit.Repo "/tmp/c">

        """
        #note to self: see --reference, --shared options
        if path is None:
            path = os.path.basename(url)
        try:
            self.git.clone(self.url, path, '--bare'*bare, '--depth=0')
            return Repo(path)
        except Exception, e:
            raise GritError(e)

