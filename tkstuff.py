"""Some utilities for tkinter

Most of these are developed "on the go", so only the methods I actually
use(d) will be overridden (if applicable)"""

import tkinter as tk

from functools import wraps
import types
import enum

GEOMETRY_MANAGERS = ('grid', 'pack', 'place')
GEOMETRY_MANAGERS_FORGET = [(n, n+'_forget') for n in GEOMETRY_MANAGERS]


def modify_call(clsnames_):
    class OnlyNewOnCall(type):
        clsnames = clsnames_
        def __call__(self, *args, **kwargs):
            if any(self.__name__.endswith(n) for n in self.clsnames):
                return self.__new__(self, *args, **kwargs)
            else:
                r = super().__call__(*args, **kwargs)
                return r
    return OnlyNewOnCall


def add_new_override(cls):
    if type(cls).__name__ == 'OnlyNewOnCall':
        type(cls).clsnames.append(cls.__name__)


class ContainingWidget(tk.Widget):
    """Provide a widget that includes other widgets.

    Currently applies .grid(), .pack() and .place() and their respecive .*_forget()
    Other calls and attribute lookups are delegated to the base widget"""
    def __init__(self, master, *widgets,
                 direction=(tk.RIGHT, tk.BOTTOM),
                 horizontal=0,
                 vertical=0,
                 base=tk.Frame):
        """Create a multiwidget

        `widgets` are (<class>, <kwargs>) of the contined widgets
            if positional arguemnts are needed, they may be included
            under the key '**args**' (clash-safe)
        `direction` is a tuple of two elements, respectively one of
            (TOP, BOTTOM) or (RIGHT, LEFT) or the inverse
            and indicates in which direction the contained widgets
            will be displayed: the first element specifies the
            first direction, when the maximum number of widgets for this
            direction is reached, the next row/column is selected by the
            second element
            e.g.: 
                (RIGHT, BOTTOM) will fill out left to right, then top to bottom
                (TOP, RIGHT) will fill out bottom to top, then left to right
            note the second element is ignored if the number of widgets for
            the first direction is unlimited
        `horizontal` and `vertical` specify the maximum number of widgets in
            their respective direction. They must allow space for all widgets
            and it is advised to set at most one of them. A value of 0 means
            an unlimited number of widgets may be positioned in that direction.
        `base` is the widget to use as container"""
        self.base = base(master)
        self.base.container_widget = self
        self.widgets = tuple(w[0](self.base,
                                  *w[1].pop('**args**', ()),
                                  **w[1]) for w in widgets)
        self.direction = direction
        self.horizontal = horizontal
        self.vertical = vertical

    def __getattr__(self, name):
        return getattr(self.base, name)

    def _geo_wrapper(name, forget):
        def wrapper(self, *args, **kwargs):
            getattr(self.base, name)(*args, **kwargs)
            self._grid_subwidgets()
        wrapper.__name__ = name
        wrapper.__doc__ = """.{}() the base widget and .grid() the subwidgets.

                            respect the directions given in __init__
                            pass *args and **kwargs to the base widget
                            """.format(name)
        def forgetter(self):
            getattr(self.base, forget)()
            for widget in self.widgets:
                widget.grid_forget()
        forgetter.__name__ = forget
        forgetter.__doc__ = ".{}() the base widget and .grid_forget() the subwidgets".format(forget)
        return wrapper, forgetter

    for name, forget in GEOMETRY_MANAGERS_FORGET:
        locals()[name], locals()[forget] = _geo_wrapper(name, forget)
    del _geo_wrapper

    def _grid_subwidgets(self):
        """.grid() the subwidgets according to `self.direction`, `self.horizontal` and `self.vertical`"""
        # x and y _S_tart and _I_ncrement
        if tk.RIGHT in self.direction:
            xs = 0
            xi = 1
        elif tk.LEFT in self.direction:
            if self.horizontal:
                xs = self.horizontal-1
            else:
                xs = len(self.widgets)-1
            xi = -1
        if tk.TOP in self.direction:
            if self.vertical:
                ys = self.vertical-1
            else:
                ys = len(self.widgets)-1
            yi = -1
        elif tk.BOTTOM in self.direction:
            ys = 0
            yi = 1
        try:
            xs, ys
        except NameError:
            raise ValueError('`direction` must be of the form specified in __init__')
        x, y = xs, ys
        for widget in self.widgets:
            # multi-depth WrappedWidget. Find the actual container
            while widget not in self.base.children.values():
                widget = widget.master
            widget.grid(row=y, column=x)
            if self.direction[0] in (tk.RIGHT, tk.LEFT):
                x += xi
            elif self.direction[0] in (tk.TOP, tk.BOTTOM):
                y += yi
            if y in (-1, self.vertical or None):
                y = ys
                x += xi
            if x in (-1, self.horizontal or None):
                x = xs
                y += yi


