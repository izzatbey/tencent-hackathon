#!/usr/bin/env python3
"""Permission gate SecuritySahabat.

Tiga tanggung jawab:
  1. parse_identity(query)        -> siapa penanya (nama / role / dept)
  2. lookup_permissions(identity) -> allowed_zones + max_risk_level dari permissions.csv
  3. filter_by_permissions(hits)  -> hasil retrieval yang di luar zona akses dibuang

Dipanggil otomatis oleh `scripts/search_kb.py` sebelum hasil dikembalikan ke
agent. Gate ini TIDAK pernah membuka dokumen bertanda `restricted`: dokumen
itu tetap disembunyikan untuk semua orang (lihat references/restricted-handling.md).

Pakai langsung untuk uji identitas:
    python3 scripts/permissions.py --query "Saya Andini, IT Admin. Boleh remote?"
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent

RISK_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}
DEFAULT_ZONE = "common"

FALLBACK_PERMS = {
    "user": "unauthenticated",
    "role": "none",
    "dept": "-",
    "allowed_zones": [DEFAULT_ZONE],
    "max_risk_level": "low",
    "allowed_projects": [],
    "source": "default",
    "match_score": 0,
}

# Nama orang: huruf kapital di awal setiap kata ("Andini Pratama", "Budi").
NAME_RE = r"[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*"
TAIL_RE = r"[^,.;:!?\n]{2,40}"

# Catatan: pola di bawah SENGAJA tidak memakai flag (?i) global - nama orang
# wajib berhuruf kapital, kalau tidak "Saya Budi dari Finance" akan terbaca
# sebagai nama "Budi dari Finance".
IDENTITY_PATTERNS = [
    # "Saya Andini, IT Admin" / "Saya Andini Pratama, IT Admin"
    (r"\b(?:[Ss]aya|[Aa]ku)\s+(" + NAME_RE + r")\s*,\s*(" + TAIL_RE + r")", ("name", "role")),
    # "Saya Budi dari Finance"
    (r"\b(?:[Ss]aya|[Aa]ku)\s+(" + NAME_RE + r")\s+[Dd]ari\s+(" + TAIL_RE + r")", ("name", "dept")),
    # "Andini di sini, IT Admin"
    (r"\b(" + NAME_RE + r")\s+di\s+sini\s*,\s*(" + TAIL_RE + r")", ("name", "role")),
    # "[Role] [Name]" -> hanya dipakai dengan kosakata role yang dikenal,
    # supaya frasa acak berhuruf kapital tidak dituduh sebagai identitas.
]


# --------------------------------------------------------------------------
# config
# --------------------------------------------------------------------------
def load_config():
    cfg_path = SKILL_DIR / "config.json"
    if cfg_path.exists():
        try:
            return json.loads(cfg_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def resolve_permissions_csv(config=None):
    """Lokasi permissions.csv: config.permissions_csv_path -> kb/ -> root skill
    -> knowledge-base/kb/ (layout repo)."""
    config = config if config is not None else load_config()
    candidates = []
    if config.get("permissions_csv_path"):
        p = Path(str(config["permissions_csv_path"])).expanduser()
        # path relatif = relatif ke folder skill, bukan cwd
        candidates.append(p if p.is_absolute() else SKILL_DIR / p)
    candidates += [SKILL_DIR / "kb" / "permissions.csv", SKILL_DIR / "permissions.csv",
                   SKILL_DIR.parent / "knowledge-base" / "kb" / "permissions.csv"]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def risk_gate_mode(config=None):
    config = config if config is not None else load_config()
    mode = str(config.get("risk_gate", "flag")).lower()
    return mode if mode in ("off", "flag", "enforce") else "flag"


def skip_gate(config=None):
    config = config if config is not None else load_config()
    return bool(config.get("skip_permission_gate", False))


# --------------------------------------------------------------------------
# identitas
# --------------------------------------------------------------------------
def parse_identity(query, roles=(), names=()):
    """Ekstrak identitas penanya dari teks pertanyaan.

    Urutan: pola eksplisit ("Saya X, Role") -> kosakata role yang dikenal ->
    nama yang dikenal. Tidak ada yang cocok = unauthenticated (zona common).
    """
    q = " ".join(str(query or "").split())
    identity = {
        "name": None,
        "role": None,
        "dept": None,
        "authenticated": False,
        "matched_by": "none",
    }

    for pattern, keys in IDENTITY_PATTERNS:
        m = re.search(pattern, q)
        if not m:
            continue
        identity[keys[0]] = m.group(1).strip()
        identity[keys[1]] = m.group(2).strip()
        identity["authenticated"] = True
        identity["matched_by"] = "explicit"
        break

    if not (identity["role"] and identity["name"]) and roles:
        # "IT Admin Andini" — role harus dari kosakata yang dikenal.
        alt = "|".join(re.escape(r) for r in sorted(roles, key=len, reverse=True))
        m = re.search(r"\b(?i:(" + alt + r"))\s+(" + NAME_RE + r")\b", q)
        if m:
            identity["role"] = m.group(1).strip()
            identity["name"] = m.group(2).strip()
            identity["authenticated"] = True
            identity["matched_by"] = "explicit"

    if not identity["role"]:
        for role in sorted(roles, key=len, reverse=True):
            if re.search(r"(?<!\w)" + re.escape(role) + r"(?!\w)", q, re.I):
                identity["role"] = role
                identity["authenticated"] = True
                identity["matched_by"] = identity["matched_by"] if identity["matched_by"] != "none" else "role-term"
                break

    if not identity["name"]:
        for name in sorted(names, key=len, reverse=True):
            if re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", q, re.I):
                identity["name"] = name
                identity["authenticated"] = True
                identity["matched_by"] = identity["matched_by"] if identity["matched_by"] != "none" else "name-term"
                break

    return identity


# --------------------------------------------------------------------------
# permissions.csv
# --------------------------------------------------------------------------
def split_multi(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    return [v.strip() for v in str(value).replace(",", ";").split(";") if v.strip()]


def load_permissions_rows(path=None):
    path = Path(path) if path else resolve_permissions_csv()
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            rows = [r for r in csv.DictReader(fh) if r.get("user") or r.get("role")]
    except (OSError, csv.Error):
        return []
    return rows


def vocabulary(rows):
    roles, names = set(), set()
    for row in rows:
        role = str(row.get("role") or "").strip()
        if role and role.lower() != "none":
            roles.add(role)
        user = str(row.get("user") or "").strip()
        if user and user.lower() != "unauthenticated":
            names.add(user)
            names.add(user.split()[0])
    return roles, names


def _norm(value):
    return " ".join(str(value or "").lower().split())


def lookup_permissions(identity, rows=None, config=None):
    """Cocokkan identitas ke baris permissions.csv (nama > role > dept)."""
    rows = load_permissions_rows() if rows is None else rows
    config = config if config is not None else load_config()

    role = _norm(identity.get("role"))
    dept = _norm(identity.get("dept"))
    # Nama bisa terbaca lebih panjang dari yang dimaksud ("Budi Santoso, ..."),
    # jadi coba nama utuh dan kata pertamanya.
    raw_name = _norm(identity.get("name"))
    names = [n for n in (raw_name, raw_name.split()[0] if raw_name else "") if n]

    best, best_score = None, 0
    for row in rows:
        r_user, r_role, r_dept = _norm(row.get("user")), _norm(row.get("role")), _norm(row.get("dept"))
        score = 0
        if any(n == r_user or n in r_user or n in r_user.split() for n in names):
            score += 3
        if role and (role == r_role or role in r_role or r_role in role):
            score += 2
        if dept and (dept == r_dept or dept in r_dept or r_dept in dept):
            score += 1
        if score > best_score:
            best, best_score = row, score

    if best is None:
        fallback = dict(FALLBACK_PERMS)
        override = config.get("default_permissions") or {}
        if isinstance(override, dict) and override:
            fallback.update({
                "allowed_zones": split_multi(override.get("allowed_zones")) or [DEFAULT_ZONE],
                "max_risk_level": str(override.get("max_risk_level", "low")).lower(),
                "allowed_projects": split_multi(override.get("allowed_projects")),
                "source": "config.default_permissions",
            })
        return fallback

    return {
        "user": str(best.get("user") or "unknown"),
        "role": str(best.get("role") or "-"),
        "dept": str(best.get("dept") or "-"),
        "allowed_zones": split_multi(best.get("allowed_zones")) or [DEFAULT_ZONE],
        "max_risk_level": str(best.get("max_risk_level") or "low").lower(),
        "allowed_projects": split_multi(best.get("allowed_projects")),
        "source": "permissions.csv",
        "match_score": best_score,
    }


# --------------------------------------------------------------------------
# filtering
# --------------------------------------------------------------------------
def risk_level_allowed(result_risk, max_risk):
    """True bila tingkat risiko dokumen masih dalam batas akses user."""
    return RISK_ORDER.get(str(result_risk or "low").lower(), 1) <= RISK_ORDER.get(
        str(max_risk or "low").lower(), 4
    )


def doc_zones(hit):
    zones = split_multi(hit.get("zones")) or split_multi(hit.get("zone"))
    return zones or [DEFAULT_ZONE]


def project_allowed(meta, permissions):
    """True bila dokumen restricted ini membuka diri untuk user.

    Syarat: dokumen punya field `project`, dan `allowed_projects` user memuat
    proyek itu (atau `*`). Dokumen tanpa `project` tidak pernah terbuka.
    Zona tetap ditegakkan terpisah oleh filter_by_permissions().
    """
    projects = {p.lower() for p in split_multi(meta.get("project"))}
    if not projects or not permissions:
        return False
    allowed = {p.lower() for p in split_multi(permissions.get("allowed_projects"))}
    return "*" in allowed or bool(projects & allowed)


def filter_by_permissions(hits, permissions, mode="flag"):
    """Saring hasil retrieval berdasarkan zona + (opsional) tingkat risiko.

    zone  -> selalu ditegakkan. Dokumen terlihat bila SALAH SATU zonanya ada di
             allowed_zones (union), jadi menambah zona hanya memperluas akses.
    risk  -> "off" = abaikan, "flag" = tampilkan + tandai, "enforce" = buang.
    """
    allowed = {z.lower() for z in split_multi(permissions.get("allowed_zones")) or [DEFAULT_ZONE]}
    max_risk = str(permissions.get("max_risk_level") or "low").lower()
    mode = mode if mode in ("off", "flag", "enforce") else "flag"

    kept, dropped, risk_notes = [], [], []
    for hit in hits:
        zones = {z.lower() for z in doc_zones(hit)}
        if not (zones & allowed):
            dropped.append({"doc_id": hit.get("doc_id"), "reason": "zone", "zones": sorted(zones)})
            continue
        risk = str(hit.get("risk_level") or "low").lower()
        if not risk_level_allowed(risk, max_risk):
            if mode == "enforce":
                dropped.append({"doc_id": hit.get("doc_id"), "reason": "risk", "risk": risk})
                continue
            if mode == "flag":
                risk_notes.append({"doc_id": hit.get("doc_id"), "risk": risk, "max_risk": max_risk})
        kept.append(hit)
    return kept, dropped, risk_notes


def resolve(query, user=None, role=None, config=None, rows=None, from_text=True):
    """Satu pintu: query + override -> (identity, permissions). Dipakai search_kb.

    from_text=False: identitas hanya dari user/role pemanggil, klaim di teks
    pertanyaan ("Saya Andini, IT Admin") diabaikan. Dipakai API web, tempat
    identitas datang dari sesi, bukan dari apa yang diketik penanya.
    """
    config = config if config is not None else load_config()
    rows = load_permissions_rows() if rows is None else rows
    roles, names = vocabulary(rows)
    identity = parse_identity(query if from_text else "", roles=roles, names=names)
    if user:
        identity["name"] = user
        identity["authenticated"] = True
        identity["matched_by"] = "cli"
    if role:
        identity["role"] = role
        identity["authenticated"] = True
        identity["matched_by"] = identity.get("matched_by") if identity.get("matched_by") != "none" else "cli"

    perms = lookup_permissions(identity, rows=rows, config=config)
    if perms.get("source") != "permissions.csv":
        # Identitas tidak dikenali sistem -> perlakukan sebagai unauthenticated.
        identity["authenticated"] = False
        identity["matched_by"] = "none"
    return identity, perms


def main():
    ap = argparse.ArgumentParser(description="Uji permission gate SecuritySahabat.")
    ap.add_argument("--query", "-q", help="Pertanyaan (untuk ekstraksi identitas)")
    ap.add_argument("--user", help="Override nama user")
    ap.add_argument("--role", help="Override role user")
    ap.add_argument("--csv", help="Path permissions.csv")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = load_permissions_rows(args.csv)
    identity, perms = resolve(args.query or "", user=args.user, role=args.role, rows=rows)
    payload = {"rows": len(rows), "csv": str(args.csv or resolve_permissions_csv()),
               "identity": identity, "permissions": perms}
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else
          "user=%s | role=%s | zones=%s | max_risk=%s | source=%s | matched_by=%s" % (
              perms["user"], perms["role"], ";".join(perms["allowed_zones"]),
              perms["max_risk_level"], perms["source"], identity["matched_by"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
