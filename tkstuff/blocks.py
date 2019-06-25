"""Some prepared widgets, forms and functions"""

import tkinter as tk
import misc.tk as mtk
import misc.tk.forms as mtkf

class PasswordEntry(tk.Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, show='*', **kwargs)


IntEntry = mtk.ValidatedWidget.new_cls(tk.Entry, misc.Validator(int))


class LoginForm(mtkf.Form):
    username: mtkf.Element = tk.Entry
    password: mtkf.Element = PasswordEntry
