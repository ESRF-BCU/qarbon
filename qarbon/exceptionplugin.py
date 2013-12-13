# ----------------------------------------------------------------------------
# This file is part of qarbon (http://qarbon.rtfd.org/)
#
# Copyright (c) 2013 European Synchrotron Radiation Facility, Grenoble, France
#
# Distributed under the terms of the GNU Lesser General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
# ----------------------------------------------------------------------------

"""Helper exception plugins"""

__all__ = ['BaseExceptionPlugin', 'MultiplexExceptionPlugin',
           'LogExceptionPlugin']

import sys
import logging

#------------------------------------------------------------------------------
# Exception handling
#------------------------------------------------------------------------------


class BaseExceptionPlugin(object):
    """A callable class that acts as an excepthook that handles an exception.
    This base class simply calls the :obj:`sys.__excepthook__`

    :param hook_to: callable excepthook that will be called at the end of
                    this hook handling [default: None]
    :type hook_to: callable"""

    def __init__(self, target=None):
        self._target = target

    def __call__(self, *exc_info):
        result = self.handle(*exc_info)
        if result and self._target is not None:
            return self._target(*exc_info)
        return result

    def handle(self, *exc_info):
        """Report an exception. Overwrite as necessary"""
        sys.__excepthook__(*exc_info)
        return True


class MultiplexExceptionPlugin(list, BaseExceptionPlugin):
    """Just splits the exception handling to all elements in itself
    (as a list)"""

    def __init__(self, target=None):
        list.__init__(self)
        BaseExceptionPlugin.__init__(self, target=target)

    def handle(self, *exc_info):
        for target in self:
            ret = target(*exc_info)
            if not ret:
                return False
        return True


class LogExceptionPlugin(BaseExceptionPlugin):
    """A callable class that acts as an excepthook that logs the exception in
    the python logging system.

    :param hook_to: callable excepthook that will be called at the end of
                    this hook handling [default: None]
    :type hook_to: callable
    :param name: logger name [default: None meaning use logging module,
                 "" means use root logger (slightly different because logging
                 module initializes logging system with basicConfig if
                 necessary]
    :type name: str
    :param level: log level [default: logging.ERROR]
    :type level: int"""

    def __init__(self, target=None, name=None, level=logging.CRITICAL):
        super(LogExceptionPlugin, self).__init__(target=target)
        self._level = level
        if name is None:
            self._log = logging.log
        else:
            self._log = logging.getLogger(name=name).log

    def handle(self, *exc_info):
        self._log(self._level, "Uncaught exception:", exc_info=exc_info)
        return True
