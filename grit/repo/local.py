#!/usr/bin/env python
#
# Copyright (C) 2011-2012 Ryan Galloway (ryan@rsgalloway.com)
#
# This module is part of Grit and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php

import os
import re
import time
import tempfile
import traceback
from datetime import datetime

from dulwich.repo import Repo
from dulwich.objects import Blob, Tree, Commit

from grit.repo import Proxy
from grit.repo import Item, Version
from grit.util import touch, is_git_dir
from grit.util import serialize, deserialize
from grit.cmd import Git
from grit.exc import *
from grit.log import log

__all__ = ['is_repo', 'get_repos', 'get_repo_parent', 'Local']

def is_repo(path):
    """:return: True if path is a valid repository"""
    return is_git_dir(path)

def get_repos(path):
    """
    Returns list of found branches.

    :return: List of grit.Local objects
    """
    p = str(path)
    ret = []
    if not os.path.exists(p):
        return ret
    for d in os.listdir(p):
        pd = os.path.join(p, d)
        if os.path.exists(pd) and is_repo(pd):
            ret.append(Local(pd))
    return ret

def get_repo_parent(path):
    """
    Returns parent repo or input path if none found.

    :return: grit.Local or path
    """
    # path is a repository
    if is_repo(path):
        return Local(path)

    # path is inside a repository
    elif not os.path.isdir(path):
        _rel = ''
        while path and path != '/':
            if is_repo(path):
                return Local(path)
            else:
                _rel = os.path.join(os.path.basename(path), _rel)
                path = os.path.dirname(path)
        return path

