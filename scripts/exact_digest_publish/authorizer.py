"""Interactive approval under the separately provisioned authorizer OS identity.

This helper requires an explicit terminal decision. The OS account/session is
the trust root; this is not a biological-human-presence or WebAuthn verifier.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
import uuid

from .client import config, rpc
from .model import Denied, PublicationSubject, decode_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--subject", required=True, help="JSON subject previously returned by stage")
    parser.add_argument("--expires-in", type=int, default=60)
    args = parser.parse_args()
    settings = config(args.config)
    if os.getuid() != settings["authorizer_uid"] or os.geteuid() != settings["authorizer_uid"]:
        raise Denied("AUTHORIZER_IDENTITY_REQUIRED")
    if settings["authority_mode"] != "human_session":
        raise Denied("FIXTURE_AUTHORITY_IS_NOT_HUMAN_APPROVAL")
    data = Path(args.subject).read_bytes()
    if len(data) > 4096:
        raise Denied("SUBJECT_TOO_LARGE")
    subject = PublicationSubject.parse(decode_json(data.decode("utf-8")))
    status = rpc(settings, {"action": "status"})
    if (not status.get("ok") or status["policy_digest"] != subject.policy_digest
            or status["destination_id"] != subject.destination_id):
        raise Denied("STALE_OR_WRONG_SUBJECT")
    if not 1 <= args.expires_in <= status["policy"]["max_grant_seconds"]:
        raise Denied("INVALID_GRANT_LIFETIME")
    # No --yes flag, stdin approval, model callback, or evaluation-to-grant rule.
    # The caller must independently control this authenticated OS session.
    try:
        terminal = open("/dev/tty", "r+", encoding="utf-8", buffering=1)
    except OSError:
        raise Denied("INTERACTIVE_HUMAN_DECISION_REQUIRED") from None
    with terminal:
        if not terminal.isatty():
            raise Denied("INTERACTIVE_HUMAN_DECISION_REQUIRED")
        terminal.write("Approve ONE publication of these exact bytes and scope:\n")
        terminal.write(json.dumps(subject.wire(), indent=2, sort_keys=True) + "\n")
        terminal.write("Allowed uses: 1. Expires in " + str(args.expires_in) + " seconds after confirmation.\n")
        terminal.write("Type approve " + subject.key + " to authorize; anything else cancels:\n")
        if terminal.readline(256).strip() != "approve " + subject.key:
            raise Denied("HUMAN_DECISION_CANCELLED")
    response = rpc(settings, {"action": "grant", "subject": subject.wire(),
                   "grant_id": str(uuid.uuid4()), "expires_at": int(time.time()) + args.expires_in,
                   "scope_digest": subject.key, "decision": "approve"})
    print(json.dumps(response, indent=2, sort_keys=True))
    return 0 if response.get("ok") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
