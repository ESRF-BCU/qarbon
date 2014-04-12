# ----------------------------------------------------------------------------
# This file is part of qarbon (http://qarbon.rtfd.org/)
#
# Copyright (c) 2013 European Synchrotron Radiation Facility, Grenoble, France
#
# Distributed under the terms of the GNU Lesser General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
# ----------------------------------------------------------------------------

"""A widget to display errors/exceptions.

This module contains widgets to display error messages coming from a python
exception (both the widget and dialog versions are present)

A :func:`protect` decorator can be used to protect your functions/methods. The
decorator will display the exception thrown from your code in a dialog and
it will absorve the exception (default behaviour, can be modified).

Examples::

    from qarbon import config
    from qarbon.qt.gui.application import Application
    from qarbon.qt.gui.exceptionwidget import ErrorDialog
    from qarbon.qt.gui.exceptionwidget import protect

    class Beamer:
        def turnOn(self):
            return False

    def buggy():
        l = [1, 2, 3]
        try:
            print(l[3])
        except IndexError:
            msgbox = ErrorDialog()
            msgbox.exec_()

    @protect
    def turnBeamOn(ctrl_obj):
        result = ctrl_obj.turnOn()
        if not result:
            raise Exception("Could not turn on beam!")

    def main():
        config.APPLICATION_NAME = "Qarbon demo"
        app = Application()

        buggy()
        beamer = Beamer()
        turnBeamOn(beamer)

    if __name__ == "__main__":
        main()
    """

__all__ = ["BaseReportPlugin", "ClipboardReportPlugin", "SMTPReportPlugin",
           "BaseErrorFormatterPlugin", "TangoErrorFormatterPlugin",
           "ErrorWidget", "ErrorDialog", "protect"]

__docformat__ = 'restructuredtext'

import os
import sys
import inspect
import datetime
import functools
import traceback
import collections

try:
    import pygments
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import PythonTracebackLexer
except ImportError:
    pygments = None

from qarbon.exceptionplugin import BaseExceptionPlugin
from qarbon.external.qt import QtCore, QtGui, uic
from qarbon.qt.gui.application import Application
from qarbon.qt.gui.icon import Icon


#------------------------------------------------------------------------------
# Report handlers
# Handle an error report in some way (print to screen, send email, etc)
#------------------------------------------------------------------------------


class BaseReportPlugin(object):

    Label = "Default report handler"

    def __init__(self, parent):
        self.parent = parent

    def report(self, message):
        pass


class ClipboardReportPlugin(BaseReportPlugin):
    """Report a message by copying it to the clipboard"""

    Label = "Copy to Clipboard"

    def report(self, message):
        app = Application()
        clipboard = app.clipboard()
        clipboard.setText(message)

        QtGui.QMessageBox.information(None, "Done!",
                                      "Message Copied to clipboard")


class SendMailDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        ui_file_name = os.path.join(os.path.dirname(__file__), 'ui',
                                    'sendmailform.ui')
        uic.loadUi(ui_file_name, baseinstance=self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.editMessage.setFont(QtGui.QFont("Monospace"))

    def setFrom(self, efrom):
        self.lineEditFrom.setText(efrom)

    def setTo(self, eto):
        self.editTo.setText(eto)

    def setSubject(self, subject):
        self.editSubject.setText(subject)

    def setMessage(self, message):
        self.editMessage.setPlainText(message)

    def getFrom(self):
        return str(self.editFrom.text())

    def getTo(self):
        return str(self.editTo.text())

    def getSubject(self):
        return str(self.editSubject.text())

    def getMessage(self):
        return str(self.editMessage.toPlainText())

    def getMailInfo(self):
        return self.getFrom(), self.getTo(), self.getSubject(), \
               self.getMessage()


class SMTPReportPlugin(BaseReportPlugin):
    """Report a message by sending an email"""

    Label = "Send email"

    def report(self, message):
        app = Application()
        subject = "Error in " + app.applicationName()
        dialog = self.createDialog(subject=subject, message=message)

        if not dialog.exec_():
            return

        mail_info = dialog.getMailInfo()

        try:
            self.sendMail(*mail_info)
            QtGui.QMessageBox.information(None, "Done!",
                "Email has been sent!")
        except:
            einfo = sys.exc_info()[:2]
            msg = "".join(traceback.format_exception_only(*einfo))
            QtGui.QMessageBox.warning(None, "Failed to send email",
                "Failed to send email. Reason:\n\n" + msg)

    def sendMail(self, efrom, eto, subject, message):
        import smtplib
        import email.mime.text
        msg = email.mime.text.MIMEText(message)
        msg['From'] = efrom
        msg['To'] = eto
        msg['Subject'] = subject

        s = smtplib.SMTP('localhost')
        s.sendmail(efrom, eto, msg.as_string())
        s.quit()

    def getDialogClass(self):
        return SendMailDialog

    def createDialog(self, efrom=None, eto=None, subject=None, message=None):
        dialog = self.getDialogClass()()
        dialog.setWindowTitle("Compose message")
        if efrom is not None:
            dialog.setFrom(efrom)
        if eto is not None:
            dialog.setFrom(eto)
        if subject is not None:
            dialog.setSubject(subject)
        if message is not None:
            dialog.setMessage(message)
        return dialog


_REPORT_HANDLERS = None


def get_report_handlers():
    global _REPORT_HANDLERS
    if _REPORT_HANDLERS is None:
        _REPORT_HANDLERS = {}
        for k, v in globals().items():
            if inspect.isclass(v):
                if issubclass(v, BaseReportPlugin) and v != BaseReportPlugin:
                    _REPORT_HANDLERS[k] = v
    return _REPORT_HANDLERS


#------------------------------------------------------------------------------
# Error message handlers
# Handle a specific exception in a message panel
#------------------------------------------------------------------------------


class BaseErrorFormatterPlugin(object):
    """This class is designed to handle a generic error into a
    :class:`ErrorWidget`"""

    def translateError(self, err_type=None, err_value=None,
                       err_traceback=None):
        """Translates the given error object into title string, an HTML error
        string, an HTML error orgin

        :param error: an error object (typically an exception object)
        :type error: object"""
        return (self.toTitle(err_type, err_value, err_traceback),
            self.toErrorHtml(err_type, err_value, err_traceback),
            self.toDetailedErrorHtml(err_type, err_value, err_traceback),
            self.toOriginHtml(err_type, err_value, err_traceback))

    def toTitle(self, err_type=None, err_value=None, err_traceback=None):
        if err_type is None:
            return "Unhandled Error"
        else:
            return "Unhandled Error ({0})".format(err_type.__name__)

    def toErrorHtml(self, err_type=None, err_value=None, err_traceback=None):
        return "".join(traceback.format_exception_only(err_type, err_value))

    def toDetailedErrorHtml(self, err_type=None, err_value=None,
                            err_traceback=None):
        error = self.toErrorHtml(err_type, err_value, err_traceback)
        return "<html><body><pre>{0}</pre></body></html>".format(error)

    def toOriginHtml(self, err_type=None, err_value=None, err_traceback=None):
        html_orig = '<html><head><style type="text/css">{style}</style>' \
                    '</head><body>'
        exc_info = "".join(traceback.format_exception(err_type, err_value,
                                                      err_traceback))
        style = ""
        if pygments is not None:
            formatter = HtmlFormatter()
            style = formatter.get_style_defs()
        html = html_orig.format(style=style)
        if pygments is None:
            html += "<pre>%s</pre>" % exc_info
        else:
            formatter = HtmlFormatter()
            html += highlight(exc_info, PythonTracebackLexer(), formatter)
        html += "</body></html>"
        return html


class TangoErrorFormatterPlugin(BaseErrorFormatterPlugin):
    """This class is designed to handle :class:`PyTango.DevFailed` error into
    a :class:`ErrorWidget`"""

    def toTitle(self, err_type, err_value, err_traceback):
        return "Tango Error"

    def toErrorHtml(self, err_type=None, err_value=None, err_traceback=None):
        return err_value.args[0].desc

    def toDetailedErrorHtml(self, err_type=None, err_value=None,
                            err_traceback=None):
        html_orig = '<html><head><style type="text/css">{style}</style>' \
                    '</head><body>'
        style, formatter = "", None
        if pygments is not None:
            formatter = HtmlFormatter()
            style = formatter.get_style_defs()
        html = html_orig.format(style=style)
        for de in err_value.args:
            e_html = """<pre>{reason}: {desc}</pre>{origin}<hr>"""
            origin, reason, desc = de.origin, de.reason, de.desc
            if reason.startswith("PyDs_") and pygments is not None:
                origin = highlight(origin, PythonTracebackLexer(), formatter)
            else:
                origin = "<pre>%s</pre>" % origin
            html += e_html.format(desc=desc, origin=origin, reason=reason)
        html += "</body></html>"
        return html

    def toOriginHtml(self, err_type=None, err_value=None, err_traceback=None):
        exc_info = "".join(traceback.format_exception(err_type, err_value,
                                                      err_traceback))
        html_orig = '<html><head><style type="text/css">{style}</style>' \
                    '</head><body>'
        style, formatter = "", None
        if pygments is not None:
            formatter = HtmlFormatter()
            style = formatter.get_style_defs()
        html = html_orig.format(style=style)
        if pygments is None:
            html += "<pre>%s</pre>" % exc_info
        else:
            html += highlight(exc_info, PythonTracebackLexer(), formatter)
        html += "</body></html>"
        return html


_REPORT = """\
-- Description ----------------------------------------------------------------
An error occured in '{appName} {appVersion}' on {time}
{text}

-- Details --------------------------------------------------------------------
{detail}

-- Origin ---------------------------------------------------------------------
{origin}
-------------------------------------------------------------------------------
"""


class ErrorWidget(QtGui.QWidget):
    """A panel intended to display an error.
    Example::

        l = [1, 2, 3]
        try:
            print(l[3])
        except IndexError:
            msgbox = ErrorWidget()
            msgbox.show()

    You can show the error outside the exception handling code. If you do this,
    you should keep a record of the exception information as given by
    :func:`sys.exc_info`::

        l = [1, 2, 3]
        exc_info = None
        try:
            print(l[3])
        except IndexError:
            exc_info = sys.exc_info()

        if exc_info:
            msgbox = ErrorWidget(*exc_info)
            msgbox.show()"""

    toggledDetails = QtCore.Signal(bool)

    def __init__(self, err_type=None, err_value=None, err_traceback=None,
                 parent=None):
        QtGui.QWidget.__init__(self, parent)

        if err_type is None and err_value is None and err_traceback is None:
            err_type, err_value, err_traceback = sys.exc_info()[:3]

        self._exc_info = err_type, err_value, err_traceback
        ui_file_name = os.path.join(os.path.dirname(__file__), "ui",
                                    "errorpanel.ui")
        uic.loadUi(ui_file_name, baseinstance=self)
        self.detailsWidget.setVisible(False)
        self.checkBox.setVisible(False)
        self.checkBox.setCheckState(QtCore.Qt.Unchecked)
        self._initReportCombo()

        self.showDetailsButton.toggled.connect(self._onShowDetails)
        self.reportComboBox.activated.connect(self._onReportTriggered)

        self.setIcon(Icon("emblem-important"))

        if err_value is not None:
            self.setError(*self._exc_info)
        self.adjustSize()

    def _initReportCombo(self):
        report_handlers = get_report_handlers()
        combo = self.reportComboBox
        for name, report_handler in report_handlers.items():
            combo.addItem(report_handler.Label, name)

    def _onReportTriggered(self, index):
        report_handlers = get_report_handlers()
        combo = self.reportComboBox
        name = combo.itemData(index)
        report_handler = report_handlers[name]
        report = report_handler(self)
        app = Application()
        txt = _REPORT.format(appName=app.applicationName(),
                             appVersion=app.applicationVersion(),
                             time=datetime.datetime.now().ctime(),
                             text=self.getText(),
                             detail=self.getDetailedText(),
                             origin=self.getOriginText())
        report.report(txt)

    def _onShowDetails(self, show):
        self.detailsWidget.setVisible(show)
        if show:
            text = "Hide details..."
        else:
            text = "Show details..."
        self.showDetailsButton.setText(text)
        self.adjustSize()
        self.toggledDetails.emit(show)

    def checkBoxState(self):
        """Returns the check box state

        :return: the check box state
        :rtype: PyQt4.Qt.CheckState"""
        return self.checkBox.checkState()

    def checkBoxText(self):
        """Returns the check box text

        :return: the check box text
        :rtype: str"""
        return str(self.checkBox.text())

    def setCheckBoxText(self, text):
        """Sets the checkbox text.

        :param text: new checkbox text
        :type text: str"""
        self.checkBox.setText(text)

    def setCheckBoxState(self, state):
        """Sets the checkbox state.

        :param text: new checkbox state
        :type text: PyQt4.Qt.CheckState"""
        self.checkBox.setCheckState(state)

    def setCheckBoxVisible(self, visible):
        """Sets the checkbox visibility.

        :param visible: True makes checkbox visible, False hides it
        :type visible: bool"""
        self.checkBox.setVisible(visible)

    def addButton(self, button, role=QtGui.QDialogButtonBox.ActionRole):
        """Adds the given button with the given to the button box

        :param button: the button to be added
        :type button: PyQt4.QtGui.QPushButton
        :param role: button role
        :type role: PyQt4.Qt.QDialogButtonBox.ButtonRole"""
        self.buttonBox.addButton(button, role)

    def setIcon(self, icon, size=64):
        """Sets the icon to the dialog

        :param icon: the icon
        :type icon: PyQt4.QtGui.QIcon"""
        pixmap = icon.pixmap(size)
        self.iconLabel.setPixmap(pixmap)

    def setText(self, text):
        """Sets the text of this panel

        :param text: the new text
        :type text: str"""
        self.textLabel.setText(text)

    def getText(self):
        """Returns the current text of this panel

        :return: the text for this panel
        :rtype: str"""
        return self.textLabel.text()

    def setDetailedText(self, text):
        """Sets the detailed text of the dialog

        :param text: the new text
        :type text: str"""
        self.detailsTextEdit.setPlainText(text)

    def setDetailedHtml(self, html):
        """Sets the detailed HTML of the dialog

        :param html: the new HTML text
        :type html: str"""
        self.detailsTextEdit.setHtml(html)

    def getDetailedText(self):
        """Returns the current detailed text of this panel

        :return: the detailed text for this panel
        :rtype: str"""
        return self.detailsTextEdit.toPlainText()

    def getDetailedHtml(self):
        """Returns the current detailed HTML of this panel

        :return: the detailed HTML for this panel
        :rtype: str"""
        return self.detailsTextEdit.toHtml()

    def setOriginText(self, text):
        """Sets the origin text of the dialog

        :param text: the new text
        :type text: str"""
        self.originTextEdit.setPlainText(text)

    def setOriginHtml(self, html):
        """Sets the origin HTML of the dialog

        :param html: the new HTML text
        :type html: str"""
        self.originTextEdit.setHtml(html)

    def getOriginText(self):
        """Returns the current origin text of this panel

        :return: the origin text for this panel
        :rtype: str"""
        return self.originTextEdit.toPlainText()

    def getOriginHtml(self):
        """Returns the current origin HTML of this panel

        :return: the origin HTML for this panel
        :rtype: str"""
        return self.originTextEdit.toHtml()

    def setError(self, err_type=None, err_value=None, err_traceback=None):
        """Sets the exception object.
        Example usage::

            l = [1, 2, 3]
            exc_info = None
            try:
                print(l[3])
            except IndexError:
                exc_info = sys.exc_info()

            if exc_info:
                msgbox = ErrorWidget()
                msgbox.setError(*exc_info)
                msgbox.show()

        :param err_type: the exception type of the exception being handled
                         (a class object)
        :type error: class object
        :param err_value: exception object
        :type err_value: object
        :param err_traceback: a traceback object which encapsulates the call
                              stack at the point where the exception originally
                              occurred
        :type err_traceback: traceback"""
        i = sys.exc_info()
        self._exc_info = [err_type or i[0],
                          err_value or i[1],
                          err_traceback or i[2]]

        formatter_klass = self.findErrorFormatter(self._exc_info[0])
        formatter = formatter_klass()
        error_data = formatter.translateError(*self.getError())
        title, error, detailed_error, origin = error_data
        self.setWindowTitle(title)
        self.setText(error)
        self.setDetailedHtml(detailed_error)
        self.setOriginHtml(origin)

    def getError(self):
        """Returns the current exception information of this panel

        :return: the current exception information (same as type as returned by
                 :func:`sys.exc_info`)
        :rtype: tuple<type, value, traceback>"""
        return self._exc_info

    @staticmethod
    def getErrorFormatters():
        result = {}
        try:
            import PyTango
            result[PyTango.DevFailed] = TangoErrorFormatterPlugin
        except ImportError:
            pass
        return result

    @classmethod
    def registerErrorHandler(klass, err_type, err_handler):
        klass.getErrorFormatters()[err_type] = err_handler

    @classmethod
    def findErrorFormatter(klass, err_type):
        """Finds the proper error handler class for the given error

        :param err_type: error class
        :type err_type: class object
        :return: a message box error handler
        :rtype: TaurusMessageBoxErrorHandler class object"""

        for exc, h_klass in klass.getErrorFormatters().items():
            if issubclass(err_type, exc):
                return h_klass
        return BaseErrorFormatterPlugin


class ErrorDialog(QtGui.QDialog):
    """A panel intended to display an error.
    Example::

        l = [1, 2, 3]
        try:
            print(l[3])
        except IndexError:
            msgbox = ErrorDialog()
            msgbox.show()

    You can show the error outside the exception handling code. If you do this,
    you should keep a record of the exception information as given by
    :func:`sys.exc_info`::

        l = [1, 2, 3]
        exc_info = None
        try:
            print(l[3])
        except IndexError:
            exc_info = sys.exc_info()

        if exc_info:
            msgbox = ErrorDialog(*exc_info)
            msgbox.show()"""

    def __init__(self, err_type=None, err_value=None, err_traceback=None,
                 parent=None):
        QtGui.QDialog.__init__(self, parent)
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)
        if err_type is None and err_value is None and err_traceback is None:
            err_type, err_value, err_traceback = sys.exc_info()[:3]
        self._panel = ErrorWidget(err_type, err_value, err_traceback, self)
        self.setWindowTitle(self._panel.windowTitle())
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._panel)
        self._panel.buttonBox.accepted.connect(self.accept)
        self._panel.toggledDetails.connect(self._onShowDetails)

    def _onShowDetails(self, show):
        self.adjustSize()

    def panel(self):
        """Returns the :class:`Framework4.GUI.Qt.Widgets.ErrorWidget`.

        :return: the internal panel
        :rtype: Framework4.GUI.Qt.Widgets.ErrorWidget"""
        return self._panel

    def addButton(self, button, role=QtGui.QDialogButtonBox.ActionRole):
        """Adds the given button with the given to the button box

        :param button: the button to be added
        :type button: PyQt4.QtGui.QPushButton
        :param role: button role
        :type role: PyQt4.Qt.QDialogButtonBox.ButtonRole"""
        self.panel().addButton(button, role)

    def setIcon(self, icon, size=64):
        """Sets the icon to the dialog

        :param icon: the icon
        :type icon: PyQt4.QtGui.QIcon"""
        self._panel.setIcon(icon, size=size)

    def setText(self, text):
        """Sets the text of the dialog

        :param text: the new text
        :type text: str"""
        self._panel.setText(text)

    def getText(self):
        """Returns the current text of this panel

        :return: the text for this panel
        :rtype: str"""
        return self._panel.getText()

    def setDetailedText(self, text):
        """Sets the detailed text of the dialog

        :param text: the new text
        :type text: str"""
        self._panel.setDetailedText(text)

    def setError(self, err_type=None, err_value=None, err_traceback=None):
        """Sets the exception object.
        Example usage::

            l = [1, 2, 3]
            exc_info = None
            try:
                print(l[3])
            except IndexError:
                exc_info = sys.exc_info()

            if exc_info:
                msgbox = ErrorDialog()
                msgbox.setError(*exc_info)
                msgbox.show()

        :param err_type: the exception type of the exception being handled
                         (a class object)
        :type error: class object
        :param err_value: exception object
        :type err_value: object
        :param err_traceback: a traceback object which encapsulates the call
                              stack at the point where the exception originally
                              occurred
        :type err_traceback: traceback"""
        self._panel.setError(err_type, err_value, err_traceback)
        self.setWindowTitle(self._panel.windowTitle())


