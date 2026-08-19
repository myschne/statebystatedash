from __future__ import annotations

import json
from pathlib import Path


root = Path(__file__).resolve().parents[1]
service_path = root / "stable-hologram-497015-i9-45282bfa717e.json"
meta_path = root / "metasecret.txt"
output_path = root / ".streamlit" / "secrets.toml"

service = json.loads(service_path.read_text(encoding="utf-8"))
meta_token = meta_path.read_text(encoding="utf-8").strip()

lines = ["[gcp_service_account]"]
for key, value in service.items():
    if isinstance(value, str):
        lines.append(f"{key} = {json.dumps(value)}")

lines.extend(["", "[meta]", f"page_access_token = {json.dumps(meta_token)}", ""])
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text("\n".join(lines), encoding="utf-8")
print(f"Created {output_path} with GA4 and Meta credentials.")
