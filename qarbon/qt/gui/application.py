# ----------------------------------------------------------------------------
# This file is part of qarbon (http://qarbon.rtfd.org/)
#
# Copyright (c) 2013 European Synchrotron Radiation Facility, Grenoble, France
#
# Distributed under the terms of the GNU Lesser General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
# ----------------------------------------------------------------------------

"""Helper functions to manage QApplication.

Most common use case::


    from qarbon.external.qt import QtGui
    from qarbon.qt.gui.application import Application

    app = Application()
    label = QtGui.QLabel("Hello, world!")
    label.show()
    app.exec_()

The advantage here is you can call :func:`Application` anywhere on your
program.
"""

__all__ = ["Application"]

from qarbon import log
from qarbon import config


def Application(argv=None, **kwargs):
    """Returns a QApplication.

    If the process has initialized before a QApplication it returns the
    existing instance, otherwise it creates a new one.

    When a QApplication is created it takes argv into account. If argv is
    None (default), it take arguments from :attr:`sys.argv`.

    If argv is given and a QApplication already exists, argv will have no
    effect.

    :param argv: optional arguments to QApplication. If the QApplication is
                 already initialized, argv will have no effect.

    Example::

        from qarbon.external.qt import QtGui
        from qarbon.qt.gui.application import Application

        app = Application()
        label = QtGui.QLabel("Hello, world!")
        label.show()
        app.exec_()

    :param kwargs: currently unused
    :return: the QApplication
    :rtype: QtGui.QApplication"""

    # It is important to initialize logging before Qt because Qt might
    # fire some log messages
    init_logging = kwargs.get('init_logging', False)
    if init_logging:
        log.initialize()

    from qarbon.external.qt import QtGui
    app = QtGui.QApplication.instance()
    if app is None:
        if argv is None:
            from sys import argv
        app = QtGui.QApplication(argv)

        init_application = kwargs.get('init_application', True)
        init_organization = kwargs.get('init_organization', True)
        if init_application:
            app_name = kwargs.get('application_name', config.APPLICATION_NAME)
            app.setApplicationName(app_name)
            app_version = kwargs.get('application_version',
                                     config.APPLICATION_VERSION)
            app.setApplicationVersion(app_version)
        if init_organization:
            org_name = kwargs.get('organization_name',
                                  config.ORGANIZATION_NAME)
            app.setOrganizationName(org_name)
            org_domain = kwargs.get('organization_domain',
                                    config.ORGANIZATION_DOMAIN)
            app.setOrganizationDomain(org_domain)

    elif argv:
        log.info("QApplication already initialized. argv will have no "
                 "effect")
    return app


def getApplication(argv=None, **properties):
    """Returns a QApplication.

    If the process has initialized before a QApplication it returns the
    existing instance, otherwise it creates a new one.

    When a QApplication is created it takes argv into account. If argv is
    None (default), it take arguments from :attr:`sys.argv`.

    If argv is given and a QApplication already exists, argv will have no
    effect.

    This is function as the same effect as :func:`Application`. Please use
    :func:`Application` instead.

    Example::

        from qarbon.external.qt import QtGui
        from qarbon.qt.gui.application import getApplication

        app = getApplication()
        label = QtGui.QLabel("Hello, world!")
        label.show()
        app.exec_()

    :param argv: optional arguments to QApplication. If the QApplication is
                 already initialized, argv will have no effect
    :param properties: currently unused
    :return: the QApplication
    :rtype: QtGui.QApplication"""
    return Application(argv=argv, **properties)