class ProxyWidget(tk.Widget):
    """Provide a widget that delegates some lookups to a .container
        in a way compatile with ContainningWidget

        the delegated lookups are:
        - .grid, .pack, .place and their .*_forget counterparts
        - .destroy

        the methods are wrapped in the following way:
            The first call gets send to .container, the second one is actually
            handled by the superclass.

        i.e. The method will first be passed to self.container and executed
            on super() at the second call"""
    def __init__(self, *args, container=None, **kwargs):
        """Create a new ProxyWidget. `container` is the container,
            other arguments are passed along"""
        super().__init__(*args, **kwargs)
        if container is not None:
            self.container = container

    def _geo_wrapper(name, forget):
        def wrapper(self, *args, **kwargs):
            if self.__visible == 1:
                self.__visible = 2
                getattr(super(), name)(*args, **kwargs)
            elif self.__visible == 0:
                self.__visible = 1
                getattr(self.container, name)(*args, **kwargs)
        def forgetter(self):
            if self.__visible == 2:
                self.__visible = 1
                getattr(self.container, forget)()
            elif self.__visible == 1:
                self.__visible = 0
                getattr(super(), forget)()
        wrapper.__name__ = name
        forgetter.__name__ = forget
        return wrapper, forgetter

    __visible = False
    for name, forget in GEOMETRY_MANAGERS_FORGET:
        locals()[name], locals()[forget] = _geo_wrapper(name, forget)
    del _geo_wrapper


class BaseWrappedWidget(ProxyWidget, metaclass=modify_call(
        ['BaseWrappedWidget', 'WrappedWidget', 'LabeledWidget'])):
    """Provide a widget that is contained inside a
        ContainingWidget along others but provides normal access"""

    #@classmethod  # __new__ is complicated because the class is istantiated later
    def __new__(cls, master, main_widget, *auxiliary_widgets, container_kw={}):
        """Create a new WrappedWidget.

        The resulting widget is a subclass of the main widget.
        The containing widget (and, through it, the auxiliary widgets)
            is accessible through .container

        `main_widget` and each of the `auxiliary_widgets`
            are (<class>, <kwargs>)"""
        main_cls, main_kw = main_widget
        main_cls = type('Wrapped'+main_cls.__name__,
                        (main_cls, cls),
                        {'__new__': main_cls.__new__,
                         '__init__': main_cls.__init__
                         })
        container = ContainingWidget(master,
                                     (main_cls, main_kw),
                                     *auxiliary_widgets,
                                     **container_kw)
        self = container.widgets[0]
        self.container=container
        return self


class WrappedWidget(BaseWrappedWidget):
    pass


class LabeledWidget(BaseWrappedWidget):
    """Convenience class for widgets to be displayed with a Label"""
    def __new__(cls, master, widget, text, **options):
        """Create a new WrappedWidget with a Label with the selected text.

            `options` are passed
            by default, the Label is shown to the left, this may be overridden in `options`"""
        kw = {'direction': (tk.LEFT, tk.BOTTOM)}
        kw.update(options)
        return super().__new__(cls, master, widget, (tk.Label, {'text': text}),
                           container_kw=kw)


