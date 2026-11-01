#!/usr/bin/env python3
import json, sys, hashlib
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from emit_ci_receipt import checked_head, ReceiptError
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"evidence"/"validation-report.generated.json"
OUT.unlink(missing_ok=True)
try:
    VALIDATED_HEAD=checked_head(ROOT.parents[1])
except ReceiptError as e:
    sys.exit(f"VALIDATION_BLOCKED: {e}")
def load(p): return json.loads(p.read_text())
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
NAMES=("transformation","run","evidence","promotion")
SCHEMAS={n:load(ROOT/"contracts"/f"{n}.schema.json") for n in NAMES}
for s in SCHEMAS.values(): Draft202012Validator.check_schema(s)
def semantic(x):
    c=x["contract_type"].replace("one_to_infinity_",""); out=[]
    def fail(code,cond):
        if cond: out.append(code)
    if c=="transformation":
        m=x.get("mechanism",{}); s=m.get("retained_state",{}); r=m.get("reinvestment",{})
        fail("OTI-T-001",s.get("used_next_cycle") is not True)
        fail("OTI-T-002",r.get("connected") is not True or r.get("source_state_id")!=s.get("state_id") or r.get("target_next_input","").strip().lower() in ("","none","unused"))
        fail("OTI-T-003",x.get("economics",{}).get("active_constraint") not in m.get("constraints",[]))
    elif c=="run":
        d=x.get("delay",{})
        fail("OTI-R-001",any(u.get("applied_next_cycle") for u in x.get("learning_updates",[])) and (d.get("feedback_matured") is not True or d.get("elapsed_hours",0)<d.get("minimum_hours",0)))
        fail("OTI-R-002",x.get("provider_receipt",{}).get("claims_authority") is not False)
    elif c=="evidence":
        stage=x.get("stage"); b=x.get("beneficiary_outcome",{})
        fail("OTI-E-004",x.get("producer_id")==x.get("evaluator_id"))
        if stage=="value_proof":
            proxies=" ".join(x.get("proxy_metrics",[])).lower()
            fail("OTI-E-003",not b.get("observed") and "benchmark" in proxies)
            fail("OTI-E-005",not b.get("observed") and "benchmark" not in proxies)
        elif stage=="economic_scalability_proof":
            ec=x.get("economics",{})
            fail("OTI-E-001",ec.get("observed_human_minutes_per_outcome",1e99)>=ec.get("baseline_human_minutes_per_outcome",0) or ec.get("observed_cost_per_outcome",1e99)>ec.get("baseline_cost_per_outcome",0))
            fail("OTI-E-006",ec.get("active_constraint_measured") is not True)
        elif stage=="compounding_proof":
            co=x.get("compounding",{})
            fail("OTI-E-002",co.get("retained_state_used") is not True or co.get("delta",0)<=0 or co.get("delta",0)<co.get("minimum_delta",1e99) or x.get("method",{}).get("preregistered") is not True)
        fail("OTI-E-007",any(z.get("passed") is not True for z in x.get("countermetrics",[])))
    elif c=="promotion":
        fail("OTI-P-001",x.get("decision",{}).get("automated") is not False or x.get("decision",{}).get("authority_type")!="human")
    return sorted(set(out))
def validate(x,name):
    errs=list(Draft202012Validator(SCHEMAS[name],format_checker=FormatChecker()).iter_errors(x))
    return (["JSON_SCHEMA"] if errs else []) + semantic(x)
results=[]
for f in sorted((ROOT/"fixtures"/"positive").glob("*.json")):
    name=f.name.split(".")[0]; issues=validate(load(f),name)
    results.append({"fixture":f.name,"expected":"accept","actual":"accept" if not issues else "reject","passed":not issues,"rules":issues,"sha256":digest(f)})
for f in sorted((ROOT/"fixtures"/"adversarial").glob("*.json")):
    z=load(f); issues=validate(z["payload"],z["target_contract"]); ok=z["expected_rule"] in issues
    results.append({"fixture":z["fixture_id"],"expected":"reject","expected_rule":z["expected_rule"],"actual":"reject" if issues else "accept","passed":ok,"rules":issues,"sha256":digest(f)})
positive=[r for r in results if r["expected"]=="accept"]; adversarial=[r for r in results if r["expected"]=="reject"]
passed=len(positive)==4 and len(adversarial)==11 and all(r["passed"] for r in results)
checked_head(ROOT.parents[1], VALIDATED_HEAD)
report={"git_head":VALIDATED_HEAD,"status":"pass" if passed else "fail","candidate_only":True,"admission":"NOT_ADMITTED","positive_passing":sum(r["passed"] for r in positive),"adversarial_rejecting_for_intended_rule":sum(r["passed"] for r in adversarial),"validator_sha256":digest(Path(__file__)),"schema_sha256":{n:digest(ROOT/"contracts"/f"{n}.schema.json") for n in NAMES},"results":results,"not_proven":["human review","production value","retention","closure","scalability","compounding"]}
OUT.write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"status":report["status"],"positive":f"{report['positive_passing']}/4","adversarial_intended":f"{report['adversarial_rejecting_for_intended_rule']}/11"},indent=2))
sys.exit(0 if passed else 1)