__PROTECT_ERROR_DIALOG = None


def _ProtectErrorDialog(err_type=None, err_value=None, err_traceback=None,
                        parent=None):
    global __PROTECT_ERROR_DIALOG
    box = __PROTECT_ERROR_DIALOG
    if box is None:
        __PROTECT_ERROR_DIALOG = box = ErrorDialog(err_type=err_type,
            err_value=err_value, err_traceback=err_traceback, parent=parent)
        box.setAttribute(QtCore.Qt.WA_QuitOnClose, False)
    else:
        box.setError(err_type=err_type, err_value=err_value,
                     err_traceback=err_traceback)
    if box.panel().checkBoxState() == QtCore.Qt.Checked:
        return
    return box


def protect(obj=None, title=None, msg=None, async=False, re_throw=False):
    """The idea of this function is to be used as a decorator on any method
    you which to protect against exceptions. The handler of the exception is to
    display an :class:`ErrorDialog` with the exception information.
    Example::

        @protect
        def turnBeamOn(ctrl_obj):
            result = ctrl_obj.TurnOn()
            if not result:
                raise Exception("Could not turn on beam!")
    """
    if obj is None:
        return functools.partial(protect, title=title, msg=msg, async=async,
                                 re_throw=re_throw)

    if not isinstance(obj, collections.Callable):
        raise TypeError('{!r} is not a callable object'.format(obj))

    @functools.wraps(obj)
    def wrapper(*args, **kwargs):
        try:
            return obj(*args, **kwargs)
        except:
            msgbox = _ProtectErrorDialog(*sys.exc_info())
            if msgbox is None:
                return
            if title is not None:
                msgbox.setWindowTitle(title)
            if msg is not None:
                msgbox.setText(msg)
            if async:
                msgbox.setModal(False)
                msgbox.show()
            else:
                msgbox.exec_()
            if re_throw:
                raise
    return wrapper


