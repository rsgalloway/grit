#!/usr/bin/env python
#
# Copyright (C) 2011-2012 Ryan Galloway (ryan@rsgalloway.com)
#
# This module is part of Grit and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php

import os
import re
import traceback
import simplejson as json
from time import time
from datetime import datetime

import dulwich
from dulwich.objects import Blob, Commit, parse_timezone

from grit.util import serialize, deserialize, is_tree
from grit.log import log
from grit.exc import *

class ItemsMixin:
    """mixin class for handling items"""
    def _get_tree(self):
        return self.__tree

    def _set_tree(self, tree):
        self.__tree = tree

    tree = property(_get_tree, _set_tree)

    def addFile(self, path, msg=""):
        """Adds a file to the version"""
        item = Item.from_path(repo=self.repo, path=path)
        self.addItem(item)

    def addItem(self, item):
        """Adds an item if the tree is mutable"""
        try:
            self.tree.addItem(item)
        except AttributeError, e:
            raise VersionError('Saved versions are immutable')

    def removeItem(self, item):
        """Removes an item if the tree is mutable"""
        try:
            self.tree.removeItem(item)
        except AttributeError, e:
            raise VersionError('Saved versions are immutable')

    def iteritems(self):
        """Generator that yields Items"""
        if self.type in ['blob']:
            raise StopIteration

        for path, mode, sha in self.tree.iteritems():
            item = Item(self, sha, path, mode)
            yield item
            for i in item.iteritems():
                yield i

    #TODO: move path arg to iteritems, items() returns only local items
    def items(self, path=None):
        """
        Returns set of items.

        :param path: Regex filter on item path.

        :return: List of Item class objects.
        """
        items = list(self.iteritems())
        if path is not None:
            path += '$'
            regex = re.compile(path)
            items = [i for i in items if regex.match(i.path)]
        return items

class Item(object, ItemsMixin):

    def __init__(self, parent, sha, path, mode=0100644):
        """
        Create a new Item instance, wrapper around SHA object.

        :param parent: Repo, Version or Tree object.
        :param sha: A Blob or Tree sha id.
        :param path: Relative path to item.
        :param mode: Filesystem mode.

        :returns: repo.Item instance.
        """
        self.blob = None
        self.parent = parent
        self.path = os.path.join(getattr(parent, 'path', ''), path)
        self.id = sha
        self.mode = mode
        self.name = os.path.basename(path)
        self.type = self._get_type()
        self.user = getattr(self.parent, 'author', None)
        self.comment = getattr(self.parent, 'message', None)
        self.date = getattr(self.parent, 'date', None)

        # do not run get_object on blobs on init
        if self.type == 'tree':
            self.tree = self.repo.get_object(self.id)

    def __repr__(self):
        return '<grit.Item "%s">' %(self.path)

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.id == other.id

    def __getattr__(self, key):
        return getattr(self.parent, key, None)

    def _get_type(self):
        if is_tree(self.mode):
            return 'tree'
        else:
            return 'blob'

    def _get_blob(self):
        """read blob on access only because get_object is slow"""
        if not self.__blob:
            self.__blob = self.repo.get_object(self.id)
        return self.__blob

    def _set_blob(self, blob):
        self.__blob = blob
        if blob:
            self.id = blob.id

    blob = property(_get_blob, _set_blob)

    @property
    def size(self):
        return self.blob.raw_length()

    @property
    def log(self):
        self.parent.repo.git.log('--oneline', '--', self.path)

    @classmethod
    def from_path(self, repo, path, name=None):
        """
        Create a new Item from a file path.

        :param repo: Repo object.
        :param path: File path.
        :param name: Name of item (to override original file name).

        :return: New Item class instance.
        """
        if name is None:
            name = os.path.basename(path)
        #FIXME: hack, there has to be a better way
        return Item.from_string(repo=repo, name=name, string=open(path).read())

    @classmethod
    def from_string(self, repo, name, string):
        """
        Create a new Item from a data stream.

        :param repo: Repo object.
        :param name: Name of item.
        :param data: Data stream.

        :return: New Item class instance.
        """
        try:
            log.debug('Creating new item: %s' % name)
            blob = Blob.from_string(string)
            item = Item(parent=repo, sha=blob.sha, path=name)
            item.blob = blob
            return item
        except AssertionError, e:
            raise ItemError(e)

    def file(self):
        """:return: File-like StringIO object"""
        from StringIO import StringIO
        return StringIO(self.data())

    def data(self):
        """:return: blob data"""
        return self.blob.data

    def setData(self, data):
        self.blob.data = data

    def save(self, msg=None):
        """
        Modify item data and commit to repo. 
        Git objects are immutable, to save means adding a new item

        :param msg: Commit message.
        """
        if msg is None:
            msg = 'Saving %s' % self.name
        log.debug(msg)
        self.repo.addItem(self, msg)

    def checkout(self, path):
        """
        Check out file data to path.

        :param path: Filesystem path to check out item to.

        :return: True if successful.
        """
        if os.path.isdir(path):
            path = os.path.join(path, self.name)
        try:
            log.debug('Checking out %s to %s' %(self.path, path))
            f = open(path, 'w')
            f.write(self.data())
            f.close()
            return True
        except Exception, e:
            raise ItemError(e)

    def versions(self, rev=None, index=None):
        """:return: List of Versions for this Item"""
        raise NotImplementedError
        _revisions = [line.split()[0] for line in self.log.split('\n') if line]
        _versions = [Version(self.obj.repo.commit(r)) for r in _revisions if rev is None or r.startswith(rev)]
        if index is not None and len(_versions) > index:
            _versions = _versions[index]
        return _versions

    def serialize(self):
        d = self.__dict__
        d['desc'] = self.comment
        if self.parent and self.parent.repo:
            d['parent'] = self.parent.repo.name
        return serialize(d)

    def deserialize(self, params):
        deserialize(self, params)

