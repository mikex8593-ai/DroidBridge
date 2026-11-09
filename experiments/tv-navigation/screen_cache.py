# SPDX-License-Identifier: Apache-2.0
# Experimental TV navigation work; see PROVENANCE.md.
"""Read-only recognition of durable TV screen maps. Never issues input.

Call with a *newly acquired* hierarchy and foreground identity. Timestamps are
monotonic seconds from the same process. A match is a recommendation, not an
execution lease; the existing guarded runner must still recheck state/focus.
Do not reuse XML/timestamps after a failed dump or increment timestamps for old XML.
"""
import math
import xml.etree.ElementTree as ET


def lookup(catalog, observation, *, now):
    def refresh(reason):
        return {"action": "refresh_observation", "reason": reason, "mapping": None}
    if catalog.get("schema_version") != 1:
        return refresh("unsupported_catalog")
    if not isinstance(observation, dict):
        return refresh("missing_observation")
    try:
        start, end = observation["started"], observation["completed"]
        if any(type(x) not in (int, float) or not math.isfinite(x) for x in (start, end, now)):
            return refresh("invalid_clock")
        if not 0 <= end-start <= 4 or not 0 <= now-end <= 1:
            return refresh("stale_or_slow_observation")
        if observation.get("success") is not True:
            return refresh("failed_observation")
        package, activity, version = (observation[k] for k in ("package", "activity", "version"))
        if not all(isinstance(v, str) and v for v in (package, activity, version)):
            return refresh("missing_identity")
        nodes = list(ET.fromstring(observation["xml"]).iter("node"))
    except (KeyError, ValueError, TypeError, ET.ParseError):
        return refresh("invalid_observation")
    apps = [a for a in catalog.get("apps", []) if a.get("package") == package]
    if len(apps) != 1:
        return refresh("unknown_or_ambiguous_app")
    app = apps[0]
    if app.get("version") != version:
        return refresh("unverified_app_version")
    # Reject foreground overlays or foreign-package nodes rather than merging IDs.
    if not nodes or any(n.get("package") != package for n in nodes):
        return refresh("foreign_or_missing_nodes")
    ids = {n.get("resource-id") for n in nodes if n.get("enabled") == "true"}
    matches = [s for s in app.get("screens", [])
               if s.get("activity") == activity and s.get("required_ids")
               and set(s["required_ids"]).issubset(ids)]
    if len(matches) != 1:
        return refresh("unknown_or_ambiguous_screen")
    screen = matches[0]
    if screen.get("status") != "live_verified" or not screen.get("mapping"):
        return {"action": "observe_only", "screen": screen["name"], "mapping": None}
    return {"action": "guarded_mapping_available", "screen": screen["name"],
            "mapping": screen["mapping"], "requires_runner_checks": True}


def recognize(device, catalog, *, clock=None):
    """Read identity around one fresh hierarchy. No input or launch operations."""
    import time
    clock = clock or time.monotonic
    if device.cancelled():
        return {"action": "refresh_observation", "reason": "cancelled", "mapping": None}
    before = device.identity()
    started = clock()
    xml = device.observe()
    completed = clock()
    after = device.identity()
    now = clock()
    if before != after or device.cancelled():
        return {"action": "refresh_observation", "reason": "identity_changed_or_cancelled", "mapping": None}
    return lookup(catalog, dict(zip(('package', 'activity', 'version'), after),
                               success=True, started=started, completed=completed, xml=xml), now=now)
