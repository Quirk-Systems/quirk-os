"""One authenticated local RPC. Role is never supplied by the client."""
from __future__ import annotations

import argparse
import json
import socket
import struct
import sys
from pathlib import Path

from .broker import MAX_MESSAGE, CONFIG_KEYS, protected, read_file
from .model import Denied, canonical, decode_json, exact, integer


def config(path: str) -> dict:
    location = Path(path)
    protected(location, {0}, 0)
    value = exact(decode_json(read_file(location, 16384).decode("utf-8")), CONFIG_KEYS)
    integer(value["broker_uid"], 1, 2**31 - 1)
    return value


def rpc(settings: dict, message: dict) -> dict:
    wire = (canonical(message) + "\n").encode("utf-8")
    if len(wire) > MAX_MESSAGE:
        raise Denied("MESSAGE_TOO_LARGE")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(5)
        connection.connect(settings["socket_path"])
        _, uid, _ = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        if uid != settings["broker_uid"]:
            raise Denied("WRONG_BROKER_IDENTITY")
        connection.sendall(wire)
        with connection.makefile("rb") as stream:
            response = stream.readline(MAX_MESSAGE + 1)
        if len(response) > MAX_MESSAGE or not response.endswith(b"\n"):
            raise Denied("INVALID_RESPONSE")
        return decode_json(response.decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    response = rpc(config(args.config), decode_json(sys.stdin.read(MAX_MESSAGE + 1)))
    print(json.dumps(response, sort_keys=True))
    return 0 if response.get("ok") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
