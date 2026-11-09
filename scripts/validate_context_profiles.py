"""Validate candidate consumer declarations, never infer runtime adoption."""
import argparse
import json
import re
from pathlib import Path

REQUIREMENTS = {f"QC{i:02}" for i in range(1, 13)}


def validate(profile):
    errors = []
    if not isinstance(profile, dict):
        return ["profile must be an object"]
    if profile.get("format") != "quirk-context-profile-candidate/0.1":
        errors.append("unsupported profile format")
    if profile.get("status") != "candidate" or profile.get("authority_effect") != "none":
        errors.append("profile cannot grant authority")
    for field in ("repository", "scope", "domain", "inheritance", "refresh"):
        if not isinstance(profile.get(field), str) or not profile[field].strip():
            errors.append("missing " + field)
    if not re.fullmatch(r"[0-9a-f]{40}", str(profile.get("observed_base", ""))):
        errors.append("missing exact observed base")
    requirements = profile.get("requirements")
    if not isinstance(requirements, list) or any(not isinstance(x, str) for x in requirements) or set(requirements) != REQUIREMENTS or len(requirements) != 12:
        errors.append("missing or duplicate continuity requirement")
    contract = profile.get("contract", {})
    if not isinstance(contract, dict) or contract.get("repository") != "Quirk-Systems/quirk-core" or contract.get("path") != "contracts/context-continuity/v0.1/README.md" or not re.fullmatch(r"[0-9a-f]{64}", str(contract.get("sha256", ""))):
        errors.append("unbound contract")
    for field in ("acceptance_cases", "limitations"):
        values = profile.get(field)
        if not isinstance(values, list) or not values or any(not isinstance(v,str) or not v.strip() for v in values):
            errors.append("missing " + field)
    coverage = profile.get("coverage")
    if not isinstance(coverage, dict) or set(coverage) != {"authored", "delivered", "loaded", "behavior_tested", "deployed"} or any(type(v) is not bool for v in coverage.values()):
        errors.append("invalid coverage dimensions")
    elif any(coverage[k] for k in ("delivered","loaded","behavior_tested","deployed")):
        # Evidence belongs in a separate exact-revision adoption receipt.
        errors.append("candidate profile alone cannot attest adoption")
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profiles", nargs="+", type=Path)
    parser.add_argument("--contract", type=Path)
    args=parser.parse_args()
    failures=[]
    for path in args.profiles:
        try:
            profile=json.loads(path.read_text())
            errors=validate(profile)
            if args.contract and not errors:
                import hashlib
                if hashlib.sha256(args.contract.read_bytes()).hexdigest() != profile["contract"]["sha256"]:
                    errors.append("contract bytes differ")
        except (OSError, ValueError, TypeError):
            errors=["unreadable profile"]
        if errors:
            failures.append({"path":str(path),"errors":errors})
    print(json.dumps({"checked":len(args.profiles),"failures":failures,"runtime_adoption_verified":False}))
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
