"""Synthetic local timing; no latency SLO or human-benefit claim."""
import json
import platform
import statistics
import time
from context_continuity import resolve


def main():
    results=[]
    for size in (100, 1000, 10000):
        records=[dict(id=f"source-{i:05}",revision="r1",original="An untried idea with an exact original.",origin=f"origin-{i}",owner="fixture",purpose="create",audiences=["local"],domains=["creative"],derived_from=[],kind="opportunity" if i%10==0 else "reference",state="untried",freshness="historical") for i in range(size)]
        samples=[]
        for _ in range(7):
            start=time.perf_counter()
            package=resolve(records,release="synthetic-1",audience="local",purpose="create",domains=["creative"],as_of="2026-10-14T00:00:00Z")
            samples.append((time.perf_counter()-start)*1000)
        results.append({"records":size,"runs":len(samples),"median_ms":round(statistics.median(samples),3),"max_ms":round(max(samples),3),"output_bytes":len(json.dumps(package).encode())})
    print(json.dumps({"python":platform.python_version(),"system":platform.system(),"machine":platform.machine(),"corpus":"synthetic independent records; not deep/wide adversarial lineage","results":results,"human_effort":None,"network_latency":None,"production_slo":None},indent=2))


if __name__ == "__main__":
    main()
