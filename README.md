# misc-utils
Miscellaneous stuff I wrote, mostly for tkinter

Includes:

- in the main module:
  - a table display for a terminal
  - various class wrappers
  - multiline input
  - a Tree
  - a class for delayed lookup evaluation
- a timer module, extensible but also working out of the box
- in a validation module
  - a general Validator (factory for the following)
  - a condition-based Validator
  - a conversion-based Validator
  - a MultiValidator for combining the above
- tkinter extensions (<del>may</del> probably will explode in your face):
  - container widgets
  - wrapping widgets
  - validated widgets
  - scrolled widgets
  - single widget for radio button groups (probably the most safe to use)
  - FormWidget and an extensible factory
  - dialogs for forms and arbirtary widgets
  - some pre-prepared cominations of the above: IntEntry, FloatEntry, PasswordEntry, LoginForm