class ScrollableWidget(tk.Widget):
    """Provide a scrollable widget.

        create a ContainingWidget with a canvas and a scrollbar and add the
        given widget to the canvas. Attach the apropriate methods.

        This class is to be used as a decorator/wrapper:
        
            >>> @ScrollableWidget(...)
            ... class MyWidget(tk.Widget):
            ...     def stuff(self, *args):
            ...         self.magic(*args)

            >>> ScrollableLabel = ScrollableWidget(...)(tk.Label)

        +-------------------------------------------------+
        | WARNING: multiple calling of a geometry manager |     
        |          *will*  *mess*  *things*  *up*         |
        +-------------------------------------------------+"""
    def __init__(self, direction=tk.VERTICAL, width=None, height=None):
        self.direction = {tk.VERTICAL: 'y', tk.HORIZONTAL: 'x'}[direction]
        self.width = width
        self.height = height

    def __call__(self, wrapped_cls):
        class NewClass(ProxyWidget, wrapped_cls):
            def __new__(cls, master, cnf={}, **kw):
                container = ContainingWidget(master,  # attention: order matters and is used
                                             (tk.Canvas, {'width': self.width,
                                                          'height': self.height}),
                                             (tk.Scrollbar, {})
                                             )
                canvas, scrollbar = container.widgets
                canvas.config(**{self.direction+'scrollcommand': scrollbar.set})
                scrollbar.config(command=getattr(canvas, self.direction+'view'))
                inst = wrapped_cls.__new__(cls)
                inst.container = container  # other init done afterwards
                return inst

            def __init__(self, master=None, cnf={}, **kw):
                super().__init__(master, cnf, **kw)
                self.container.widgets[0].create_window((0, 0), window=self)
                

            def set_scrollregion(self):
                canvas = self.container.widgets[0]
                sw, sh = self.winfo_width(), self.winfo_height()
                canvas.config(scrollregion=(-sw//2, -sh//2, sw//2, sh//2))

            def _wait_for_scrollregion(self, t, initial, ct=10):
                if (self.winfo_width(), self.winfo_height()) == (1, 1) and ct:
                    self.after(t, self._wait_for_scrollregion, t, initial, ct-1)
                else:
                    self.set_scrollregion()

            def _geo_wrapper(name, forget):
                def wrapper(self, *args, **kwargs):
                    initial = self.winfo_width(), self.winfo_height()
                    getattr(super(), name)(*args, **kwargs)
                    self.container.widgets[1].grid(row=0, column=1, sticky=tk.NS)
                    self.after(0, self._wait_for_scrollregion, 1, initial)
                wrapper.__name__ = name
                def wrapper_forget(self):
                    getattr(self.container, forget)()
                wrapper_forget.__name__ = forget
                return wrapper, wrapper_forget

            for name, forget in GEOMETRY_MANAGERS_FORGET:
                locals()[name], locals()[forget] = _geo_wrapper(name, forget)
            del _geo_wrapper

        NewClass.__name__ = 'Scrollable'+wrapped_cls.__name__
        return NewClass
        


class ValidatedWidget(tk.Widget):
    """A widget which validates its input"""
    @classmethod
    def new_cls(cls, widget, validator, getter=None):
        """Create a new widget class

            create a dynamic subclass of VilidatedWidget and the passed `widget`
            `validator` should take the widget's input
                and may also be set on instances separately
            `getter` provides the name of the function to use for getting
                input from the widget. If it is None, .get() and
                .curselection() are tried"""
        def __init__(self, master=None, cnf={}, validator=None, **kw):
            """Initialize self.

                if `validator` is not None, it overrides the default set in the class
                all other arguments are passed to `widget.__init__`"""
            if validator is not None:
                self.validator = validator
            widget.__init__(self, master, cnf, **kw)
        if getter is None:
            try:
                getter = widget.get
            except AttributeError:
                try:
                    getter = widget.curselection
                except AttributeError:
                    raise AttributeError('Neither a .get() nor a .curselection()'
                                         ' were found. Please specify its name '
                                         'in `getter`')
        else:
            getter = getattr(widget, getter)
        return type('Validated{}Widget'.format(widget.__name__),
                       (cls, widget),
                       {'__new__': object.__new__,
                        '__init__': __init__,
                        'getter': getter,
                        'validator': staticmethod(validator)}
                       )

    @classmethod
    def new(cls, master, widget, widgetkw, validator, getter=None):
        """Create a new widget.

            the class is created by cls.new_cls() and then initialized
                with the gven arguements"""
        return cls.new_cls(widget, validator, getter)(master, **widgetkw)
    
    def get(self):
        return self.validator(self.getter())


class RadioChoiceWidget(ContainingWidget):  # yay, no class creation magic, just __init__
    def __init__(self, master, *choices, default=0, **container_kw):
        """Create a new RadioChoiceWidget.

            `choices` are (<code>, <display>). <code> is returned by .get()
                <display> is show to the user
            if `default` is not None, the `default`th (0-index) one will be selected
            `container_kw` will be passed along and may
                e.g. be used to specify directions"""
        self.var = tk.Variable(master)
        rbtn = []
        for code, text in choices:
            rbtn.append((tk.Radiobutton, {'value': code, 'text': text, 'variable': self.var}))
        super().__init__(master, *rbtn, **container_kw)
        if default is not None:
            self.widgets[default].select()

    def get(self):
        return self.var.get()

