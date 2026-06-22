"""Taxonomy version pin + pinned-list loader for Profit Sentinel.

THE single authoritative home for the Shopify Standard Product Taxonomy version
this project resolves categories against. seed_shopify.py and category_inference.py
READ PINNED_TAXONOMY_VERSION from here — the literal "2026-05" lives in exactly
one place so there is no stale mirror to drift.

The pinned list itself is the committed slim projection at
  connectors/data/taxonomy/<version>/categories.json
which carries the resolution fields (id / full_name / parent_id / level) for every
node in every vertical of the upstream release. The full ~80 MB upstream
categories.json (attributes + return_reasons) stays the gitignored reference asset
(data/shopify_taxonomy/); this slim file is what resolution binds to so the repo is
reproducible without the 80 MB blob.

Version drift policy (the WHY this module exists): a resolved or seed-baked category
gid only means something "as of release X". Stamping every resolution with
PINNED_TAXONOMY_VERSION and resolving only against the pinned list lets a later
release that re-ids / re-parents / retires a node be DETECTED (the H21 drift signal
in category_inference.py) rather than silently mis-grouping. The version->version
remap that consumes a detected drift is DEFERRED (see technical_architecture.md).
"""

import json
import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)

# ── The pin ───────────────────────────────────────────────────────────────────
# Change this ONE literal (plus drop in the matching pinned list) to re-pin.
PINNED_TAXONOMY_VERSION = "2026-05"

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PINNED_TAXONOMY_DIR = os.path.join(_THIS_DIR, "data", "taxonomy")


def pinned_taxonomy_path(version: str = PINNED_TAXONOMY_VERSION) -> str:
    """Absolute path to the committed slim pinned categories.json for `version`."""
    return os.path.join(PINNED_TAXONOMY_DIR, version, "categories.json")


@lru_cache(maxsize=4)
def load_pinned_taxonomy(version: str = PINNED_TAXONOMY_VERSION) -> dict:
    """Load the pinned list, returning {id -> {full_name, parent_id, level}}.

    Cached per version (the file is immutable once committed). Returns {} on any
    load failure so callers degrade safely rather than crashing a backfill — a
    missing/empty index makes EVERY gid fail to resolve, which surfaces loudly via
    the drift path rather than silently mis-resolving.
    """
    path = pinned_taxonomy_path(version)
    try:
        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)
        index = {
            c["id"]: {
                "full_name": c["full_name"],
                "parent_id": c.get("parent_id"),
                "level": c["level"],
            }
            for c in doc["categories"]
        }
        logger.info(
            "SOURCE: Taxonomy Config | INFO: loaded pinned list %s | "
            "nodes=%d | path=%s",
            version, len(index), path,
        )
        return index
    except (OSError, KeyError, ValueError) as e:
        logger.error(
            "SOURCE: Taxonomy Config | ERROR: %s | "
            "CONTEXT: failed to load pinned taxonomy version=%s path=%s",
            str(e), version, path,
        )
        return {}


def resolves(node_id: str, version: str = PINNED_TAXONOMY_VERSION) -> bool:
    """True iff `node_id` (a full gid) is a real node in the pinned list."""
    if not node_id:
        return False
    return node_id in load_pinned_taxonomy(version)


def full_name_for(node_id: str, version: str = PINNED_TAXONOMY_VERSION) -> str | None:
    """Pinned breadcrumb for `node_id`, or None if it does not resolve."""
    return load_pinned_taxonomy(version).get(node_id, {}).get("full_name")
