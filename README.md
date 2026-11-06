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
MEMORY.md           Konteks & keputusan tim (dibaca otomatis Claude Code lewat CLAUDE.md)
knowledge-base/     source/ (dokumen & data mock asli) · kb/ (dokumen terpecah + permissions.csv)
backend/            scripts/ (retrieval, guard, permission gate) · tests/ · config.json
frontend/           Chat UI (Vite + Svelte + TS)
skill/              SKILL.md + references/ — instruksi Claude Skill
docs/               architecture.md · specs/ (spesifikasi per fase) · workbuddy-memory/
tools/              pack_skill.py — rakit dist/security-sahabat.skill
```

Desain sistem, diagram, dan kontrak API: **[docs/architecture.md](docs/architecture.md)**.
Tujuan akhir (CAB decision brain: KB perusahaan + standar global, policy
register, LLM+RAG+agent) dan roadmap v2: **[docs/vision-v2.md](docs/vision-v2.md)**.

## Mulai cepat

Butuh Python 3.10+ (engine tanpa dependensi) dan Node 22 (hanya untuk UI).
Di Windows jalankan dulu `set PYTHONUTF8=1` dan `set PYTHONIOENCODING=utf-8`
(PowerShell: `$env:PYTHONUTF8=1; $env:PYTHONIOENCODING="utf-8"`).

### Menjalankan aplikasi di laptop

```bash
cd frontend
npm ci --ignore-scripts
npm run build
cd ..
python backend/api/server.py --static frontend/dist
```

Buka http://127.0.0.1:8787, pilih persona di kanan atas, lalu bertanya.
Setiap jawaban punya nomor catatan; baca ulang catatannya dengan
`python backend/api/server.py --replay <nomor>`. Mode pengembangan UI (hot
reload) ada di [frontend/README.md](frontend/README.md).

Pra-CAB belum punya UI. Jalankan server dengan `--demo`, lalu di terminal lain
`python tools/demo_pracab.py` untuk alur lengkap: precheck SOP-14 → dispatch
ditolak → rapat CAB → approve → mock dispatch → undo → verifikasi audit log.
Kontrak endpoint: [docs/pracab-api.md](docs/pracab-api.md).

### Menjalankan lewat WorkBuddy

Buka folder repo ini sebagai folder kerja tugas di WorkBuddy. Skill
`.codebuddy/skills/security-sahabat/` ikut terbaca, jadi agen WorkBuddy bisa
langsung menjawab dengan engine yang sama. Publikasi link live lewat WorkBuddy
Sites dan bukti pemakaian untuk submission: [docs/workbuddy.md](docs/workbuddy.md).

### Tes

```bash
python backend/tests/verify_matrix.py          # 46 kasus regresi, wajib 0 gagal
python -m unittest discover -s backend/tests   # core, API, skill, spesifikasi fitur yang belum ada
cd frontend && npm run check && npm test && npm run e2e
cd frontend && npm run evidence                # screenshot bukti -> docs/test-results/
python tools/mutate_guards.py                  # setiap penjaga keamanan punya tes yang merah
```

Hasil per test case brief beserta screenshot: [docs/test-results/](docs/test-results/README.md).
Rancangan tes dan sumbernya: [docs/testing.md](docs/testing.md).

### Paket skill

```bash
python tools/pack_skill.py            # dist/security-sahabat.skill (zip)
python tools/pack_skill.py --project  # perbarui .codebuddy/skills/security-sahabat/
```

## Pembagian kerja

| Area | Owner |
| --- | --- |
| `backend/`, `skill/`, sistem | Izzat |
| `frontend/`, tes UI/UX | Farrez |
| `knowledge-base/` | Tim, perubahan lewat PR |

## Status terhadap brief (S1–S6)

> **Catatan 6 Nov 2026 (hari terakhir):** target demo bukan menjadikan produk ini
> CAB. Fokusnya **risk dari knowledge base lewat input chat WorkBuddy** (atau UI
> di panel WorkBuddy), sesuai rencana awal Challenge A. Naskah demo:
> [docs/submission/demo-script.md](docs/submission/demo-script.md). Pra-CAB dan
> policy register tetap ada sebagai bukti desain, tidak didemokan hari ini.

| Tahap brief | Status | Catatan |
| --- | --- | --- |
| Mock dataset (§4) | ✅ | `knowledge-base/source/` |
| S1 Intake & parser (LLM) | 🟡 | Belum ada; identitas diparse rule-based di permission gate |
| S2 Permission gate | ✅ | Zona + risiko + anti existence-leak; 9 persona brief |
| Garuda untuk persona berwenang (test #3) | ✅ | Lewat `allowed_projects`; selain itu identik dengan proyek fiktif |
| S3 Retrieval — controls, sops, topology | ✅ | `kb/` terpecah per dokumen |
| S3 Retrieval — `cmdb.csv`, `chat_exports.jsonl` | 🟡 | Tidak diindeks sebagai teks; dipakai lewat `kb_facts.py`, `cab_rules.py`, `ask_bridge.py` (CMDB) dan kutipan memo 1 Okt (chat) |
| Conflict flagging (SOP-7, SOP-9) | ✅ | Dari catatan di KB, belum dari chat export |
| Injection guard (query + evidence) & PII masking | ✅ | |
| S4 Answer synthesizer (LLM) | 🟡 | Jalan di mode Claude Skill; belum ada untuk web app |
| Klarifikasi dua Budi (test #9) | ✅ | `ask_bridge.py` memakai `kb/directory.csv`, tanpa LLM |
| S5 Approval gate | ✅ | Perintah aksi dari chat tidak dijalankan; `approval_state` pending/blocked di audit. State penuh ada di Pra-CAB |
| S6 Audit log | ✅ | Rantai hash `audit_chain.py`, `--replay`, `GET /api/audit/verify` |
| HTTP API (`POST /api/ask`) | ✅ | `backend/api/server.py`, stdlib; `answer` null sampai S4, kecuali klarifikasi/verdict dari `ask_bridge.py` |
| Audit log per pertanyaan | ✅ | JSONL ber-`q_id` dari API, `--replay <q_id>` |
| Frontend chat UI | ✅ | Svelte, `frontend/` |
| Pra-CAB: rule engine SOP-14, state machine, approval, mock dispatch + undo | ✅ | Backend; [kontrak API](docs/pracab-api.md), [ADR 0003](docs/decisions/0003-pracab-fondasi-backend.md) |
| Audit log berantai hash + verifikasi | ✅ | `backend/scripts/audit_chain.py`, `GET /api/audit/verify`; `--replay` membaca rantai yang sama |
| Adapter LLM (Claude untuk uji coba, WorkBuddy stub) | 🟡 | Dipakai intake Pra-CAB; default `off` |
| Existence leak (non-interference) | ✅ | Dokumen tak terbaca dilewati sebelum pencarian, [ADR 0002](docs/decisions/0002-existence-leak-differential.md) |
| Status test matrix | | [docs/testing.md](docs/testing.md) |
