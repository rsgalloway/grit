#!/usr/bin/env python
#
# Copyright (C) 2011-2012 Ryan Galloway (ryan@rsgalloway.com)
#
# This module is part of Grit and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php

import os
import sys
import stat

def touch(filename):
    fp = open(filename, 'a')
    fp.close()

def is_git_dir(d):
    if os.path.isdir(d) and \
            os.path.isdir(os.path.join(d, 'objects')) and \
            os.path.isdir(os.path.join(d, 'refs')):
        headref = os.path.join(d, 'HEAD')
        return os.path.isfile(headref) or \
                (os.path.islink(headref) and
                os.readlink(headref).startswith('refs'))
    return False

def is_tree(mode):
    if mode is None:
        return False
    return stat.S_ISDIR(mode)

def serialize(d):
    """
    Attempts to serialize values from a dictionary, 
    skipping private attrs.

    :param d: A dictionary of params to serialize, 
            typically cls.__dict__
    """
    ret = {}
    for k,v in d.items():
        if not k.startswith('_'):
            ret[k] = str(d[k])
    #ret['__class__'] = obj.__class__.__name__
    return ret

def deserialize(params):
    cls = params.get('__class__').capitalize()
    exec("from repo import %s; obj = %s.deserialize(params)" %(cls, cls))
    return obj

def user_config(**kwargs):
    """
    Initialize Git user config file.

    :param kwargs: key/value pairs are stored in the git user config file.
    """
    for kw in kwargs:
        git('config --global user.%s "%s"' %(kw, kwargs.get(kw))).wait()
