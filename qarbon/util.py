# ----------------------------------------------------------------------------
# This file is part of qarbon (http://qarbon.rtfd.org/)
#
# Copyright (c) 2013 European Synchrotron Radiation Facility, Grenoble, France
#
# Distributed under the terms of the GNU Lesser General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
# ----------------------------------------------------------------------------

"""Helper functions."""

__all__ = ['isString', 'isSequence', 'moduleImport', 'moduleDirectory']

import os
import sys
import collections


__str_klasses = [str]
__seq_klasses = [collections.Sequence, bytearray]

# some versions of python don't have unicode (python [3.0, 3.3])
try:
    unicode
    __str_klasses.append(unicode)
except:
    pass

# some versions of python don't have basestring (python [3.0, inf[)
try:
    basestring
    __str_klasses.insert(0, basestring)
except:
    pass

__str_klasses = tuple(__str_klasses)
__seq_klasses = tuple(__seq_klasses)


def isString(obj):
    """Determines if the given object is a string.

    :param obj: the object to be analysed
    :type obj: object
    :return: True if the given object is a string or False otherwise
    :rtype: bool"""
    return isinstance(obj, __str_klasses)


def isSequence(obj, inc_string=False):
    """Determines if the given object is a sequence.

    :param obj: the object to be analysed
    :type obj: object
    :param inc_string: if False, exclude str/unicode objects from the list
                       of possible sequence objects
    :type inc_string: bool
    :return: True if the given object is a sequence or False otherwise
    :rtype: bool"""
    if inc_string:
        return isinstance(obj, __seq_klasses)
    else:
        return isinstance(obj, __seq_klasses) and not isString(obj)


def moduleImport(name):
    """Import module, returning the module after the last dot.

    :param name: name of the module to be imported
    :type name: str
    :return: the imported module
    :rtype: module"""
    __import__(name)
    return sys.modules[name]


def moduleDirectory(module):
    """Returns the location of a given module.

    :param module: the module object
    :type module: module
    :return: the directory where the module is located
    :rtype: str"""
    return os.path.dirname(os.path.abspath(module.__file__))


def __formatStack_OLD(stack_func):
    line_count = 3
    stack = stack_func(line_count)
    stack.reverse()
    out = ''
    for frame_record in stack:
        out += '\n' + 60 * '-'
        frame, filename, line, funcname, lines, _ = frame_record
        #out += '\n    depth = %d' % frame[5]
        out += '\n filename = %s' % filename
        out += '\n function = %s' % funcname
        if lines is None:
            code = '<code could not be found>'
            out += '\n     line %d: %s' % (line, code)
        else:
            lines, line_nb = [s.strip(' \n') for s in lines], len(lines)
            if line_nb >= 3:
                out += '\n     line %d: %s' % (line - 1, lines[0])
                out += '\n  => line %d: %s' % (line, lines[1])
                out += '\n     line %d: %s' % (line + 1, lines[2])
            elif line_nb > 0:
                out += '\n  => line %d: %s' % (line, lines[0])
        if frame:
            max_local_len = max(map(len, frame.f_locals))
            template = "\n      %%%ds = " % max_local_len
            out += '\n   locals = '
            for k, v in frame.f_locals.items():
                out += template % k
                try:
                    cut = False
                    v = str(v)
                    i = v.find('\n')
                    if i == -1:
                        i = 80
                    else:
                        i = min(i, 80)
                        cut = True
                    if len(v) > 80:
                        cut = True
                    out += v[:i]
                    if cut:
                        out += '[...]'
                except:
                    out += '<could not find suitable string representation>'
    return out


def __formatStack(stack_func):
    line_count = 3
    stack = stack_func(line_count)
    stack.reverse()
    out = ''
    for frame_record in stack:
        #out += '\n' + 60 * '-'
        frame, filename, line, funcname, lines, _ = frame_record
        #out += '\n    depth = %d' % frame[5]
        out += '\n  File "%s", line %d, in %s' % (filename, line, funcname)
        out += '\n    code:'
        if lines is None:
            out += '\n      line %d: <code could not be found>' % (line,)
        else:
            lines, line_nb = [s.strip(' \n') for s in lines], len(lines)
            if line_nb >= 3:
                out += '\n      line %d: %s' % (line - 1, lines[0])
                out += '\n      line %d: %s' % (line, lines[1])
                out += '\n      line %d: %s' % (line + 1, lines[2])
            elif line_nb > 0:
                out += '\n      line %d: %s' % (line, lines[0])
        if frame:
            max_local_len = max(map(len, frame.f_locals))
            template = "\n        %%%ds = " % max_local_len
            out += '\n    locals: '
            for k, v in frame.f_locals.items():
                out += template % k
                try:
                    cut = False
                    v = str(v)
                    i = v.find('\n')
                    if i == -1:
                        i = 80
                    else:
                        i = min(i, 80)
                        cut = True
                    if len(v) > 80:
                        cut = True
                    out += v[:i]
                    if cut:
                        out += '[...]'
                except:
                    out += '<could not find suitable string representation>'
    return out


def formatStack():
    import inspect
    return __formatStack(inspect.stack)


def formatTrace():
    import inspect
    return __formatStack(inspect.trace)
