"""Validation"""

from misc import Instance


class MultiValidator:
    """Chain multiple validators"""
    def __init__(self, *validators):
        """Create a new MultiValidator

            `validators` are single validators to be chained"""
        self.validators = validators

    def __call__(self, value):
        for validator in self.validators:
            good, value = validator(value)
            if not good:
                return False, value
        return True, value


class ConditionValidator:
    """validate based on a user-defined condition"""
    def __init__(self, *conditions):
        """Create a new ConditionValidator.

            `conditions` are iterables of the form
                (<condition>, <error message>), where <condition>
                is a delayed evaluation using `misc.Instance`
                that yields a value to used in boolean context
                indicating whether the value passed is valid
                e.g. Instance().attr['key'] == 'someval'
                <error message> is the error message to return
                if the condition resolves to a falsey value
            """
        self.conditions = conditions

    def __call__(self, value):
        for cond, msg in self.conditions:
            if not Instance.lookup(cond, value):
                return False, msg
        return True, value


class TransformValidator:
    """validate based on transformation"""
    def __init__(self, *transformations):
        """Create a new TransformValidator

            `transformations` are callables taking as single argument
                the user input and returning the transformed input.
                They may also be tuples of the form (<callable>, <config>)
                where <callale> is the callable described above
                and <config> is a mapping from exceptions that may occur
                during the transformation to error messages or tuples of
                multiple such exceptions.
                The default maps (ValueError, TypeError) to
                'Must be of type <name>' with <name> replaced by
                the callables __name__, making it suitable for types.
            """
        default_config = {(ValueError, TypeError): 'Must be of type {__name__}',
                         }
        self.trans = []
        self.configs = []
        for t in transformations:
            config = default_config.copy()
            if isinstance(t, tuple):
                t, new_cnf = t
                config.update(new_cnf)
            self.trans.append(t)
            self.configs.append(config)

    def __call__(self, value):
        for trans, cnf in zip(self.trans, self.configs):
            try:
                value = trans(value)
            except Exception as e:
                for exc, msg in cnf.items():
                    if isinstance(e, exc):
                        return False, msg.format(__name__=trans.__name__,
                                                 value=value,
                                                 )
                raise
        return True, value
