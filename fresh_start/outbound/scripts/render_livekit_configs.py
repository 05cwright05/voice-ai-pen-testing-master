from __future__ import annotations

import json
from pathlib import Path

from app.config import get_settings


def main() -> None:
    settings = get_settings()
    out_dir = Path(__file__).resolve().parents[1] / "livekit"
    out_dir.mkdir(parents=True, exist_ok=True)

    inbound_trunk = {
        "trunk": {
            "name": "voice-mvp-inbound-trunk",
            "numbers": [settings.target_phone_number],
            "authUsername": settings.inbound_trunk_username,
            "authPassword": settings.inbound_trunk_password,
        }
    }

    dispatch_rule = {
        "dispatch_rule": {
            "name": "voice-mvp-individual-dispatch",
            "rule": {"dispatchRuleIndividual": {"roomPrefix": "call-"}},
        }
    }

    (out_dir / "inbound-trunk.json").write_text(
        json.dumps(inbound_trunk, indent=2), encoding="utf-8"
    )
    (out_dir / "dispatch-rule.json").write_text(
        json.dumps(dispatch_rule, indent=2), encoding="utf-8"
    )
    print(f"Wrote {out_dir / 'inbound-trunk.json'}")
    print(f"Wrote {out_dir / 'dispatch-rule.json'}")


if __name__ == "__main__":
    main()
