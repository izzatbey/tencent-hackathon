# Backend — SecuritySahabat

| Path | Isi |
| --- | --- |
| `scripts/search_kb.py` | `process_query()` — satu pintu masuk: injection → PII → identitas → retrieval |
| `scripts/permissions.py` | Permission gate: identitas, zona, risiko |
| `scripts/injection_guard.py` | Deteksi prompt injection (query + evidence) |
| `scripts/pii_masker.py` | Penyamaran NIK / telepon / email / EMP-ID / IP |
| `api/server.py` | HTTP API tipis (stdlib): `POST /api/ask`, `GET /api/personas`, audit log JSONL |
| `tests/verify_matrix.py` | 44 kasus regresi |
| `tests/test_accountability.py` | Edge case per 5 aturan akuntabilitas (unittest) |
| `tests/test_api.py` | DTO, audit log, validasi, HTTP |
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
python -m unittest discover -s backend/tests -v
```

Audit log: env `SECURITY_SAHABAT_AUDIT_LOG`, default `backend/logs/audit.jsonl`
(di-gitignore). Isinya pertanyaan yang sudah disamarkan, status internal dan
publik, `doc_id` yang dikutip, dan hash jawaban; tidak pernah teks mentah atau
`allowed_projects`.

## Berikutnya (🟡)

- Answer composer (LLM) yang mengikuti `skill/references/answer-playbook.md`;
  sampai itu ada, `answer` bernilai `null` untuk status `OK`.
- Existence leak lewat perbedaan respons: [docs/decisions/0002](../docs/decisions/0002-existence-leak-differential.md).
