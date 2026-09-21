#!/usr/bin/env python3
from __future__ import annotations

import argparse
import cProfile
import copy
import io
import json
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from pstats import Stats
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from deck_grammar.access import build_access_pool
from deck_grammar.hand import compile_hand


def _positive_int(raw: str) -> int:
    value = int(raw)
    if value <= 0:
        raise argparse.ArgumentTypeError("value must be > 0")
    return value


def _linear_build_access_pool(collection: dict[str, Any], entitlements: list[dict[str, Any]], *, as_of: datetime) -> list[dict[str, Any]]:
    from deck_grammar.access import DeckGrammarError, _slug, is_active_entitlement  # local import to mirror production behavior

    instances = [json.loads(json.dumps(item)) for item in collection["card_instances"]]
    owned_card_ids = {
        item["card_id"]
        for item in instances
        if item["access_kind"] == "owned" and item["ownership_claim"] == "owned"
    }
    for entitlement in entitlements:
        if not is_active_entitlement(entitlement, as_of):
            continue
        if entitlement.get("authority_effect") != "none":
            raise DeckGrammarError("an entitlement may not alter authority")
        for card_id in entitlement.get("scope", {}).get("card_ids", []):
            if card_id in owned_card_ids:
                continue
            instance_id = (
                "card-instance.entitled."
                + _slug(entitlement["entitlement_id"].removeprefix("entitlement."))
                + "."
                + _slug(card_id.removeprefix("card."))
            )
            if any((existing["instance_id"] == instance_id for existing in instances)):
                continue
            instances.append(
                {
                    "instance_id": instance_id,
                    "card_id": card_id,
                    "holder_ref": entitlement["grantee_ref"],
                    "access_kind": entitlement["access_kind"],
                    "state": "accessible",
                    "acquired_at": entitlement["starts_at"],
                    "expires_at": entitlement.get("ends_at"),
                    "entitlement_ref": entitlement["entitlement_id"],
                    "ownership_claim": "not_owned",
                    "authority_effect": "none",
                    "edition": None,
                    "provenance_refs": [entitlement["source_ref"]],
                    "metadata": {"entitlement_state": entitlement["state"]},
                }
            )
    return instances


