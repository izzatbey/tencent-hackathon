# Project Memory — SecuritySahabat

Konteks kerja untuk sesi Claude Code berikutnya. Isi dari diskusi pembentukan
repo (26 Oktober 2026). Perbarui file ini bila ada keputusan baru.

## Ringkas

- **Apa:** agent Q&A security & compliance "boleh atau tidak?" dengan kutipan
  wajib, permission-aware, "tidak tahu" bila tak ada bukti, topik restricted
  = tidak ada. Studi kasus fiktif PT Nusantara Logistik Prima.
- **Untuk:** Tencent Cloud Hackathon Indonesia 2026, Challenge A (The
  Workplace Brain). Submission **1 Nov 2026**, Demo Day **27 Nov 2026**.
- **Acuan utama:** [adjusted_brief.md](adjusted_brief.md) (S1–S6, 20 test
  case, demo script) · desain: [docs/architecture.md](docs/architecture.md).
- **Tim:** Muhammad Izzat (izzatbey) — backend, skill, sistem. Rekan — frontend
  (belum diundang ke repo per 26 Okt). Komunikasi dalam Bahasa Indonesia.
- **Repo:** `izzatbey/tencent-hackathon`, **harus tetap private** —
  `knowledge-base/source/topology.md` §6 berisi teks restricted asli.

## Asal-usul kode

1. Dibangun di WorkBuddy (workbuddy.ai) sebagai Claude skill lewat
   skill-creator, task "Use the skill-creator skill". Fase 1–4 + context
   injection selesai di sana; sesi berhenti karena **kredit WorkBuddy habis**
   saat merampingkan `config.json`.
2. 47 artifact diunduh ke `Documents\Claude\workbuddy-artifacts\` (arsip asli,
   jangan diubah). `scripts/permissions.py` tidak terdaftar sebagai artifact —
   diambil dari dalam paket `security-sahabat.skill`.
3. Brief, spesifikasi fase, dan mock data dari
   `Downloads\2026-10-22-09-11-26\` dipindah ke repo (`adjusted_brief.md`,
   `docs/specs/`, `docs/workbuddy-memory/`, `knowledge-base/source/`).

## Struktur & cara kerja

- `backend/` berperan sebagai "skill dir": skrip mencari `config.json` di
  `backend/`, lalu KB di `backend/kb/` → fallback `knowledge-base/kb/`
  (`REPO_KB` di `search_kb.py`). Jangan pindahkan `scripts/` keluar `backend/`.
- `tools/pack_skill.py` merakit `dist/security-sahabat.skill` dari `skill/` +
  `backend/` + `knowledge-base/kb/` (44 file). `knowledge-base/source/` sengaja
  tidak ikut. `dist/` di-gitignore.
- `process_query()` di `backend/scripts/search_kb.py` = satu-satunya pintu
  masuk. Urutan tidak boleh ditukar: injection guard → PII mask → identitas +
  permission gate → retrieval → karantina context injection → flag konflik.
- Status/rc: `OK` 0 · `RESTRICTED_SILENCED` 2 · `NO_MATCH` 3 ·
  `INJECTION_DETECTED` 4.

## Keputusan yang mengikat

- **Tanpa kutipan = tanpa klaim.** Ragu → tidak boleh + eskalasi.
- **Persona = 9 persona brief** di `knowledge-base/kb/permissions.csv`
  (andini, ragil, sari, bimo, dewi, citra, damar, eka, indah; nama lengkap dari
  `contacts.csv`). Zona brief (segmen jaringan) dipetakan ke kosakata zona KB:
  `common`, `restricted`, `it-admin`, `ops-read`, `warehouse` (+ `hr`,
  `finance`, `fleet`, `security`, `management` untuk dokumen mendatang).
  `source/permissions.csv` = versi asli brief, tidak dipakai kode.
- **Proyek restricted** (`restricted: true`) terbuka hanya bila dokumen punya
  `project`, `allowed_projects` user memuatnya (atau `*`), DAN gate aktif.
  Saat ini: Proyek Garuda (`RESTRICTED-01`) → hanya Andini & Indah.
- **Existence leak:** bagi yang tidak berwenang, jawaban harus identik dengan
  proyek fiktif. Di skill: Template 3 kata per kata (bukan kalimat khusus).
  Di API: `RESTRICTED_SILENCED` wajib dikirim ke frontend sebagai `NO_MATCH`.
  `verify_matrix` menguji Garuda vs "Proyek Falcon".
- **Field yang tidak boleh keluar ke frontend:** `kb_root`,
  `permission_gate.dropped`, isi `quarantined`, `restricted_matches`,
  `mask_log`, `injection_check`, `permissions.allowed_projects`.
- Kutipan selalu verbatim; PII hanya disamarkan di pertanyaan.

## Tes

- `python backend/tests/verify_matrix.py` — **44 kasus, wajib 0 gagal**
  sebelum commit (phase2 13, phase3 14, injection 10, pii 4, ctx 1, leak 2).
- Di Windows set `PYTHONUTF8=1` dan `PYTHONIOENCODING=utf-8` dulu, kalau tidak
  output berhuruf non-ASCII rusak.

## Belum dikerjakan (per 26 Okt)

- HTTP API `POST /api/ask` + mapping status di atas (kontrak draf:
  `docs/architecture.md` §4).
- S1 parser LLM, S4 answer synthesizer untuk web app, S5 approval gate,
  S6 audit log.
- Indexing `cmdb.csv`, `chat_exports.jsonl`; klarifikasi "dua Budi"
  (`contacts.csv`, brief test #9).
- Frontend chat UI.

## Catatan / jebakan

- Bagi penanya tak berwenang, kata "proyek" saja sudah membungkam pertanyaan
  (kata itu eksklusif di metadata restricted). Menguntungkan untuk anti-leak,
  tapi pertanyaan sah seperti "share dokumen proyek ke vendor" ikut bisu.
- `allowed_projects` berisi nama proyek restricted — jangan pernah
  ditampilkan di UI atau log yang bisa dibaca user lain.
- Pencocokan identitas: nama (3) > role (2) > dept (1). "Saya Budi dari
  Finance" kini cocok ke Dewi lewat dept karena tak ada Budi di
  permissions.csv.
- `docs/specs/` dan `docs/workbuddy-memory/` adalah catatan historis WorkBuddy;
  nama persona lama (Rina, Joko) di sana sudah tidak berlaku.