class __MessageDialogExceptionPlugin(BaseExceptionPlugin):
    """A callable class that acts as an excepthook that displays an unhandled
    exception in a :class:`ErrorDialog`.

    :param target: callable excepthook that will be called at the end of
                    this hook handling [default: None]
    :type target: callable
    :param title: message box title [default: None meaning use exception value]
    :type name: str
    :param msg: message box text [default: None meaning use exception]"""

    MSG_BOX = None

    def __init__(self, target=None, title=None, msg=None):
        BaseExceptionPlugin.__init__(self, target=target)
        self._title = title
        self._msg = msg

    def _getMessageBox(self, err_type=None, err_value=None, err_traceback=None,
                       parent=None):
        box = self.__class__.MSG_BOX

        if box is None:
            self.__class__.MSG_BOX = box = ErrorDialog(err_type=err_type,
                err_value=err_value, err_traceback=err_traceback,
                parent=parent)
            box.setModal(False)
        else:
            box.setError(err_type=err_type, err_value=err_value,
                         err_traceback=err_traceback)
        if box.panel().checkBoxState() == QtCore.Qt.Checked:
            return
        return box

    def handle(self, *exc_info):
        app = Application()
        if app is None:
            return
        msgbox = self._getMessageBox(*exc_info)
        if msgbox is None:
            return
        if self._title is not None:
            msgbox.setWindowTitle(self._title)
        if self._msg is not None:
            msgbox.setText(self._msg)
        msgbox.show()
        return True


