# SecuritySahabat

**"Tanya boleh atau tidak. Dapat jawaban dengan bukti."**

Tencent Cloud Hackathon Indonesia 2026 — "AI CAN DO IT" · **Challenge A — The Workplace Brain**
Submission: **1 November 2026** · Demo Day: **27 November 2026**

> Brief lengkap (arsitektur, dataset, 20 test case, demo script, rencana fase):
> **[adjusted_brief.md](adjusted_brief.md)**

## Rumusan masalah

Di korporasi Indonesia, ketika karyawan ingin melakukan sesuatu — *buka port ke
server*, *install software di laptop kantor*, *share file ke vendor eksternal*,
*request akses ke database HR* — mereka sering tidak tahu:

1. **Apakah tindakan ini diperbolehkan** menurut policy perusahaan?
2. **Mengapa boleh atau tidak** — apa landasan compliance-nya (ISO 27001, SOP internal, regulasi)?
3. **Siapa yang harus approve** — siapa knowledge owner atau approver-nya?
4. **Apa risikonya** jika dilakukan tanpa pengawasan?

Jawabannya **tersebar** di SOP, chat, dokumen, dan ingatan senior staff.
Akibatnya keputusan tidak konsisten, security awareness rendah, dan orang
cenderung "tanya teman dulu" alih-alih "tanya sistem".

## Solusi

Agent Q&A security & compliance yang:

- **Selalu mengutip sumber** — SOP mana, control ID apa, pesan chat mana.
- **Permission-aware** — hanya menampilkan informasi yang boleh dilihat penanya;
  konten restricted diperlakukan persis seperti konten yang tidak ada.
- **Konsisten & objektif** — pertanyaan sama, jawaban sama.
- **Jujur bilang "tidak tahu"** — lalu mengarahkan ke SME yang tepat.
- **Tercatat** — siapa bertanya apa, sumber apa yang dipakai, jawaban apa yang diberikan.

**Pengguna:** karyawan umum, IT staff yang memvalidasi change request,
karyawan baru saat onboarding, dan manager yang butuh jawaban compliance konsisten.

Studi kasus: **PT Nusantara Logistik Prima** (fiktif) — perusahaan logistik,
kantor Jakarta (WIB), Makassar (WITA), Jayapura (WIT).

> **Repo ini private.** `knowledge-base/source/topology.md` §6 berisi teks
> restricted asli. Jangan jadikan repo public tanpa menghapus file itu.

---

## Struktur repo

```
adjusted_brief.md   Brief proyek — rumusan masalah, arsitektur S1–S6, test matrix
knowledge-base/     source/ (dokumen & data mock asli) · kb/ (dokumen terpecah + permissions.csv)
backend/            scripts/ (retrieval, guard, permission gate) · tests/ · config.json
frontend/           Chat UI (belum dimulai)
skill/              SKILL.md + references/ — instruksi Claude Skill
docs/               architecture.md · specs/ (spesifikasi per fase) · workbuddy-memory/
tools/              pack_skill.py — rakit dist/security-sahabat.skill
```

Desain sistem, diagram, dan kontrak API: **[docs/architecture.md](docs/architecture.md)**.

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

## Status terhadap brief (S1–S6)

| Tahap brief | Status | Catatan |
| --- | --- | --- |
| Mock dataset (§4) | ✅ | `knowledge-base/source/` |
| S1 Intake & parser (LLM) | 🟡 | Belum ada; identitas diparse rule-based di permission gate |
| S2 Permission gate | ✅ | Zona + risiko + anti existence-leak |
| S3 Retrieval — controls, sops, topology | ✅ | `kb/` terpecah per dokumen |
| S3 Retrieval — `cmdb.csv`, `chat_exports.jsonl` | 🟡 | Belum di-index backend |
| Conflict flagging (SOP-7, SOP-9) | ✅ | Dari catatan di KB, belum dari chat export |
| Injection guard (query + evidence) & PII masking | ✅ | |
| S4 Answer synthesizer (LLM) | 🟡 | Jalan di mode Claude Skill; belum ada untuk web app |
| Klarifikasi dua Budi (test #9) | 🟡 | `contacts.csv` belum dipakai |
| S5 Approval gate | 🟡 | |
| S6 Audit log | 🟡 | |
| HTTP API (`POST /api/ask`) | 🟡 | |
| Frontend chat UI | 🟡 | |
