#!/usr/bin/env python
#
# Copyright (C) 2011-2012 Ryan Galloway (ryan@rsgalloway.com)
#
# This module is part of Grit and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php

import os
import sys
import urllib
import simplejson as json

from grit.repo import Local
from grit.repo import is_repo, get_repos
from grit.repo.version import Item
from grit.util import serialize
from grit.exc import *
from grit.log import log

__doc__ = """
This module contains server handler functions.
"""

def handle_read(repo, **kwargs):
    """handles reading repo information"""
    log.info('read: %s %s' %(repo, kwargs))
    if type(repo) in [unicode, str]:
        return {'name': 'Repo', 'desc': 'Welcome to Grit', 'comment': ''}
    else:
        return repo.serialize()

def handle_new(path, **kwargs):
    """:return: new repo.Local instance"""
    log.info('new: %s %s' %(path, kwargs))
    repo = Local.new(path=path, **kwargs)
    return repo.serialize()

def handle_branch(repo, **kwargs):
    """:return: Local.create()"""
    log.info('branch: %s %s' %(repo, kwargs))
    if type(repo) in [unicode, str]:
        path = os.path.join(repo, kwargs.get('name', 'Unnamed'))
        desc = kwargs.get('desc')
        branch = Repo.new(path=path, desc=desc, bare=True)
    else:
        name = kwargs.get('name')
        path = kwargs.get('path')
        if path and not name:
            name = os.path.basename(path)
        desc = kwargs.get('desc')
        branch = repo.branch(name=name, desc=desc)
    return branch.serialize()

def handle_delete(repo, **kwargs):
    log.info('delete: %s %s' %(repo, kwargs))
    return repo.delete(**kwargs)

def handle_repos(repo, **kwargs):
    log.info('repos: %s %s' %(repo, kwargs))
    repos = get_repos(getattr(repo, 'abspath', repo))
    return [r.serialize() for r in repos]

def handle_items(repo, **kwargs):
    """:return: repo.files()"""
    log.info('items: %s %s' %(repo, kwargs))
    if not hasattr(repo, 'items'):
        return []
    return [i.serialize() for i in repo.items(**kwargs)]

def handle_addItem(repo, **kwargs):
    """:return: repo.addItem()"""
    log.info('addItem: %s %s' %(repo, kwargs))

def handle_tags(repo, **kwargs):
    """:return: repo.tags()"""
    log.info('tags: %s %s' %(repo, kwargs))
    return [str(t) for t in repo.tags(**kwargs)]

def handle_versions(repo, **kwargs):
    """:return: repo.versions()"""
    log.info('versions: %s %s' %(repo, kwargs))
    if not hasattr(repo, 'versions'):
        return []
    return [v.serialize() for v in repo.versions(**kwargs)]

def handle_submodules(repo, **kwargs):
    """:return: repo.submodules()"""
    log.info('submodules: %s %s' %(repo, kwargs))
    return [serialize(s, type='submodule', url=s.url) for s in repo.submodules(**kwargs)]

def handle_addSubmodule(repo, **kwargs):
    """:return: repo.addSubmodule()"""
    log.info('addSubmodule: %s %s' %(repo, kwargs))
    try:
        proxy = repo.addSubmodule(**kwargs)
        return [serialize(proxy, type='submodule', url=proxy.url)]
    except RepoError, e:
        raise

def handle_addVersion(repo, **kwargs):
    """:return: repo.addSubmodule()"""
    log.info('addVersion: %s %s' %(repo, kwargs))
    try:
        v = repo.addVersion(**kwargs)
        return v.serialize()
    except RepoError, e:
        raise

def handle_parent(repo, **kwargs):
    """:return: repo.parent()"""
    log.info('parent: %s %s' %(repo, kwargs))
    _parent = repo.parent()
    if _parent:
        return [_parent.serialize()]

def handle_upload(repo, **kwargs):
    """
    :param kwargs: valud kwargs
         filename: file name
         filedata: file data
    :return: new Item
    """
    log.info('upload: %s' %(repo))
    name = kwargs.get('filename', 'Untitled')
    data = kwargs.get('filedata')
    repo.addItem(Item.from_string(repo=repo, name=name, string=data))