class Tree(dulwich.objects.Tree):
    """
    Special mutable tree class for new versions.
    """
    def __init__(self):
        """
        Creates a new Tree object for storing blobs.

        :param tree: Tree instance.

        :return: New Tree instance.
        """
        super(Tree, self).__init__()
        self.type == 'tree'
        self.__items = {}

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return '<grit.Tree "%s">' %(self.id)

    def __iter__(self):
        return iter(self.__items)

    def clear(self):
        self.removeItems([item for item in self])

    def items(self):
        return self.__items.values()

    def addItem(self, item):
        super(Tree, self).add(item.mode, item.name, item.id)
        self.__items[item.name] = item

    def removeItem(self, item):
        del self._entries[item.name]
        del self.__items[item.name]

class Version(object, ItemsMixin):

    def __init__(self, repo, commit, tree=None):
        """
        Create a new Version instance.

        :param commit: A dulwich.objects.Commit object.

        :return: repo.Version instance.
        """
        self.repo = repo
        self.commit = commit
        self.name = self.commit.id
        self.type = 'version'
        self.user = str(self.commit.author)
        self.comment = str(self.commit.message)
        self.date = datetime.utcfromtimestamp(self.commit.commit_time)

        if tree is None:
            try:
                self.tree = self.repo.get_object(self.commit.tree)
            except KeyError:
                self.tree = None
        else:
            self.tree = tree

    def __str__(self):
        return str(self.commit.id)

    def __repr__(self):
        return '<grit.Version "%s">' % self.version

    def __eq__(self, other):
        return self.id == getattr(other, 'id', str(other))

    def __getattr__(self, key):
        return getattr(self.commit, key)

    @property
    def version(self):
        """:return: Version number / index in list of versions"""
        try:
            return self.repo._commits().index(self.commit)
        except ValueError:
            return None

    def _get_parent(self):
        return self.repo.versions(-1)

    def _set_parent(self, version):
        self.commit.parents = [version.id]

    parent = property(_get_parent, _set_parent)

    def save(self, message):
        """
        Add version to repo object store, set repo head to version sha.

        :param message: Message string.
        """
        self.commit.message = message
        self.commit.tree = self.tree
        #TODO: store new blobs only
        for item in self.tree.items():
            self.repo.object_store.add_object(item.blob)
        self.repo.object_store.add_object(self.tree)

        # set HEAD to new commit
        self.repo.object_store.add_object(self.commit)
        self.repo.refs['refs/heads/master'] = self.commit.id

    @classmethod
    def new(self, repo):
        """
        Create a new version of a repo.Local object.

        :param repo: Instance of repo.Local.

        :return: New Version instance.
        """
        #TODO: subclass Commit, pass parent as init param
        try:
            # create new commit instance and set metadata
            commit = Commit()
            author = os.environ.get('USER')
            commit.author = commit.committer = author
            commit.commit_time = commit.author_time = int(time())
            tz = parse_timezone('-0200')[0]
            commit.commit_timezone = commit.author_timezone = tz
            commit.encoding = "UTF-8"
            commit.message = ''

            # set previous version as parent to this one
            parent = repo.versions(-1)
            if parent:
                commit.parents = [parent.id]

            # create new tree, add entries from previous version
            tree = Tree()
            curr = repo.versions(-1)
            if curr:
                for item in curr.items():
                    tree.addItem(item)
            commit.tree = tree.id

            # create new version, and add tree
            version = Version(repo=repo, commit=commit, tree=tree)
            return version

        except Exception, e:
            traceback.print_exc()
            return VersionError(e)

    def checkout(self, path=None):
        raise NotImplementedError

    def serialize(self):
        d = self.__dict__
        d['desc'] = self.comment
        return serialize(d)

    def deserialize(self, params):
        return deserialize(params)
