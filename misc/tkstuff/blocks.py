"""Some prepared widgets, forms and functions"""

import tkinter as tk
import misc.validation as mval
import misc.tkstuff as mtk
import misc.tkstuff.forms as mtkf

class PasswordEntry(tk.Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, show='*', **kwargs)


def type_entry(cls):
    return mtk.ValidatedWidget.new_cls(tk.Entry, mval.Validator(cls))


IntEntry = type_entry(int)
FloatEntry = type_entry(float)


class LoginForm(mtkf.Form):
    username: mtkf.Element = tk.Entry
    password: mtkf.Element = PasswordEntry
