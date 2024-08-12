import sys
from pathlib import Path
from typing import Callable, Optional, List, Dict, Set, Tuple
from dataclasses import dataclass
from icecream import ic
from code import InteractiveConsole
import types
import inspect
import re
import tokenize


@dataclass
class NanoPDBContinue:
    exit: bool = False


# NanoPDB V2: conditional brakpoints
class NanoPDB:
    def __init__(self):
        self._main_file: Optional[Path] = None
        self._in_breakpoint = False
        self._is_first_call = True

        # file -> {line numbers of breakpoints}
        self._breakpoints_in_files: Dict[Path, Set[int]] = {}
        self._breakpoint_conditions: Dict[Tuple[Path, int], str] = {}

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

    def add_breakpoint(self, file: str, line: int, condition: Optional[str]):
        p = Path(file)
        if p not in self._breakpoints_in_files:
            self._breakpoints_in_files[p] = set()
        if line in self._breakpoints_in_files[p]:
            print(f"Breakpoint {file}:{line} already set")
            if condition:
                self._breakpoint_conditions[(p, line)] = condition
                print("Condition updated")
            return
        self._breakpoints_in_files[p].add(line)
        if condition:
            self._breakpoint_conditions[(p, line)] = condition
        if condition:
            print(f"Breakpoint at {file}:{line} if {condition}")
        else:
            print(f"Breakpoint at {file}:{line}")

    def remove_breakpoint(self, file: str, line: int):
        p = Path(file)
        if p in self._breakpoints_in_files:
            self._breakpoints_in_files[p].remove(line)
            del self._breakpoint_conditions[(p, line)]
            print(f"Breakpoint {file}:{line} removed")
        else:
            print(f"Breakpoint {file}:{line} does not exist")

    def get_breakpoints(self) -> List[Tuple[Path, int, Optional[str]]]:
        breakpoints = []
        for p in self._breakpoints_in_files.keys():
            for line in self._breakpoints_in_files[p]:
                if (p, line) in self._breakpoint_conditions:
                    breakpoints.append(
                        (p, line, self._breakpoint_conditions[(p, line)])
                    )
                else:
                    breakpoints.append((p, line, None))

        return breakpoints

    def _breakpoint(
        self, frame: types.FrameType = None, reason: str = "breakpoint", *args, **kwargs
    ):
        if self._in_breakpoint:
            return

        frame = frame or sys._getframe(1)
        location = (
            f"{frame.f_code.co_filename}:{frame.f_lineno} ({frame.f_code.co_name})"
        )

        helpers = {}

        def add_helper(f: Callable) -> Callable:
            helpers[f.__name__.lstrip("_")] = f
            return f

        @add_helper
        def _cont():
            """continue the program execution"""
            raise SystemExit(NanoPDBContinue(exit=False))

        @add_helper
        def _exit():
            """continue the program execution"""
            raise SystemExit(NanoPDBContinue(exit=True))

        @add_helper
        def _location():
            """show the current location"""
            return location

        @add_helper
        def _locals():
            return frame.f_locals

        @add_helper
        def _glocals():
            return frame.f_globals

        @add_helper
        def break_at_line(line: int, condition: Optional[str] = None):
            file = frame.f_code.co_filename
            self.add_breakpoint(file, line, condition)

        @add_helper
        def break_at_file_line(file: str, line: int, condition: Optional[str] = None):
            self.add_breakpoint(file, line, condition)

        @add_helper
        def list_break():
            breakpoints = self.get_breakpoints()
            if len(breakpoints) == 0:
                print("There is no breakpoint")
                return
            for bk in breakpoints:
                path, line, condition = bk
                if condition is None:
                    print(f"Break at {path}:{line}")
                else:
                    print(f"Break at {path}:{line} if {condition}")

        self._in_breakpoint = True
        message = f"breakpoint at {location}"
        self._eval(_locals=frame.f_locals | frame.f_globals | helpers, message=message)
        self._in_breakpoint = False

    def _should_break_at(self, frame: types.FrameType):
        p = Path(frame.f_code.co_filename)
        line = frame.f_lineno
        if p in self._breakpoints_in_files and line in self._breakpoints_in_files[p]:
            if (p, line) in self._breakpoint_conditions:
                return eval(
                    self._breakpoint_conditions[(p, line)],
                    frame.f_globals,
                    frame.f_locals,
                )
            return True
        return False

    def _handle_line(self, frame: types.FrameType):
        if self._should_break_at(frame):
            self._breakpoint(frame, reason="breakpoint")

    def _default_dispatch(self, frame: types.FrameType, event: str, arg):
        # return a reference to a trace function
        if event == "call":
            return self._dispatch_trace

    def _dispatch_trace(self, frame: types.FrameType, event: str, arg):
        # event is a string: 'call', 'line', 'return', 'exception' or 'opcode'.
        # The trace function is invoked (with event set to 'call') whenever a new local scope is entered;
        # it should return a reference to a local trace function to be used for the new scope, or None if the scope shouldn’t be traced.
        # Typically, we can return the trace function itself.

        # (Tip) uncomment the follwing three lines to see how `sys.settrace` works if we return None.
        # All event types show be `call`.
        # location = f"{frame.f_code.co_filename}:{frame.f_lineno} ({frame.f_code.co_name})"
        # print(f"event: {event}, location: {location}")
        # return

        # (Tip) uncomment the follwing three lines to see how `sys.settrace` works if we return the trace function itself.
        # location = f"{frame.f_code.co_filename}:{frame.f_lineno} ({frame.f_code.co_name})"
        # print(f"event: {event}, location: {location}")
        # return self._default_dispatch(frame, event, arg)

        # frame.f_back: pointer to the last frame
        # do not trace when exit the target file
        if (
            event == "return"
            and frame.f_code.co_name == "<module>"
            and frame.f_back
            and frame.f_back.f_code.co_filename == __file__
        ):
            return

        if self._is_first_call:
            # break at entrance
            assert self._main_file == frame.f_code.co_filename
            self._is_first_call = False
            self._breakpoint(frame, reason="start")
            return self._default_dispatch(frame, event, arg)

        if event == "call":
            return self._default_dispatch(frame, event, arg)
        elif event == "line":
            self._handle_line(frame)

    def run(self, _globals):
        file = Path(sys.argv[0])
        self._main_file = file.name
        # see https://realpython.com/python-exec/#using-python-for-configuration-files
        compiled = compile(file.read_text(), filename=file.name, mode="exec")
        sys.breakpointhook = self._breakpoint
        # see https://docs.python.org/3.11/library/sys.html#sys.settrace
        sys.settrace(self._dispatch_trace)
        exec(compiled, _globals)
