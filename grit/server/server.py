#!/usr/bin/env python
#
# Copyright (C) 2011-2012 Ryan Galloway (ryan@rsgalloway.com)
#
# This module is part of Grit and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php

import os
import sys
import urllib
import urlparse
import simplejson as json

from datetime import datetime as dt

from stat import *

from cherrypy import CherryPyWSGIServer
from wsgiref.headers import Headers
from git_http_backend import GitHTTPBackendInfoRefs
from git_http_backend import GitHTTPBackendSmartHTTP
from git_http_backend import WSGIHandlerSelector
from git_http_backend import StaticWSGIServer

from grit.repo import Local
from grit.repo import is_repo, get_repo_parent
from grit.server.handler import *
from grit.exc import *
from grit.log import log
from grit.cfg import GRIT_STATIC_DIR

# needed for static content server
import time
import email.utils
import mimetypes
mimetypes.add_type('application/x-git-packed-objects-toc','.idx')
mimetypes.add_type('application/x-git-packed-objects','.pack')

__all__ = ['Server']

def make_app(*args, **kw):
    '''
    Assembles basic WSGI-compatible application providing functionality of git-http-backend.

    content_path (Defaults to '.' = "current" directory)
        The path to the folder that will be the root of served files. Accepts relative paths.

    uri_marker (Defaults to '')
        Acts as a "virtual folder" separator between decorative URI portion and
        the actual (relative to content_path) path that will be appended to
        content_path and used for pulling an actual file.

        the URI does not have to start with contents of uri_marker. It can
        be preceeded by any number of "virtual" folders. For --uri_marker 'my'
        all of these will take you to the same repo:
            http://localhost/my/HEAD
            http://localhost/admysf/mylar/zxmy/my/HEAD
        This WSGI hanlder will cut and rebase the URI when it's time to read from file system.

        Default of '' means that no cutting marker is used, and whole URI after FQDN is
        used to find file relative to content_path.

    returns WSGI application instance.
    '''

    default_options = [
        ['content_path','.'],
        ['uri_marker','']
    ]
    args = list(args)
    options = dict(default_options)
    options.update(kw)
    while default_options and args:
        _d = default_options.pop(0)
        _a = args.pop(0)
        options[_d[0]] = _a
    options['content_path'] = os.path.abspath(options['content_path'].decode('utf8'))
    options['uri_marker'] = options['uri_marker'].decode('utf8')

    selector = WSGIHandlerSelector()
    git_inforefs_handler = GitHTTPBackendInfoRefs(**options)
    git_rpc_handler = GitHTTPBackendSmartHTTP(**options)
    static_handler = StaticServer(**options)
    file_handler = FileServer(**options)
    json_handler = JSONServer(**options)
    ui_handler = UIServer(**options)

    if options['uri_marker']:
        marker_regex = r'(?P<decorative_path>.*?)(?:/'+ options['uri_marker'] + ')'
    else:
        marker_regex = ''

    selector.add(
        marker_regex + r'(?P<working_path>.*?)/info/refs\?.*?service=(?P<git_command>git-[^&]+).*$',
        GET = git_inforefs_handler,
        HEAD = git_inforefs_handler
        )
    selector.add(
        marker_regex + r'(?P<working_path>.*)/(?P<git_command>git-[^/]+)$',
        POST = git_rpc_handler
        )
    selector.add(
        marker_regex + r'/static/(?P<working_path>.*)$',
        GET = static_handler,
        HEAD = static_handler)
    selector.add(
        marker_regex + r'(?P<working_path>.*)/file$',
        GET = file_handler,
        HEAD = file_handler)
    selector.add(
        marker_regex + r'(?P<working_path>.*)$',
        GET = ui_handler,
        POST = json_handler,
        HEAD = ui_handler)

    return selector

