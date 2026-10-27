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
- **Tim:** Muhammad Izzat (izzatbey): backend, skill, sistem. Farrez: frontend
  dan test case UI/UX + core. Wafi: anggota tim. Komunikasi dalam Bahasa Indonesia.
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
  `backend/` + `knowledge-base/kb/` (52 file per 27 Okt). `knowledge-base/source/` sengaja
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
- `python -m unittest discover -s backend/tests` — core + API + Pra-CAB
  (`test_pracab.py`). Kegagalan yang
  diketahui ditulis `@unittest.expectedFailure` (existence leak versi Inggris,
  tes #7 SLA crane). Status matriks brief: `docs/testing.md`.
- Frontend: `npm run check`, `npm test`, `npm run e2e` di `frontend/`.
- Di Windows set `PYTHONUTF8=1` dan `PYTHONIOENCODING=utf-8` dulu, kalau tidak
  output berhuruf non-ASCII rusak.

## Keputusan 27 Okt (Farrez)

- Frontend Vite + Svelte 5 + TS, API tipis stdlib di `backend/api/`, tes core
  pakai `unittest` (`docs/decisions/0001`).
- `answer` bernilai `null` untuk `OK` sampai S4 ada; UI tidak menyimpulkan.
- Injection guard menormalkan Unicode (NFKC + buang karakter Cf) sebelum
  memindai; PII masker mengenali NIK/HP berspasi, bertitik, bertanda hubung.

## Keputusan 27 Okt (Izzat): Pra-CAB

- Fitur utama backend = **Pra-CAB** (change request dicek terhadap SOP-14,
  dirutekan ke approver, ditahan sampai disetujui). Detail: `docs/decisions/0003`,
  kontrak frontend: `docs/pracab-api.md`.
- Keputusan selalu dari `cab_rules.py`; LLM (`llm.py`) hanya untuk intake
  teks bebas. Default `SECURITY_SAHABAT_LLM=off`; uji coba pakai `claude`,
  nanti WorkBuddy.
- State CR = putar ulang audit log berantai hash (`audit_chain.py`). Jangan
  menulis state di luar `CabStore._emit`.
- Setiap cek punya `basis` (`sop`/`interpretasi`/`sistem`); interpretasi wajib
  diberi label, bukan disamarkan sebagai bunyi SOP.
- `kb/cmdb.csv` dan `kb/directory.csv` (tanpa email/telepon) ditambahkan ke KB.

## Belum dikerjakan (per 27 Okt)

- Pra-CAB: UI frontend; klarifikasi "dua Budi" di intake; usulan jendela waktu
  alternatif; data hari libur nasional (belum ada di dataset); provider WorkBuddy.

- **Existence leak lewat beda respons** ("Project Garuda" dibungkam, "Project
  Falcon" dijawab): opsi di `docs/decisions/0002`, menunggu Izzat + Farrez.
- Tes #7: pertanyaan di luar data tetap mendapat bukti tak relevan (butuh
  ambang relevansi atau S4).
- S4 answer synthesizer untuk `/api/ask`. (S1 intake LLM, S5 approval gate, dan
  replay audit log sudah ada untuk Pra-CAB; `/api/ask` belum memakai S1.)
- Indexing `cmdb.csv`, `chat_exports.jsonl`; klarifikasi "dua Budi"
  (`contacts.csv`, brief test #9).
- Autentikasi: API mempercayai `user`/`role` dari request (pemilih persona demo).

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