def _make_access_workload(*, owned_instances: int, entitlement_count: int, scope_size: int) -> tuple[dict[str, Any], list[dict[str, Any]], datetime]:
    as_of = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
    collection = {
        "collection_id": "collection.performance.benchmark",
        "owner_ref": "human.benchmark",
        "card_instances": [
            {
                "instance_id": f"card-instance.owned.{index:05d}",
                "card_id": f"card.affordance.{index % (owned_instances // 2 + 1):05d}",
                "holder_ref": "human.benchmark",
                "access_kind": "owned",
                "state": "accessible",
                "acquired_at": "2026-01-01T00:00:00Z",
                "ownership_claim": "owned",
                "authority_effect": "none",
                "edition": None,
                "provenance_refs": ["source.collection.benchmark"],
                "metadata": {},
            }
            for index in range(owned_instances)
        ],
    }

    entitlements: list[dict[str, Any]] = []
    card_domain = max(owned_instances * 2, entitlement_count * scope_size // 2)
    for ent_index in range(entitlement_count):
        start = (ent_index * 7) % card_domain
        scope = [f"card.affordance.{(start + offset) % card_domain:05d}" for offset in range(scope_size)]
        if scope:
            scope.append(scope[0])
        entitlements.append(
            {
                "entitlement_id": f"entitlement.performance.{ent_index:05d}",
                "grantee_ref": "human.benchmark",
                "access_kind": "premium",
                "state": "active",
                "authority_effect": "none",
                "starts_at": (as_of - timedelta(days=2)).isoformat().replace("+00:00", "Z"),
                "ends_at": None,
                "scope": {"card_ids": scope},
                "source_ref": f"source.entitlement.{ent_index:05d}",
            }
        )
    return collection, entitlements, as_of


def _benchmark_build_access_pool(*, repeats: int, owned_instances: int, entitlement_count: int, scope_size: int) -> dict[str, Any]:
    collection, entitlements, as_of = _make_access_workload(
        owned_instances=owned_instances,
        entitlement_count=entitlement_count,
        scope_size=scope_size,
    )

    baseline = _linear_build_access_pool(copy.deepcopy(collection), copy.deepcopy(entitlements), as_of=as_of)
    optimized = build_access_pool(copy.deepcopy(collection), copy.deepcopy(entitlements), as_of=as_of)
    equivalent = baseline == optimized

    linear_samples: list[float] = []
    set_samples: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        _linear_build_access_pool(copy.deepcopy(collection), copy.deepcopy(entitlements), as_of=as_of)
        linear_samples.append(time.perf_counter() - start)

        start = time.perf_counter()
        build_access_pool(copy.deepcopy(collection), copy.deepcopy(entitlements), as_of=as_of)
        set_samples.append(time.perf_counter() - start)

    linear_median = statistics.median(linear_samples)
    set_median = statistics.median(set_samples)
    speedup = (linear_median / set_median) if set_median > 0 else None

    return {
        "scenario": "build_access_pool",
        "workload": {
            "owned_instances": owned_instances,
            "entitlements": entitlement_count,
            "scope_card_ids_per_entitlement": scope_size,
            "result_instances": len(optimized),
        },
        "equivalent_output": equivalent,
        "samples": {
            "linear_seconds": linear_samples,
            "set_backed_seconds": set_samples,
        },
        "median_seconds": {
            "linear": linear_median,
            "set_backed": set_median,
            "speedup_ratio": speedup,
        },
    }


def _make_compile_hand_workload(*, persona_instances: int, affordance_instances: int, slot_count: int) -> dict[str, Any]:
    cards_by_id: dict[str, dict[str, Any]] = {}
    instances_by_id: dict[str, dict[str, Any]] = {}
    card_instance_ids: list[str] = []

    for index in range(persona_instances):
        card_id = f"card.persona.{index:04d}"
        cards_by_id[card_id] = {
            "card_id": card_id,
            "card_kind": "persona",
            "metadata": {"tags": ["common", f"persona-{index % 8}"]},
        }
        instance_id = f"card-instance.persona.{index:04d}"
        instances_by_id[instance_id] = {"instance_id": instance_id, "card_id": card_id}
        card_instance_ids.append(instance_id)

    for index in range(affordance_instances):
        card_id = f"card.affordance.{index:04d}"
        cards_by_id[card_id] = {
            "card_id": card_id,
            "card_kind": "affordance",
            "metadata": {"tags": ["common", f"affordance-{index % 12}"]},
        }
        instance_id = f"card-instance.affordance.{index:04d}"
        instances_by_id[instance_id] = {"instance_id": instance_id, "card_id": card_id}
        card_instance_ids.append(instance_id)

    slots: list[dict[str, Any]] = []
    for slot_index in range(slot_count):
        kind = "persona" if slot_index % 4 == 0 else "affordance"
        require_tag = f"{kind}-{slot_index % (8 if kind == 'persona' else 12)}"
        slots.append(
            {
                "slot_id": f"slot.{slot_index:03d}",
                "card_kind": kind,
                "minimum": 1,
                "maximum": 2,
                "selectors": {
                    "prefer_card_ids": [
                        f"card.{kind}.{(slot_index + 3) % (persona_instances if kind == 'persona' else affordance_instances):04d}",
                        f"card.{kind}.{(slot_index + 7) % (persona_instances if kind == 'persona' else affordance_instances):04d}",
                    ],
                    "require_tags": ["common", require_tag],
                    "exclude_card_ids": [],
                },
                "default_role": f"role.{slot_index:03d}",
                "default_weight": 0.01 if kind == "persona" else 1.0,
            }
        )

    return {
        "deck": {
            "deck_id": "deck.performance.benchmark",
            "purpose_partition": "deck_grammar_live_proof",
            "task_class": "build_candidate_pack",
            "platform": "github",
            "area_ref": "area.performance",
            "card_instance_ids": card_instance_ids,
        },
        "preset": {
            "preset_id": "preset.performance.profile",
            "applies_when": {
                "purpose_partitions": ["deck_grammar_live_proof"],
                "task_classes": ["build_candidate_pack"],
                "platforms": ["github"],
                "area_refs": ["area.performance"],
            },
            "personalization": {
                "permanent_persona_assignment": False,
                "auto_persist_hand": False,
            },
            "authority": {
                "cards_cannot_expand_authority": True,
                "maximum_right": "propose",
            },
            "slots": slots,
            "approach": {
                "mode": "benchmark",
                "note": "compile_hand profile fixture",
            },
        },
        "cards_by_id": cards_by_id,
        "instances_by_id": instances_by_id,
        "collection": {
            "collection_id": "collection.performance.benchmark",
            "owner_ref": "human.benchmark",
            "card_instances": [],
        },
        "goal": {
            "goal_id": "goal.performance.profile",
            "desired_state": "measure compile_hand",
            "evidence_of_completion": ["profile output"],
            "constraints": ["deterministic"],
            "facts": ["benchmark"],
        },
        "intention": {"intention_id": "intention.performance.profile"},
        "area": {"area_id": "area.performance"},
    }


def _profile_compile_hand(*, repeats: int, persona_instances: int, affordance_instances: int, slot_count: int, top_functions: int) -> dict[str, Any]:
    fixture = _make_compile_hand_workload(
        persona_instances=persona_instances,
        affordance_instances=affordance_instances,
        slot_count=slot_count,
    )

    samples: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        compile_hand(
            deck=fixture["deck"],
            preset=fixture["preset"],
            cards_by_id=fixture["cards_by_id"],
            instances_by_id=fixture["instances_by_id"],
            collection=fixture["collection"],
            goal=fixture["goal"],
            intention=fixture["intention"],
            area=fixture["area"],
            authority_grant_ref="authority.human.performance",
            external_authority_ceiling="propose",
        )
        samples.append(time.perf_counter() - start)

    profiler = cProfile.Profile()
    profiler.enable()
    compile_hand(
        deck=fixture["deck"],
        preset=fixture["preset"],
        cards_by_id=fixture["cards_by_id"],
        instances_by_id=fixture["instances_by_id"],
        collection=fixture["collection"],
        goal=fixture["goal"],
        intention=fixture["intention"],
        area=fixture["area"],
        authority_grant_ref="authority.human.performance",
        external_authority_ceiling="propose",
    )
    profiler.disable()

    stats_stream = io.StringIO()
    stats = Stats(profiler, stream=stats_stream).sort_stats("cumulative")
    stats.print_stats(top_functions)
    profile_lines = [line.rstrip() for line in stats_stream.getvalue().splitlines() if line.strip()]

    return {
        "scenario": "compile_hand",
        "workload": {
            "preset_slots": slot_count,
            "eligible_instances": persona_instances + affordance_instances,
            "persona_instances": persona_instances,
            "affordance_instances": affordance_instances,
        },
        "timing_seconds": {
            "samples": samples,
            "median": statistics.median(samples),
            "p95": max(samples),
        },
        "cprofile_top": profile_lines,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic performance harnesses for deck grammar bottlenecks.")
    parser.add_argument("--scenario", choices=["build_access_pool", "compile_hand", "all"], default="all")
    parser.add_argument("--repeats", type=_positive_int, default=7)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--owned-instances", type=_positive_int, default=3500)
    parser.add_argument("--entitlements", type=_positive_int, default=320)
    parser.add_argument("--scope-size", type=_positive_int, default=28)
    parser.add_argument("--persona-instances", type=_positive_int, default=600)
    parser.add_argument("--affordance-instances", type=_positive_int, default=2800)
    parser.add_argument("--slots", type=_positive_int, default=120)
    parser.add_argument("--top-functions", type=_positive_int, default=12)
    args = parser.parse_args()

    payload: dict[str, Any] = {
        "suite": "deck_grammar.performance.v1",
        "generated_at": datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z"),
        "results": [],
    }

    if args.scenario in {"build_access_pool", "all"}:
        payload["results"].append(
            _benchmark_build_access_pool(
                repeats=args.repeats,
                owned_instances=args.owned_instances,
                entitlement_count=args.entitlements,
                scope_size=args.scope_size,
            )
        )
    if args.scenario in {"compile_hand", "all"}:
        payload["results"].append(
            _profile_compile_hand(
                repeats=args.repeats,
                persona_instances=args.persona_instances,
                affordance_instances=args.affordance_instances,
                slot_count=args.slots,
                top_functions=args.top_functions,
            )
        )

    output_text = json.dumps(payload, indent=2)
    print(output_text)
    if args.output:
        output_path = args.output if args.output.is_absolute() else ROOT / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
