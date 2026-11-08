"""Run Python inside the open Maya, through a Maya command port.

Maya must have a local Python command port open. Once per Maya session, in the
Script Editor (Python tab):

    import maya.cmds as cmds; cmds.commandPort(name="localhost:7001", sourceType="python")

Then, from a terminal:

    mayapy Tools/maya/send_to_maya.py --ping
    mayapy Tools/maya/send_to_maya.py "print(cmds.ls(type='mesh'))"
    mayapy Tools/maya/send_to_maya.py -f path/to/script.py

`cmds` is already imported and this folder is on sys.path. Prints whatever the
code prints; exits 1 if the code raised.
"""
import argparse
import os
import socket
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

# Runs inside Maya: execs the code, writes its output (or traceback) to a file
# that this script then reads back.
RUNNER = (
    "import sys, io, traceback\n"
    "_sd_buf = io.StringIO(); _sd_old = sys.stdout; sys.stdout = _sd_buf\n"
    "try:\n"
    "    import maya.cmds as cmds\n"
    "    if {here!r} not in sys.path: sys.path.insert(0, {here!r})\n"
    "    exec(compile({code!r}, {name!r}, 'exec'), {{'cmds': cmds, '__name__': '__main__'}})\n"
    "    _sd_ok = 'OK'\n"
    "except Exception:\n"
    "    traceback.print_exc(file=_sd_buf); _sd_ok = 'FAIL'\n"
    "finally:\n"
    "    sys.stdout = _sd_old\n"
    "with open({out!r}, 'w', encoding='utf-8') as _sd_f: _sd_f.write(_sd_ok + '\\n' + _sd_buf.getvalue())\n"
)


def send(port, text, timeout):
    with socket.create_connection(("127.0.0.1", port), timeout=timeout) as sock:
        sock.sendall(text.encode("utf-8"))
        return sock.recv(65536).decode("utf-8", "replace")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("code", nargs="?", help="Python statements to run in Maya")
    parser.add_argument("-f", "--file", help="Python file to run in Maya")
    parser.add_argument("--ping", action="store_true", help="only check that Maya answers")
    parser.add_argument("--port", type=int, default=7001)
    parser.add_argument("--timeout", type=float, default=120, help="seconds to wait for Maya (default 120)")
    args = parser.parse_args()
    if not (args.code or args.file or args.ping):
        parser.error("give code, -f FILE or --ping")

    if args.ping:
        code, name = "print('Maya is answering:', cmds.about(version=True))", "<ping>"
    elif args.file:
        with open(args.file, encoding="utf-8") as f:
            code, name = f.read(), os.path.abspath(args.file)
    else:
        code, name = args.code, "<command>"

    fd, out = tempfile.mkstemp(prefix="send_to_maya_", suffix=".txt")
    os.close(fd)
    try:
        send(args.port, RUNNER.format(here=HERE, code=code, name=name, out=out), args.timeout)
        with open(out, encoding="utf-8") as f:
            status, _, output = f.read().partition("\n")
    except (ConnectionRefusedError, socket.timeout):
        print("Maya not found on port %d. Open the command port in Maya's Script Editor (see --help)." % args.port)
        return 2
    finally:
        os.remove(out)
    print(output.rstrip())
    return 0 if status == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
