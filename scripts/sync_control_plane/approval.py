"""Database-backed authorization. The connection is trusted application wiring.

Runtime payloads never supply a registry or database identity. No database means
no authority; no positive decision is cached between invocations.
"""
from __future__ import annotations

import json
from typing import Any


class PostgresApprovalRegistry:
    def __init__(self, connection: Any):
        self.connection = connection

    def allows(self, **binding: Any) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(
                "select quirk_sync.github_approval_allows(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s::jsonb)",
                (binding["grant_id"], binding["subject_kind"], binding["subject_id"],
                 binding["subject_version"], binding["subject_digest"], binding["authority_ceiling"],
                 json.dumps(binding["allowed_actions"]), binding["requested_by"],
                 binding["approved_by"], binding["decision_ref"], json.dumps(binding["subject_contract"])),
            )
            row = cursor.fetchone()
            return bool(row and row[0] is True)


def authorization_errors(registry: Any, **binding: Any) -> list[str]:
    if registry is None:
        return ["trusted GitHub approval registry is required"]
    try:
        if registry.allows(**binding) is True:
            return []
    except Exception:
        # Database failures are denials; do not disclose connection details.
        return ["trusted GitHub approval lookup failed"]
    return ["trusted GitHub approval is absent, mismatched, expired, revoked, or stale"]
