#!/usr/bin/env python
#
# Copyright (C) 2011-2012 Ryan Galloway (ryan@rsgalloway.com)
#
# This module is part of Grit and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php

import os
import simplejson as json
from urllib import urlopen
from urllib import urlencode
from datetime import datetime

from grit.exc import *
from grit.log import log

# -----------------------------------------------------------------------------
class Proxy(object):
    """Remote object proxy class."""

    def __init__(self, url):
        """
        Create a new Proxy instance.

        :param url: URL to object

        :returns: repo.Proxy instance.
        """
        if url.split("/")[0] not in ("http:","https:"):
            raise RepoError("URL protocol must be http or https.  Value was '%s'" % url)
        self.host = "/".join(url.split("/")[2:3])
        self.base_url = "/".join(url.split("/")[0:3])
        self.url = url
        try:
            response = self.request('read')
            if response.get('success', False):
                data = response.get('data', {})
                self.__dict__.update(data)
            else:
                raise ProxyError(response.get('msg', 'Failed to get proxy object'))
        except Exception, e:
            raise ProxyError(e)

    def __str__(self):
        return str(self.url)

    def __repr__(self):
        return '<grit.Proxy "%s">' % self.url

    def __getattr__(self, cmd, *args, **kwargs):
        """
        Convert method call to http request.

        :param cmd: This is the method name that was called.

        :returns: List of Proxy objects.
        """
        def r(*args, **kwargs):
            response = self.request(cmd, *args, **kwargs)
            ret = []
            if cmd == 'data':
                return response
            elif response.get('success'):
                data = response.get('data')
                if type(data) == list:
                    for item in data:
                        p = Proxy(item.get('url', self.url))
                        p.__dict__.update(item)
                        ret.append(p)
                else:
                    return data
            elif response.get('failure'):
                raise ProxyError(response.get('data').get('msg'))
            return ret
        return r

    def request(self, cmd, *args, **kwargs):
        """
        Request data fromo the server.

        :param cmd: repo handler command.

        :returns: Result.
        """
        params = {'action': cmd}
        #TODO: serialize the kwargs?
        params.update(kwargs)
        return self.__request(self.url, params)

    def __request(self, url, params):
        """
        Make an HTTP POST request to the server and return JSON data. 

        :param url: HTTP URL to object.

        :returns: Response as dict. 
        """
        log.debug('request: %s %s' %(url, str(params)))
        try:
            response = urlopen(url, urlencode(params)).read()
            if params.get('action') != 'data':
                log.debug('response: %s' % response)
            if params.get('action', None) == 'data':
                return response
            else:
                return json.loads(response)
        except TypeError, e:
            log.exception('request error')
            raise ServerError(e)
        except IOError, e:
            log.error('request error: %s' % str(e))
            raise ServerError(e)

    def update(self, *args, **kwargs):
        raise ProxyError("Cannot update a proxy repo")

    def isLocal(self):
        return False
