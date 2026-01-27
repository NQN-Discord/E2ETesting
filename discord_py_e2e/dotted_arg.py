from typing import Callable

import parse
import behave

from discord_py_e2e.context import Context

type Args[T] = Callable[[Context], T]


class _DotAccessDict:
    def __init__(self, args):
        self.args = args

    def __getitem__(self, key):
        if "." in key:
            obj_name, *attrs = key.split(".")
            if obj_name in self.args:
                obj = self.args[obj_name]
                for part in attrs:
                    obj = getattr(obj, part)
                return obj
            return f"{{{key}}}"

        return self.args[key]


@parse.with_pattern(r"{(?:\w|.)+}")
def _dotted_arg(arg: str):
    arg = arg.strip("{}")

    def inner(context: Context):
        dotted_arg = _DotAccessDict(context.args)
        return dotted_arg[arg]

    return inner


@parse.with_pattern(r"'.+'")
def _dotted_args(template: str):
    template = template.strip("'")
    def inner(context: Context):
        return template.format_map(_DotAccessDict(context.args))

    return inner


behave.register_type(arg=_dotted_arg)
behave.register_type(args=_dotted_args)
