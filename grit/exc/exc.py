#!/usr/bin/env python
#
# Copyright (C) 2011-2012 Ryan Galloway (ryan@rsgalloway.com)
#
# This module is part of Grit and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php

from grit.log import log

class GritException(Exception):
    def __call__(self, *args):
        log.exception(*args)

class ConfigError(GritException):
    """custom exception for config errors"""

class GritError(GritException):
    """custom exception for grit errors"""

class RepoError(GritException):
    """custom exception for repo errors"""

class ProxyError(GritException):
    """custom exception for proxy errors"""

class ItemError(GritException):
    """custom exception for item errors"""

class VersionError(GritException):
    """custom exception for version errors"""

class ServerError(GritException):
    """custom exception for server errors"""

class GitError(GritException):
    """custom exception for git errors"""

class InvalidGitRepositoryError(GritException):
    """ Thrown if the given repository appears to have an invalid format.  """

class NoSuchPathError(OSError):
    """ Thrown if a path could not be access by the system. """

class GitCommandError(Exception):
    """ Thrown if execution of the git command fails with non-zero status code. """
    def __init__(self, command, status, stderr=None):
        self.stderr = stderr
        self.status = status
        self.command = command

    def __str__(self):
        return ("'%s' returned exit status %i: %s" %
                   (' '.join(str(i) for i in self.command), self.status, self.stderr))
