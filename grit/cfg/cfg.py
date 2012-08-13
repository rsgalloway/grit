#!/usr/bin/env python
#
# Copyright (C) 2011-2012 Ryan Galloway (ryan@rsgalloway.com)
#
# This module is part of Grit and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php

import os
import logging

# server settings
GRIT_SERVER_PORT = os.environ.get('GRIT_SERVER_PORT', 8080)
GRIT_LOG_LEVEL = os.environ.get('GRIT_LOG_LEVEL', logging.WARN)
GRIT_STATIC_DIR = os.environ.get('GRIT_STATIC_DIR', os.path.join(os.path.dirname(__file__), '..', '..', 'static'))
