"""An extension to tkinter.simpledialog"""

import tkinter as tk
import tkinter.simpledialog as tk_dia
import misc.tkstuff as mtk
import misc.tkstuff.forms as mtkf

class UserExitiedDialog(Exception):
    pass


class FormDialog(tk_dia.Dialog):
    """A dialog for forms"""
    def __init__(self, parent, form, title=None):
        self.form_onsubmit = form._Form__formwidget_options.get('onsubmit')
        form._Form__formwidget_options['onsubmit'] = self.ok
        self.form = form
        super().__init__(parent, title=title)

    def body(self, master):
        self.form_widget = self.form(master)
        self.form_widget.pack()

    def buttonbox(self):
        pass

    def apply(self):
        if self.form_onsubmit is not None:
            self.form_onsubmit(self.form_widget.data)
        self.result = self.form_widget.data


class WidgetDialog(tk_dia.Dialog):
    """A dialog for getting input from any widget"""
    def __init__(self, parent, widget, widget_kw={}, title=None, getter=None):
        self.widget_cls = widget
        self.widget_cnf = widget_cnf
        self.getter = mtk.get_getter(widget, getter)
        super().__init__(parent, title)

    def body(self, master):
        self.widget = self.widget_cls(master, **self.widget_kw)
        self.widget.pack()

    def validate(self):
        try:
            return self.widget.validate()[0]
        except AttributeError:
            return True

    def apply(self):
        self.result = self.getter(self.widget)
