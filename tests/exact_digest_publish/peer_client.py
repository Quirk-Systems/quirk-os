"""Trusted test driver run after the supervisor drops to one fixture UID.

This helper deliberately has no broker imports, store handles, or credentials.
All broker requests travel through the actual Unix socket.
"""

import errno
import json
import os
import socket
import sys


def rpc(socket_path, request):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(10)
        client.connect(socket_path)
        client.sendall(json.dumps(request, separators=(",", ":")).encode() + b"\n")
        response = bytearray()
        while b"\n" not in response:
            block = client.recv(65536)
            if not block:
                raise ConnectionError("broker closed without a complete response")
            response.extend(block)
        return json.loads(bytes(response).split(b"\n", 1)[0])


def run(command):
    mode = command["mode"]
    if mode == "identity":
        return {"uid": os.getuid(), "euid": os.geteuid(), "gid": os.getgid(),
                "groups": os.getgroups(), "environment_keys": sorted(os.environ)}
    if mode == "rpc":
        return rpc(command["socket_path"], command["request"])
    if mode == "repeat_rpc":
        results = [rpc(command["socket_path"], command["request"])
                   for _ in range(command["count"])]
        return {"count": len(results),
                "all_ok": all(result.get("ok") is True for result in results),
                "failures": [result for result in results if result.get("ok") is not True]}
    if mode == "write_probes":
        results = {}
        for name, path in command["paths"].items():
            try:
                # Opening for writing is itself a kernel permission check. Do
                # not damage the fixture if a regression unexpectedly allows it.
                fd = os.open(path, os.O_WRONLY | os.O_CREAT, 0o600)
            except OSError as error:
                results[name] = {"denied": error.errno in (errno.EACCES, errno.EPERM),
                                 "errno": error.errno}
            else:
                os.close(fd)
                results[name] = {"denied": False, "errno": None}
        return results
    if mode == "impersonate":
        try:
            os.setuid(command["target_uid"])
        except OSError as error:
            denied = error.errno in (errno.EACCES, errno.EPERM)
            reason = error.errno
        else:
            denied, reason = False, None
        return {"setuid_denied": denied, "errno": reason, "uid": os.getuid(),
                "response": rpc(command["socket_path"], command["request"])}
    raise ValueError("unknown fixture mode")


if __name__ == "__main__":
    try:
        result = run(json.load(sys.stdin))
    except Exception as error:
        result = {"transport_error": type(error).__name__, "detail": str(error)}
    print(json.dumps(result, sort_keys=True))
