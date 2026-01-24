import asyncio
import sys

from discord_py_e2e.debugger.connection import connect_to_nqn


def _eval(code: str) -> str:
    from __main__ import bot
    import io

    def _get_line(l):
        if l[0] == " " and l[1] != " ":
            return l[1:]
        return l

    def _print(*args, **kwargs):
        with io.StringIO() as output:
            print(*args, file=output, end="", **kwargs)
            return output.getvalue()

    gs = globals() | {"print": _print}
    ls = {}

    lines = code.split(";")
    for line in lines[:-1]:
        exec(_get_line(line), gs, ls)
    try:
        return repr(eval(_get_line(lines[-1]), gs, ls))
    except:
        exec(_get_line(lines[-1]), gs, ls)


async def main():
    evaluator = await connect_to_nqn()
    print(await evaluator.evaluate(_eval, sys.argv[1]))


if __name__ == "__main__":
    asyncio.run(main())
