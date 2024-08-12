import sys
from pathlib import Path
from typing import Callable, Optional, List
from dataclasses import dataclass
from icecream import ic
from code import InteractiveConsole

@dataclass
class NanoPDBContinue:
    exit: bool = False

# NanoPDB V0: static breakpoints
class NanoPDB:
    def __init__(self):
        self._in_breakpoint = False

    def _eval(self, _locals: dict, message: str):
        try:
            print(message)
            InteractiveConsole(locals=_locals).interact(banner="", exitmsg="")
        except SystemExit as e:
            if isinstance(e.args[0], NanoPDBContinue):
                if e.args[0].exit:
                    exit()
            else:
                exit(e.args)

    def _breakpoint(self, *args, **kwargs):
        if self._in_breakpoint:
            return

        frame = sys._getframe(1)
        location = f"{frame.f_code.co_filename}:{frame.f_lineno} ({frame.f_code.co_name})"

        helpers = {}

        def add_helper(f: Callable) -> Callable:
            helpers[f.__name__.lstrip("_")] = f
            return f

        @add_helper
        def _location():
            """ show the current location
            """
            return location

        @add_helper
        def _locals():
            return frame.f_locals

        @add_helper
        def _glocals():
            return frame.f_globals

        @add_helper
        def _cont():
            """continue the program execution"""
            raise SystemExit(NanoPDBContinue(exit=False))

        @add_helper
        def _exit():
            """continue the program execution"""
            raise SystemExit(NanoPDBContinue(exit=True))

        self._in_breakpoint = True
        message = f"breakpoint at {location}"
        self._eval(_locals=frame.f_locals | frame.f_globals | helpers, message=message)
        self._in_breakpoint = False

    def run(self, _globals):
        file = Path(sys.argv[0])
        compiled = compile(file.read_text(), filename=file.name, mode="exec")
        sys.breakpointhook = self._breakpoint
        exec(compiled, _globals)
