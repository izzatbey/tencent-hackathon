# SecuritySahabat

Asisten kebijakan security & compliance internal untuk karyawan
PT Nusantara Logistik Prima (studi kasus). Menjawab "boleh / tidak boleh"
**hanya** berdasarkan knowledge base perusahaan, dengan kutipan sumber wajib,
"tidak tahu" bila tidak ada bukti, dan topik restricted diperlakukan seolah
tidak ada.

> **Repo ini private.** `knowledge-base/source/topology.md` §6 berisi teks
> restricted asli. Jangan jadikan repo public tanpa menghapus file itu.

## Struktur

```
knowledge-base/   source/ (dokumen asli) · kb/ (dokumen terpecah + permissions.csv)
backend/          scripts/ (retrieval, guard, permission gate) · tests/ · config.json
frontend/         Chat UI (belum dimulai)
skill/            SKILL.md + references/ — instruksi Claude Skill
docs/             architecture.md — desain sistem & kontrak API
tools/            pack_skill.py — rakit dist/security-sahabat.skill
```

Desain lengkap, diagram, dan kontrak API: **[docs/architecture.md](docs/architecture.md)**.

## Mulai cepat

Butuh Python 3.10+ (tanpa dependensi eksternal).

```bash
# tanya knowledge base
python backend/scripts/search_kb.py -q "Saya Andini, IT Admin. Boleh buka port 22 ke db-hr-jkt-01?"

# 39 kasus regresi (wajib lulus sebelum merge)
python backend/tests/verify_matrix.py

# rakit paket Claude Skill -> dist/security-sahabat.skill
python tools/pack_skill.py
```

## Pembagian kerja

| Area | Owner |
| --- | --- |
| `backend/`, `skill/`, sistem | Izzat |
| `frontend/` | Rekan FE |
| `knowledge-base/` | Tim, perubahan lewat PR |

## Status

| Komponen | Status |
| --- | --- |
| Knowledge base (14 CTRL, 5 SOP, 10 TOPO, 1 restricted) | ✅ |
| Retrieval + anti over-blocking | ✅ |
| Permission gate (zona + risiko) | ✅ |
| Injection guard (query + evidence) & PII masking | ✅ |
| Claude Skill (paket `.skill`) | ✅ |
| HTTP API (`POST /api/ask`) | 🟡 |
| Answer composer (LLM) untuk web app | 🟡 |
| Frontend chat UI | 🟡 |
