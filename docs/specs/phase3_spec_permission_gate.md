# Phase 3 Spec — Full Permission Gate (User Identity + Zone Filtering)

## Goal

Add permission gate sebelum retrieval: setiap query harus di-parse untuk identitas user, lalu retrieval results di-filter sesuai `allowed_zones` dari `permissions.csv`.

## Problem yang Diselesaikan

Tanpa permission gate, agent bisa memberikan informasi sensitif ke user yang tidak punya hak akses:
- Staff gudang Makassar bertanya tentang topologi Jakarta → boleh, public
- Staff gudang Makassar bertanya tentang restricted project → harus diblokir jika tidak ada di allowed_zones
- Finance officer bertanya tentang IT controls → boleh jika control bersifat cross-functional
- Intern bertanya tentang segala hal → restricted ke zona "common" saja

## Architecture

```
User Query
    ↓
[S1] Intake/Parser — extract user identity (name, role, dept)
    ↓
[S2] Permission Gate — lookup permissions.csv → allowed_zones
    ↓
[S3] Retrieval — search KBs → filter results by allowed_zones
    ↓
[S4] Synthesizer — generate answer from filtered evidence
```

## Implementation Details

### 1. User Identity Parser

Extract identity dari query menggunakan pattern matching:

```python
# Patterns to match:
# - "Saya [Name], [Role]" → e.g., "Saya Andini, IT Admin"
# - "Saya [Name] dari [Dept]" → e.g., "Saya Budi dari Finance"
# - "[Name] di sini, [Role]" → e.g., "Andini di sini, IT Admin"
# - "[Role] [Name]" → e.g., "IT Admin Andini"
# - If no match: unauthenticated → allowed_zones = ["common"]

import re

def parse_identity(query: str) -> dict:
    patterns = [
        r"Saya\s+([A-Za-z\s]+?),\s*([A-Za-z\s]+?)(?:\s|$)",
        r"Saya\s+([A-Za-z\s]+?)\s+dari\s+([A-Za-z\s]+?)(?:\s|$)",
        r"([A-Za-z\s]+?)\s+di\s+sini,\s*([A-Za-z\s]+?)(?:\s|$)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return {
                "name": match.group(1).strip(),
                "role": match.group(2).strip(),
                "authenticated": True
            }
    
    return {"name": None, "role": None, "authenticated": False}
```

### 2. Permissions Lookup

Read `permissions.csv` dan match user identity:

```python
import csv

def lookup_permissions(name: str, role: str) -> dict:
    with open('permissions.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Match by name or role
            if (name and name.lower() in row['user'].lower()) or \
               (role and role.lower() in row['role'].lower()):
                return {
                    "user": row['user'],
                    "role": row['role'],
                    "allowed_zones": row['allowed_zones'].split(';'),
                    "max_risk_level": row['max_risk_level'],
                    "allowed_projects": row['allowed_projects'].split(';')
                }
    
    # Default: unauthenticated user
    return {
        "user": "unauthenticated",
        "role": "none",
        "allowed_zones": ["common"],
        "max_risk_level": "low",
        "allowed_projects": []
    }
```

### 3. Zone Filtering

Setiap KB entry harus punya metadata `zone` dan `risk_level`:

```python
def filter_by_permissions(results: list, permissions: dict) -> list:
    allowed_zones = permissions['allowed_zones']
    max_risk = permissions['max_risk_level']
    
    filtered = []
    for result in results:
        # Check zone
        result_zone = result.get('metadata', {}).get('zone', 'common')
        if result_zone not in allowed_zones:
            continue
        
        # Check risk level
        result_risk = result.get('metadata', {}).get('risk_level', 'low')
        if not risk_level_allowed(result_risk, max_risk):
            continue
        
        filtered.append(result)
    
    return filtered

def risk_level_allowed(result_risk: str, max_risk: str) -> bool:
    levels = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
    return levels.get(result_risk, 1) <= levels.get(max_risk, 4)
```

### 4. Zone Tags untuk KB Entries

Setiap dokumen di KB perlu ditandai dengan zone:

| Dokumen | Zone | Risk Level |
|---|---|---|
| CTRL-01 (Information security policies) | common | low |
| CTRL-09 (Networks security) | common | critical |
| CTRL-10 (Segregation of networks) | common | critical |
| SOP-7 (Remote access) | common | high |
| SOP-9 (Backup verification) | common | medium |
| SOP-14 (Change Advisory Board) | common | medium |
| SOP-15 (Restricted data handling) | restricted | critical |
| TOPO-SEGMENTS (Network topology overview) | common | medium |
| TOPO-HR-DATA (HR database segregation) | common | critical |
| TOPO-MKS-UPLINK (Makassar branch) | common | medium |
| TOPO-WMS-WINDOW (WMS replication window) | common | medium |
| Proyek Garuda (restricted entry) | restricted | critical |

### 5. Integration dengan Existing Pipeline

```python
def process_query(query: str) -> dict:
    # Step 1: Parse identity
    identity = parse_identity(query)
    
    # Step 2: Lookup permissions
    perms = lookup_permissions(identity.get('name'), identity.get('role'))
    
    # Step 3: Scrub query (remove PII, injection check)
    scrubbed = scrub_query(query)
    
    # Step 4: Check restricted triggers
    if restricted_touched(scrubbed):
        return {"status": "BLOCKED", "rc": 2}
    
    # Step 5: Search KBs
    results = search_kbs(scrubbed)
    
    # Step 6: Filter by permissions (NEW)
    filtered = filter_by_permissions(results, perms)
    
    # Step 7: Synthesize answer
    if not filtered:
        return {"status": "UNKNOWN", "rc": 3, "answer": "I don't know"}
    
    answer = synthesize_answer(filtered, query)
    return {"status": "OK", "rc": 0, "answer": answer}
```

## Test Cases

| Query | Identity | Allowed Zones | Expected |
|---|---|---|---|
| "Saya Andini, IT Admin. Boleh remote ke firewall Makassar?" | Andini | common;restricted;it-admin;infra-all;management | OK — full access |
| "Saya Budi, Finance. Boleh buka port 22 ke HR DB?" | Budi Santoso | common;finance;hr-read | OK — but no restricted project info |
| "Saya Rina, Intern. Siapa owner Proyek Garuda?" | Rina | common | BLOCKED — no restricted zone access |
| "Boleh buka port 22 ke HR DB?" (no identity) | unauthenticated | common | OK for common zone info, restricted blocked |
| "Saya Joko, Warehouse Sup. Boleh install Chrome?" | Joko | common;warehouse;ops-read | OK — common zone only |

## Files to Modify

1. `scripts/search_kb.py` — add identity parse + permissions lookup + zone filter
2. `config.json` — add `permissions_csv_path` and default permissions
3. `kb/` entries — add zone and risk_level metadata

## WorkBuddy Implementation Notes

Since WorkBuddy Skill Creator already built the skill, we need to:
1. Add a new file `scripts/permissions.py` for identity parsing and permissions lookup
2. Modify `scripts/search_kb.py` to call permissions filter before returning results
3. Update `config.json` with default permission settings
4. Ensure `permissions.csv` is accessible to the skill (either embedded or loaded from KB)

## Rollback Plan

If permission gate causes too many false positives:
1. Set default `allowed_zones` to `["common", "restricted"]` for all authenticated users
2. Only enforce strict filtering for `unauthenticated` users
3. Or disable permission gate entirely by setting `skip_permission_gate: true` in config
