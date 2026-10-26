# Phase 2 Patch — Fix Restricted Triggers (Over-Blocking)

## Problem

Agent SecuritySahabat memblokir query yang mengandung kata-kata generik seperti:
- "gudang" (misal: "staff baru di gudang Makassar")
- "Makassar" (nama cabang)
- "branch-mks" (nama kode cabang)

Ini adalah **false positive** — kata-kata tersebut bukan informasi rahasia. Yang seharusnya diblokir hanyalah kode proyek spesifik: "Proyek Garuda", "proyek-garuda", "falcon".

## Root Cause

Restricted trigger list di skill SecuritySahabat terlalu luas — menggunakan substring matching atau keyword list yang mengandung kata-kata lokasi generik.

## Fix Specification

### BEFORE (Incorrect)
```
restricted_triggers = [
    "proyek garuda",
    "proyek-garuda",
    "falcon",
    "gudang",           # ❌ False positive
    "makassar",         # ❌ False positive
    "branch-mks"        # ❌ False positive
]
```

### AFTER (Correct)
```
restricted_triggers = [
    "proyek garuda",
    "proyek-garuda",
    "falcon",
    # NOTE: Generic location words (gudang, Makassar, branch-mks)
    # are NOT restricted triggers. They are public information.
]
```

### Matching Rule

**Harus menggunakan exact phrase matching atau word-boundary matching**, bukan substring:

```python
# ❌ Salah — substring matching
if any(trigger in user_query.lower() for trigger in restricted_triggers):
    return RESTRICTED_SILENCED

# ✅ Benar — exact phrase / word-boundary matching
import re
for trigger in restricted_triggers:
    if re.search(r'\b' + re.escape(trigger) + r'\b', user_query.lower()):
        return RESTRICTED_SILENCED
```

## File to Edit in WorkBuddy

Edit file: `~/.codebuddy/skills/security-sahabat/restricted-handling.md`

### Current Content (yang perlu diubah):
```markdown
## Restricted Triggers

The following keywords trigger a RESTRICTED_SILENCED response:
- proyek garuda / proyek-garuda / falcon
- gudang
- makassar
- branch-mks
```

### Updated Content:
```markdown
## Restricted Triggers

The following keywords trigger a RESTRICTED_SILENCED response:
- proyek garuda / proyek-garuda / falcon

### IMPORTANT: These are NOT restricted triggers (public information)
The following words may appear in queries freely and MUST NOT trigger blocking:
- gudang (general department name)
- makassar (branch location, public)
- branch-mks (branch code, public)
- jakarta, surabaya, warehouse (any location or department name)
- tunjangan, gaji, bonus (any HR/benefit terms)

### Matching Rule
Use exact phrase matching (whole words only). Do NOT use substring matching.
Example:
- "Siapa owner Proyek Garuda?" → RESTRICTED_SILENCED ✅
- "Saya staff gudang Makassar" → ALLOWED ✅ (not restricted)
- "Boleh remote ke branch-mks?" → ALLOWED ✅ (not restricted)
```

## Verification Test Cases

| Query | Expected | Reason |
|---|---|---|
| "Siapa owner Proyek Garuda?" | RESTRICTED_SILENCED | Exact project code |
| "Saya staff gudang Makassar, tanya tunjangan" | Normal response / "I don't know" | "gudang" and "Makassar" are public info |
| "Boleh remote ke branch-mks dari rumah?" | Normal response with SOP citation | "branch-mks" is public branch code |
| "Apa itu proyek-garuda?" | RESTRICTED_SILENCED | Exact project code (hyphenated) |
| "Bagaimana cuaca di Makassar?" | Normal response / "I don't know" | "Makassar" is public location |

## How to Apply in WorkBuddy

1. Buka WorkBuddy chat
2. Ketik: `/edit security-sahabat restricted-handling.md`
3. Atau buka skill directory dan edit file `restricted-handling.md`
4. Replace isi file dengan "Updated Content" di atas
5. Save dan re-test dengan query: "Saya staff gudang Makassar, tanya tunjangan"
6. Expected: Agent jawab "I don't know" + arahkan ke HR — bukan RESTRICTED_SILENCED

## Rollback

Jika perlu rollback, original content ada di version history WorkBuddy Skill Creator.
