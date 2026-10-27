# Backend — SecuritySahabat

| Path | Isi |
| --- | --- |
| `scripts/search_kb.py` | `process_query()` — satu pintu masuk: injection → PII → identitas → retrieval |
| `scripts/permissions.py` | Permission gate: identitas, zona, risiko |
| `scripts/injection_guard.py` | Deteksi prompt injection (query + evidence) |
| `scripts/pii_masker.py` | Penyamaran NIK / telepon / email / EMP-ID / IP |
| `scripts/audit_chain.py` | Audit log append-only berantai hash (S6), `--verify` |
| `scripts/llm.py` | Adapter LLM: `off` (default) · `claude` · `workbuddy` (stub) · `fake` |
| `scripts/kb_facts.py` | CMDB, direktori staf, kutipan terverifikasi |
| `scripts/cab_rules.py` | Rule engine Pra-CAB (SOP-14 + SOP-7, CTRL-01/09/12, topologi) |
| `scripts/cab_request.py` | Model change request, state machine, store dari audit log |
| `scripts/cab_intake.py` | Teks bebas → draft field CR (LLM, dengan pengaman) |
| `api/server.py` | HTTP API tipis (stdlib): `POST /api/ask`, `GET /api/personas`, routing Pra-CAB |
| `api/cab_api.py` | Endpoint Pra-CAB — kontrak: [docs/pracab-api.md](../docs/pracab-api.md) |
| `tests/verify_matrix.py` | 44 kasus regresi |
| `tests/test_accountability.py` | Edge case per 5 aturan akuntabilitas (unittest) |
| `tests/test_api.py` | DTO, audit log, validasi, HTTP |
| `tests/test_pracab.py` | Audit chain, adapter LLM, aturan SOP-14, state machine, intake, HTTP |
| `config.json` | Parameter yang bisa di-tune (lihat `skill/SKILL.md` §Konfigurasi) |

Lokasi KB: `--kb-root` → env `SECURITY_SAHABAT_KB` → `kb_root` di config →
`backend/kb/` → `knowledge-base/kb/` (default di repo ini).

```python
import sys; sys.path.insert(0, "backend/scripts")
import search_kb
result = search_kb.process_query("Boleh buka port 22 ke db-hr-jkt-01?")
```

## API

```bash
python backend/api/server.py                          # http://127.0.0.1:8787
python backend/api/server.py --static frontend/dist   # sekalian melayani UI
python backend/api/server.py --demo                   # + POST /api/demo/clock
python -m unittest discover -s backend/tests -v
```

Audit log: env `SECURITY_SAHABAT_AUDIT_LOG`, default `backend/logs/audit.jsonl`
(di-gitignore). Satu rantai hash untuk tanya-jawab dan Pra-CAB. Isinya teks
yang sudah disamarkan, status internal dan publik, `doc_id` yang dikutip, hasil
precheck, dan setiap aksi (termasuk yang ditolak); tidak pernah teks mentah atau
`allowed_projects`. Periksa rantainya:

```bash
python backend/scripts/audit_chain.py --verify backend/logs/audit.jsonl
```

## LLM

| Env | Nilai |
| --- | --- |
| `SECURITY_SAHABAT_LLM` | `off` (default), `claude`, `workbuddy` |
| `SECURITY_SAHABAT_LLM_MODEL` | default `claude-opus-5-5` |
| `SECURITY_SAHABAT_LLM_EFFORT` | default `medium` |

`claude` butuh `pip install anthropic` dan kunci (`ANTHROPIC_API_KEY` atau
profil `ant auth login`). LLM hanya dipakai `POST /api/intake` untuk menyalin
teks bebas ke field draft; risiko, approver, dan verdict selalu dari
`cab_rules.py`. LLM mati atau gagal → teks disalin apa adanya ke `description`.

## Berikutnya (🟡)

- Provider WorkBuddy (`llm.WorkBuddyProvider`) setelah API-nya diketahui.
- Answer composer (LLM) untuk `/api/ask` yang mengikuti `skill/references/answer-playbook.md`;
  sampai itu ada, `answer` bernilai `null` untuk status `OK`.
- Existence leak lewat perbedaan respons: [docs/decisions/0002](../docs/decisions/0002-existence-leak-differential.md).
