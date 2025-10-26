
import json
from pathlib import Path

_SETTINGS_PATH = Path(__file__).resolve().parents[1] / "app_settings.json"

DEFAULTS = {
    "active_profile": "Default",
    "profiles": {
        "Default": {
            "store": "Main Store",
            "register": "TILL-1",
            "escpos": {"mode": "network", "host": "192.168.1.50", "port": 9100, "usb_vid": 0, "usb_pid": 0},
            "zebra": {"mode": "network", "host": "192.168.1.51", "port": 9100, "usb_vid": 0, "usb_pid": 0}
        }
    }
}

def _deepmerge(base: dict, extra: dict) -> dict:
    out = dict(base)
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deepmerge(out[k], v)
        else:
            out[k] = v if k in extra else out.get(k)
    return out

def load_settings() -> dict:
    try:
        data = json.loads(Path(_SETTINGS_PATH).read_text(encoding="utf-8"))
    except Exception:
        data = {}
    return _deepmerge(DEFAULTS, data)

def save_settings(data: dict):
    try:
        Path(_SETTINGS_PATH).write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Unable to write settings file '{_SETTINGS_PATH}': {exc}") from exc

def get_active_profile() -> dict:
    data = load_settings()
    name = data.get("active_profile", "Default")
    prof = data.get("profiles", {}).get(name, {})
    return prof

def set_active_profile(name: str):
    data = load_settings()
    if name in data.get("profiles", {}):
        data["active_profile"] = name
        save_settings(data)
