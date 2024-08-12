import os
NANOPDB_VERSION = os.environ['NANOPDB_VERSION']
if NANOPDB_VERSION == '0':
    from nanopdb.nanopdb_v0 import NanoPDB
if NANOPDB_VERSION == '1':
    from nanopdb.nanopdb_v1 import NanoPDB
if NANOPDB_VERSION == '2':
    from nanopdb.nanopdb_v2 import NanoPDB
if NANOPDB_VERSION == '3':
    from nanopdb.nanopdb_v3 import NanoPDB
if NANOPDB_VERSION == '4':
    from nanopdb.nanopdb_v4 import NanoPDB
import sys

_usage = """\
Debug the Python program given by pyfile.
usage:
    python -m nanopdb [-h] pyfile [arg] ...
"""

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "-h":
        print(_usage)
        sys.exit(0)

    dbg = NanoPDB()
    try:
        sys.argv.pop(0)
        dbg.run(
            globals().copy()
        )  # we need to copy the global namespace in the file `__main__.py`, coz we need to inherit the key like "__name__"
    except KeyboardInterrupt:
        pass
