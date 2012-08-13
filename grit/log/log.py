#!/usr/bin/env python
#
# Copyright (C) 2011-2012 Ryan Galloway (ryan@rsgalloway.com)
#
# This module is part of Grit and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php

import os
import logging
import traceback

from grit.cfg import GRIT_LOG_LEVEL

__all__ = ['log']

class Log(object):

    def __init__(self):
        self.logger = logging.getLogger('grit')
        ch = logging.StreamHandler()
        self.extra = {'host': os.environ.get('HOST'), 'user': os.environ.get('USER')}
        formatter = logging.Formatter("[%(asctime)s] %(levelname)8s %(host)s - %(user)s - %(message)s")
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        self.logger.setLevel(int(GRIT_LOG_LEVEL))

    def __getattr__(self, key, *args, **kwargs):
        def r(*args, **kwargs):
            kwargs['extra'] = self.extra
            m = getattr(self.logger, key, 'info')
            return m(*args, **kwargs)
        if key == 'exception':
            key = 'error'
            traceback.print_exc()
        return r

log = Log()