class JSONServer(StaticWSGIServer):

    def error_response(self, error, environ, start_response):
        headerbase = [('Content-Type', 'text/plain')]
        start_response(self.canned_collection['400'], headerbase)
        d = {}
        d['success'] = False
        d['failure'] = True
        d['data'] = {'msg': error}
        _ret = json.dumps(d)
        log.debug('ERROR: %s' % _ret)
        return _ret

    def json_response(self, data, environ, start_response):
        headerbase = [('Content-Type', 'text/plain')]
        start_response(self.canned_collection['200'], headerbase)

        d = {}
        d['success'] = True
        d['failure'] = False

        try:
            if type(data) == list:
                for item in data:
                    if not item.get('url'):
                        item['url'] = os.path.join(self.url, item.get('path', str(item)))

            d['data'] = data
            _ret = json.dumps(d)

        except Exception, e:
            return self.error_response(str(e), environ, start_response)

        return _ret

    def get_params(self, environ):
        kwargs = {}
        params = urlparse.parse_qs(environ.get('wsgi.input').read())
        action = params.get('action', ['read'])[0]
        xaction = params.get('xaction', ['read'])[0]
        try:
            del params['action']
            del params['xaction']
        except:
            pass

        for k,v in params.items():
            try:
                kwargs[k] = eval(params[k][0])
            except Exception, e:
                kwargs[k] = params[k][0]

        return action, kwargs

    def __call__(self, environ, start_response):

        selector_matches = (environ.get('wsgiorg.routing_args') or ([],{}))[1]
        if 'working_path' in selector_matches:
            path_info = selector_matches['working_path'].decode('utf8')
        else:
            path_info = environ.get('PATH_INFO', '').decode('utf8')

        scheme = environ.get('wsgi.url_scheme', 'http')
        host = environ.get('HTTP_HOST', 'localhost').decode('utf8')
        self.url = '%s://%s/%s' %(scheme, host, path_info)

        full_path = os.path.abspath(os.path.join(self.content_path, path_info.strip('/')))
        _pp = os.path.abspath(self.content_path)

        cmd, kwargs = self.get_params(environ)

        if not full_path.startswith(_pp):
            log.error('forbidden: %s' % full_path)
            return self.canned_handlers(environ, start_response, 'forbidden')

        if os.path.exists(full_path):
            mtime = os.stat(full_path).st_mtime
            etag, last_modified =  str(mtime), email.utils.formatdate(mtime)
        else:
            mtime, etag, last_modified = (None, None, None)

        headers = [
            ('Content-type', 'text/plain'),
            ('Date', email.utils.formatdate(time.time())),
            ('Last-Modified', last_modified),
            ('ETag', etag)
        ]

        fmap = {
            'read': handle_read,
            'new': handle_branch,
            'branch': handle_branch,
            'repos': handle_repos,
            'items': handle_items,
            'versions': handle_versions,
            'submodules': handle_submodules,
            'addSubmodule': handle_addSubmodule,
            'addVersion': handle_addVersion,
            'parent': handle_parent,
            'upload': handle_upload,
        }

        repo = get_repo_parent(full_path)
        if repo is None:
            repo = full_path
        item_path = full_path.split(str(repo))[-1][1:]

        #HACK: get the item, swap with repo
        if item_path and cmd != 'submodules':
            log.debug('full_path: %s, item_path: %s' % (full_path, item_path))
            items = repo.items(path=item_path)
            if items:
                repo = item = items[0]

        if cmd == 'data':
            data = repo.file()
            return self.package_response(data, environ, start_response)

        else:
            func = fmap.get(cmd, None)
            if func:
                response = func(repo, **kwargs)
            else:
                response = getattr(repo, cmd)(**kwargs)
        return self.json_response(response, environ, start_response)

class StaticServer(StaticWSGIServer):
    def __init__(self, *args, **kwargs):
        super(StaticServer, self).__init__(*args, **kwargs)

    def __call__(self, environ, start_response):
        path_info = environ.get('PATH_INFO', '').decode('utf8')
        self.content_path = os.path.join(os.path.dirname(__file__), '..', '..')
        return super(StaticServer, self).__call__(environ, start_response)

class FileServer(StaticWSGIServer):
    def __init__(self, *args, **kwargs):
        super(FileServer, self).__init__(*args, **kwargs)

    def __call__(self, environ, start_response):

        selector_matches = (environ.get('wsgiorg.routing_args') or ([],{}))[1]
        if 'working_path' in selector_matches:
            path_info = selector_matches['working_path'].decode('utf8')
        else:
            path_info = environ.get('PATH_INFO', '').decode('utf8')

        full_path = os.path.abspath(os.path.join(self.content_path, path_info.strip('/')))
        repo = get_repo_parent(full_path)
        item_path = full_path.split(str(repo))[-1][1:]

        # look for the item in the repo
        items = repo.items(path=item_path)

        # return file-like object
        if items:
            file_like = items[0].file()
        else:
            default = os.path.join(GRIT_STATIC_DIR, os.path.basename(item_path))
            file_like = open(default, 'rb')

        return self.package_response(file_like, environ, start_response)

class UIServer(StaticWSGIServer):
    def __init__(self, *args, **kwargs):
        super(UIServer, self).__init__(*args, **kwargs)

    def __call__(self, environ, start_response):
        full_path = os.path.join(GRIT_STATIC_DIR, 'index.html')

        mtime = os.stat(full_path).st_mtime
        etag, last_modified =  str(mtime), email.utils.formatdate(mtime)
        headers = [
            ('Content-type', 'text/html'),
            ('Date', email.utils.formatdate(time.time())),
            ('Last-Modified', last_modified),
            ('ETag', etag)
        ]

        file_like = open(full_path, 'rb')
        return self.package_response(file_like, environ, start_response, headers)

class Server(CherryPyWSGIServer):
    """
    Assembles basic WSGI-compatible application providing functionality of git-http-backend.
    """
    def __init__(self, base_dir='.', port=8080, uri_marker=''):
        """
        Creates a new instance of Server.

        :param base_dir:
            The path to the folder that will be the root of served files.
            Accepts relative paths (default is current path).

        :param port:
            The port to listen on (default 8080).

        :return: WSGI server instance.
        """
        ip = '0.0.0.0'
        app = make_app(
            content_path = base_dir,
            uri_marker = uri_marker,
            performance_settings = {
                'repo_auto_create':True
                }
            )
        super(Server, self).__init__((ip, int(port)), app)
