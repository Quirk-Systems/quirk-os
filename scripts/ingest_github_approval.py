#!/usr/bin/env python3
"""Trusted worker entry point; dry-run verifies but never registers authority."""
import argparse
import json
import os
from datetime import datetime, timezone

from sync_control_plane.github_approval import GitHubAPI, ingest, refresh, verified_record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pr', type=int)
    parser.add_argument('--request-path')
    parser.add_argument('--refresh-grant')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if bool(args.refresh_grant) == bool(args.pr and args.request_path):
        parser.error('use either --pr with --request-path, or --refresh-grant')
    api = GitHubAPI(os.environ['QUIRK_APPROVAL_GITHUB_TOKEN'])
    now = datetime.now(timezone.utc).isoformat()
    if not args.apply:
        if args.refresh_grant:
            parser.error('refresh requires --apply and the isolated ingestor connection')
        record = verified_record(api, args.pr, args.request_path, now=now)
        print(json.dumps({'registered': False, 'verified_candidate': record}, indent=2))
        return
    import psycopg  # Optional trusted-worker dependency; not loaded by runtime validators.
    with psycopg.connect(os.environ['QUIRK_APPROVAL_DATABASE_URL']) as connection:
        if args.refresh_grant:
            valid = refresh(connection, api, args.refresh_grant, now=now)
            print(json.dumps({'grant_id': args.refresh_grant, 'current_approval': valid}))
        else:
            record = ingest(connection, api, args.pr, args.request_path, now=now)
            print(json.dumps({'registered': True, 'grant_id': record['grant_id']}))


if __name__ == '__main__':
    main()
