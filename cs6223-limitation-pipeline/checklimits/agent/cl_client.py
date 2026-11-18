"""Client of the cl service (checklimits/agent_service.py): sends the command over the Unix socket named by CL_SOCKET and
prints what the harness answered. Standard library only; it holds no harness code."""
import json
import os
import socket
import sys


def main() -> int:
    path = os.environ.get("CL_SOCKET")
    if not path:
        print("cl: CL_SOCKET is not set", file=sys.stderr)
        return 2
    with socket.socket(socket.AF_UNIX) as s:
        s.settimeout(2400)
        s.connect(path)
        s.sendall((json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd()}) + "\n").encode())
        data = b""
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            data += chunk
    r = json.loads(data.decode())
    sys.stdout.write(r["stdout"])
    sys.stderr.write(r["stderr"])
    return int(r["rc"])


if __name__ == "__main__":
    sys.exit(main())
