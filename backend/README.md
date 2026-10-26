# Backend — SecuritySahabat

| Path | Isi |
| --- | --- |
| `scripts/search_kb.py` | `process_query()` — satu pintu masuk: injection → PII → identitas → retrieval |
| `scripts/permissions.py` | Permission gate: identitas, zona, risiko |
| `scripts/injection_guard.py` | Deteksi prompt injection (query + evidence) |
| `scripts/pii_masker.py` | Penyamaran NIK / telepon / email / EMP-ID / IP |
| `tests/verify_matrix.py` | 39 kasus regresi |
| `config.json` | Parameter yang bisa di-tune (lihat `skill/SKILL.md` §Konfigurasi) |

Lokasi KB: `--kb-root` → env `SECURITY_SAHABAT_KB` → `kb_root` di config →
`backend/kb/` → `knowledge-base/kb/` (default di repo ini).

```python
import sys; sys.path.insert(0, "backend/scripts")
import search_kb
result = search_kb.process_query("Boleh buka port 22 ke db-hr-jkt-01?")
```

## Berikutnya (🟡)

- HTTP API `POST /api/ask` — bungkus `process_query()`, saring field sesuai
  [docs/architecture.md §4](../docs/architecture.md#4-kontrak-api--draf-untuk-disepakati-fe--be).
- Answer composer (LLM) yang mengikuti `skill/references/answer-playbook.md`.
