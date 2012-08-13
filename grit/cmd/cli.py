#!/usr/bin/env python
#
# Copyright (C) 2011-2012 Ryan Galloway (ryan@rsgalloway.com)
#
# This module is part of Grit and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php

import os
import sys
import shutil
from datetime import datetime

from grit.log import log
from grit.exc import *

# -----------------------------------------------------------------------------
def confirm(prompt=None, resp=False):
    """
    Prompts user for confirmation.

    :param prompt: String to display to user.
    :param resp: Default response value.

    :return: Boolean response from user, or default value.
    """
    if prompt is None:
        prompt = 'Confirm'

    if resp:
        prompt = '%s [%s]|%s: ' % (prompt, 'y', 'n')
    else:
        prompt = '%s [%s]|%s: ' % (prompt, 'n', 'y')

    while True:
        ans = raw_input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'n', 'N']:
            print 'please enter y or n.'
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False

def prompt(name, default):
    """
    Prompts user for raw input.

    :return: Raw input value from user.
    """
    value = raw_input('%s [%s]: ' %(name, default))
    if not value:
        value = default
    return value

def new(url):
    """
    Creates a new Repo class instance at url.

    :param url: URL of new repo

    :return: new Repo class instance.
    """
    from grit import Repo
    return Repo.new(url=url, bare=True)

def checkout(url, version=None):
    """
    Checks out latest version of item or repository.

    :param url: URL of repo or item to check out.
    :param version: Version number to check out.
    """
    from grit import Repo
    r = Repo(url)

    def _write(item):
        log.debug('writing: %s' % item.name)
        if item.type != 'blob':
            return
        if r.type in ['repo', 'proxy', 'local']:
            path = os.path.join(r.name, item.path)
            pdir = os.path.dirname(path)
            if not os.path.isdir(pdir):
                os.makedirs(pdir)
        else:
            path = item.name

        f = open(path, 'w')
        f.write(item.data())
        f.close()

    if r.type == 'blob':
        _write(r)
    else:
        items = r.items()
        count = 1
        total = len(items)
        while count <= total:
            print '[%s/%s] %0.2f%%' %(count, total, (float(count) / total) * 100), '*'*count, '\r',
            _write(items[count-1])
            count += 1
            sys.stdout.flush()
        print

def checkin(url, files, message=None):
    """
    Check in files to a repository.

    :param url: URL of repo to check files into.
    :param message: Optional commit message.
    """
    from grit import Repo, Item
    r = Repo(url)

    if not files:
        raise GritError('No files')

    def _write(path):
        item = Item.from_path(repo=r, path=path)
        if r.isLocal():
            v.addItem(item=item)
        else:
            r.upload(filename=os.path.basename(path), filedata=open(path, 'r').read())

    if r.isLocal():
        v = r.addVersion()
    count = 1
    total = len(files) 
    while count <= total:
        print '[%s/%s] %0.2f%%' %(count, total, (float(count) / total) * 100), '*'*count, '\r',
        _write(os.path.abspath(files[count-1]))
        count += 1
        sys.stdout.flush()
    if message is None:
        message = 'Publishing %s' % ', '.join(files)
    if r.isLocal():
        v.save(message=message)
    print