class Local(Repo):
    """Local repository class."""

    def __init__(self, path=None):
        """
        Create a new repo.Local instance.

        :param path: local path to valid git repository. 

        :returns: repo.Local instance.
        """
        path = os.path.abspath(os.path.expandvars(os.path.expanduser(path or os.getcwd())))

        if not os.path.exists(path):
            raise RepoError('Invalid path: %s' % path)

        curpath = path
        while curpath:
            if is_git_dir(curpath):
                self.git_dir = curpath
                self._working_tree_dir = os.path.dirname(curpath)
                break
            gitpath = os.path.join(curpath, '.git')
            if is_git_dir(gitpath):
                self.git_dir = gitpath
                self._working_tree_dir = curpath
                break
            curpath, dummy = os.path.split(curpath)
            if not dummy:
                break

        if not is_repo(self.git_dir):
            raise RepoError('Invalid path: %s' % path)

        super(Local, self).__init__(self.git_dir)
        self.name = os.path.basename(path)
        self.path = path
        self.abspath = os.path.abspath(self.path)
        self.user = self.author
        self.comment = self.message
        self.type = "local"
        self.is_bare = self.bare

    def __str__(self):
        return str(self.path)

    def __repr__(self):
        return '<grit.Local "%s">' % self.path

    def __getattr__(self, key, *args, **kwargs):
        return getattr(self.versions(-1), key, None)

    def _get_parent(self):
        """:return: Remote origin as Proxy instance"""
        _dir = os.path.dirname(self.path)
        if is_repo(_dir):
            return Local(_dir)
        else:
            return None

    def _set_parent(self):
        raise NotImplementedError

    parent = property(_get_parent, _set_parent)

    def isLocal(self):
        return True

    @property
    def git(self):
        """git command object"""
        return Git(self.git_dir)(*args, **kwargs)

    @property
    def date(self):
        """:return: datetime object"""
        if self.commit_time:
            return datetime.utcfromtimestamp(self.commit_time)
        else:
            return datetime.now()

    def addVersion(self):
        """
        Creates a new Version, to which Items can be added and removed, and
        committed.

        :return: New Version instance.
        """
        return Version.new(self)

    def setVersion(self, version):
        """
        Checkout a version of the repo.

        :param version: Version number.
        """
        try:
            sha = self.versions(version).commit.sha
            self.git.reset("--hard", sha)
        except Exception, e:
            raise RepoError(e)

    def _commits(self, head='HEAD'):
        """Returns a list of the commits reachable from head.

        :return: List of commit objects. the first of which will be the commit
        of head, then following theat will be the parents.

        :raise: RepoError if any no commits are referenced, including if the
        head parameter isn't the sha of a commit.
        """
        pending_commits = [head]
        history = []
        while pending_commits != []:
            head = pending_commits.pop(0)
            try:
                commit = self[head]
            except KeyError:
                raise KeyError(head)
            if type(commit) != Commit:
                raise TypeError(commit)
            if commit in history:
                continue
            i = 0
            for known_commit in history:
                if known_commit.commit_time > commit.commit_time:
                    break
                i += 1
            history.insert(i, commit)
            pending_commits += commit.parents
        return history

    def versions(self, version=None):
        """
        List of Versions of this repository.

        :param version: Version index.
        :param rev: Commit sha or ref.

        :return: List of Version objects matching params.
        """
        try:
            versions = [Version(self, c) for c in self._commits()]
        except Exception, e:
            log.debug('No versions exist')
            return []
        if version is not None and versions:
            try:
                versions = versions[version]
            except IndexError:
                raise VersionError('Version %s does not exist' % version)
        return versions

    def getDescription(self):
        """:returns: repository description"""
        try:
            return self.get_named_file('description').read()
        except Exception, e:
            raise RepoError(e)

    def setDescription(self, desc='No description'):
        """sets repository description"""
        try:
            self._put_named_file('description', desc)
        except Exception, e:
            raise RepoError(e)

    def tag(self, name, message=None):
        raise NotImplementedError

    def tags(self):
        raise NotImplementedError

    def delete(self):
        os.system('rm -rf %s' % self.abspath)

    @classmethod
    def new(self, path, desc=None, bare=True):
        """
        Create a new bare repo.Local instance.

        :param path: Path to new repo.
        :param desc: Repo description.
        :param bare: Create as bare repo.

        :returns: New repo.Local instance.
        """
        if os.path.exists(path):
            raise RepoError('Path already exists: %s' % path)
        try:
            os.mkdir(path)
            if bare:
                Repo.init_bare(path)
            else:
                Repo.init(path)
            repo = Local(path)
            if desc:
                repo.setDescription(desc)
            version = repo.addVersion()
            version.save('Repo Initialization')
            return repo
        except Exception, e:
            traceback.print_exc()
            raise RepoError('Error creating repo')

    def branch(self, name, desc=None):
        """
        Create a branch of this repo at 'name'.

        :param name: Name of new branch
        :param desc: Repo description.

        :return: New Local instance.
        """
        return Local.new(path=os.path.join(self.path, name), desc=desc, bare=True)

    def addFile(self, path, msg=None):
        """add a new file(s)"""
        item = Item.from_path(repo=self, path=path)
        self.addItem(item, msg)

    def addItem(self, item, message=None):
        """add a new Item class object"""
        if message is None:
            message = 'Adding item %s' % item.path
        try:
            v = Version.new(repo=self)
            v.addItem(item)
            v.save(message)
        except VersionError, e:
            raise RepoError(e)

    def iteritems(self):
        pass

    #TODO: move path arg to iteritems, items() returns only local items
    def items(self, path=None, version=None):
        """
        Returns a list of items.

        :param path: Regex filter on item path.
        :param version: Repo versions number/index.

        :return: List of Item class objects.
        """
        if version is None:
            version = -1
        items = {}
        for item in self.versions(version).items():
            items[item.path] = item
        parent = self.parent

        # get latest committed items from parents
        while parent:
            for item in parent.items(path=path):
                if item.path not in items.keys():
                    items[item.path] = item
            parent = parent.parent

        # filter items matching path regex
        if path is not None:
            path += '$'
            regex = re.compile(path)
            return [item for path, item in items.items() if regex.match(path)]
        else:
            return items.values()

    def addSubmodule(self, url, name=None, path=None):
        raise NotImplementedError

    def submodules(self, name=None):
        raise NotImplementedError

    def data(self):
        raise NotImplementedError

    def pull(self):
        self.git.pull('-s', 'ours')

    def push(self):
        self.git.push('origin', 'master')

    def serialize(self):
        d = self.__dict__
        d['desc'] = self.getDescription()
        d['date'] = self.date
        if self.parent and self.parent.repo:
            d['parent'] = self.parent.repo.name
        return serialize(d)

    def deserialize(self, params):
        deserialize(self, params)