#------------------------------------------------------------------------------
# Demonstration
#------------------------------------------------------------------------------


def main():
    class __DemoException(Exception):
        pass

    def s1():
        return s2()

    def s2():
        return s3()

    def s3():
        raise __DemoException("A demo exception occurred")

    def py_exc():
        try:
            s1()
        except:
            msgbox = ErrorDialog(*sys.exc_info())
            msgbox.exec_()

    def tg_exc():
        try:
            import PyTango
            PyTango.Except.throw_exception('TangoException',
                                           'A simple tango exception',
                                           'right here')
        except PyTango.DevFailed:
            msgbox = ErrorDialog(*sys.exc_info())
            msgbox.exec_()

    def tg_serv_exc():
        try:
            import PyTango
            dev = PyTango.DeviceProxy("sys/tg_test/1")
            dev.read_attribute("throw_exception")
        except PyTango.DevFailed:
            msgbox = ErrorDialog(*sys.exc_info())
            msgbox.exec_()
        except:
            msgbox = ErrorDialog(*sys.exc_info())
            msgbox.exec_()

    def py_tg_serv_exc():
        try:
            import PyTango
            PyTango.Except.throw_exception('TangoException',
                                        'A simple tango exception',
                                        'right here')
        except PyTango.DevFailed as df1:
            try:
                import StringIO
                origin = StringIO.StringIO()
                traceback.print_stack(file=origin)
                origin.seek(0)
                origin = origin.read()
                PyTango.Except.re_throw_exception(df1, 'PyDs_Exception',
                                                  'DevFailed: A simple tango '
                                                  'exception', origin)
            except PyTango.DevFailed:
                msgbox = ErrorDialog(*sys.exc_info())
                msgbox.exec_()

    app = Application()
    app.setApplicationName("Message dialog demo")
    app.setApplicationVersion("1.0")

    panel = QtGui.QWidget()
    layout = QtGui.QVBoxLayout()
    panel.setLayout(layout)

    m1 = QtGui.QPushButton("Python exception")
    layout.addWidget(m1)
    m1.clicked.connect(py_exc)
    m2 = QtGui.QPushButton("Tango exception")
    layout.addWidget(m2)
    m2.clicked.connect(py_exc)
    layout.addWidget(m2)
    m3 = QtGui.QPushButton("Tango server exception")
    layout.addWidget(m3)
    m3.clicked.connect(tg_serv_exc)
    layout.addWidget(m3)
    m4 = QtGui.QPushButton("Python tango server exception")
    layout.addWidget(m4)
    m4.clicked.connect(py_tg_serv_exc)
    layout.addWidget(m4)

    panel.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
