# Project Memory — SecuritySahabat

Konteks kerja untuk sesi Claude Code berikutnya. Dibuat 26 Okt 2026, terakhir
diperbarui 27 Okt 2026 (policy register v0). Perbarui file ini bila ada
keputusan baru atau item "belum dikerjakan" selesai.

## Ringkas

- **Apa:** dua jalur di atas satu inti penjaga yang sama.
  1. **Tanya-jawab** (`/api/ask`): agent Q&A security & compliance "boleh atau
     tidak?" dengan kutipan wajib, permission-aware, "tidak tahu" bila tak ada
     bukti, topik restricted = tidak ada.
  2. **Pra-CAB** (`/api/requests`, `/api/policies`): change request / permintaan
     akses dicek terhadap policy perusahaan, diberi risiko + allowance
     (boleh / tidak / dengan syarat) + approver, lalu ditahan sampai approver
     yang benar menyetujui. Ini **fitur utama dan arah produk** (lihat
     "Arah produk").
  Studi kasus fiktif PT Nusantara Logistik Prima.
- **Untuk:** Tencent Cloud Hackathon Indonesia 2026, Challenge A (The
  Workplace Brain). Submission **1 Nov 2026**, Demo Day **27 Nov 2026**.
  20 tes Challenge A tetap dilaporkan walau fokus bergeser ke Pra-CAB.
- **Acuan utama:** [adjusted_brief.md](adjusted_brief.md) (S1–S6, 20 test
  case, demo script) · desain: [docs/architecture.md](docs/architecture.md) +
  [docs/architecture-diagram.svg](docs/architecture-diagram.svg) · visi &
  roadmap: [docs/vision-v2.md](docs/vision-v2.md) · kontrak Pra-CAB:
  [docs/pracab-api.md](docs/pracab-api.md) · ADR: `docs/decisions/0001–0004`.

## Arah produk (proyeksi)

Tujuan akhir bukan chatbot, melainkan **"CAB decision brain"**: satu otak
kepatuhan per perusahaan yang deterministik dan bisa diaudit.

- Perusahaan memasukkan KB-nya sendiri (SOP, memo, CMDB, topologi). Di
  bawahnya ada KB global (ISO 27001, NIST CSF / SP 800-53, GDPR, UU PDP) yang
  berlaku bila perusahaan belum punya aturan. Perusahaan > standar; lebih
  baru > lebih lama; konflik ditampilkan, tidak dirata-ratakan.
- User mengajukan tiket bebas → LLM menyalin ke field → engine menilai dengan
  aturan → risiko + allowance + approver + kutipan + tingkat kepastian
  (`basis`) → manusia menyetujui → eksekusi (mock) → semua tercatat.
- **Nilai jual = policy register:** aturan adalah data, bukan kode. Dokumen
  masuk → LLM mengusulkan aturan berkutipan → **pemilik dokumen** mengesahkan
  → keputusan berikutnya berubah, keputusan lama tetap, semuanya di audit log.
- LLM tidak pernah memutus izin, risiko, approver, atau verdict. Tiga peran
  LLM: intake tiket, ekstraksi usulan aturan, (rencana) penilaian fallback
  RAG yang dilabel "pendapat" dan tidak pernah `READY` tanpa manusia.
- Roadmap (detail di `docs/vision-v2.md` §7): 0 Pra-CAB ✅ · 2a policy
  register v0 ✅ · 1 UI Pra-CAB & register (Farrez), video, accountability
  sheet → 1 Nov · 2b migrasi cek built-in ke register → Demo Day · 3 upload KB
  (chunking, metadata dikonfirmasi, default restricted) · 4 ekstraksi aturan +
  "suntingan manusia → usulan aturan" · 5 retrieval hybrid + KB global lengkap
  · 6 konektor nyata + SSO.
- Keputusan desain yang sudah diambil untuk v2: aturan = data; default
  **restricted** untuk dokumen unggahan sampai owner mengisi metadata; teks ISO
  berhak cipta → hanya ID kontrol + parafrase (pola `CTRL-xx`); NIST/GDPR/UU
  PDP boleh dikutip; dokumen berinstruksi ke AI dikarantina, tidak dikirim ke
  LLM; dependensi baru (embedding) baru setelah 1 Nov.

## Status per 27 Okt (handoff)

Sudah ada dan teruji (main):

- Tanya-jawab: pipeline `process_query`, non-interference (ADR 0002),
  identitas dari persona, audit fail-closed, `--replay` (Farrez).
- Pra-CAB (ADR 0003): intake LLM → normalisasi + PII mask → scan injection →
  precheck (`cab_rules.py` + policy register) → state machine + approval per
  slot (SoD, rapat CAB dulu) → mock dispatch + undo 60 dtk → audit.
- Policy register v0 (ADR 0004): 16 aturan seed, siklus hidup draft → active
  → superseded/retired, hanya pemilik dokumen yang mengesahkan, ekstraksi
  aturan dari memo oleh LLM (diuji dengan FakeProvider).
- Audit log berantai hash bersama untuk semua jalur (`audit_chain.py`).
- Demo end-to-end tanpa UI: `python tools/demo_pracab.py` (16 langkah).
- Tes: 153 unit test (8 `expectedFailure` disengaja), 46 regresi.

Belum diverifikasi: ekstraksi aturan dengan Claude sungguhan (`pip install
anthropic` + `ANTHROPIC_API_KEY`, lalu `SECURITY_SAHABAT_LLM=claude` dan
`demo_pracab.py --llm`). Provider WorkBuddy masih stub karena API-nya belum
diketahui.

Prioritas berikutnya, urut:

1. UI Pra-CAB + register (Farrez) dari `docs/pracab-api.md`; tombol dari
   `allowed_actions`, label `basis` dibedakan.
2. Uji ekstraksi aturan dengan Claude sungguhan, catat hasilnya. **Terblokir
   per 27 Okt:** di mesin Izzat belum ada `ANTHROPIC_API_KEY` maupun paket
   `anthropic`; Izzat yang harus memasangnya (agent tidak boleh mengisi key).
3. Materi submission. Sudah ada (27 Okt): `docs/submission/accountability-sheet.md`,
   `docs/submission/project-description.md`, `docs/test-results/pracab.md`
   (+ transkrip `pracab-demo.txt`). Sisa: demo video, perbarui angka tes
   di kedua dokumen itu bila berubah sebelum submit.
4. Migrasi cek built-in berikutnya ke register (fase 2b).
5. Repo private vs syarat handbook "source code public atau ekspor workflow
   WorkBuddy": putuskan sebelum submit (lihat bagian Repo di bawah).

## Peta backend

| Modul | Peran |
| --- | --- |
| `backend/scripts/search_kb.py` | `process_query()` tanya-jawab (retrieval + gate + guard) |
| `backend/scripts/permissions.py` · `injection_guard.py` · `pii_masker.py` | penjaga bersama |
| `backend/scripts/audit_chain.py` | log append-only berantai hash, `verify()` |
| `backend/scripts/llm.py` | adapter LLM: `off` (default) · `claude` · `workbuddy` (stub) · `fake` |
| `backend/scripts/kb_facts.py` | CMDB, direktori, kutipan terverifikasi (`cite`, `cite_cmdb`, `cite_chat`) |
| `backend/scripts/cab_rules.py` | precheck Pra-CAB: cek built-in + panggil policy engine |
| `backend/scripts/policy_register.py` | skema aturan, engine, `PolicyStore` (seed + event `policy.*`) |
| `backend/scripts/cab_request.py` | model CR, state machine, `CabStore` (memegang `PolicyStore`) |
| `backend/scripts/cab_intake.py` · `policy_intake.py` | LLM: tiket → field draft · memo → usulan aturan |
| `backend/api/server.py` · `cab_api.py` | HTTP stdlib; `--demo` membuka `POST /api/demo/clock` |
| `knowledge-base/kb/_policies.json` | seed register (awalan `_` = tidak diindeks retrieval) |

## Menjalankan & demo

```
cd frontend && npm ci --ignore-scripts && npm run build && cd ..
python backend/api/server.py --static frontend/dist --demo     # http://127.0.0.1:8787
python tools/demo_pracab.py                                    # terminal kedua
python backend/scripts/audit_chain.py --verify backend/logs/audit.jsonl
```

Jangan jalankan dua server ke file audit yang sama: kunci audit chain hanya
berlaku dalam satu proses.

`demo_pracab.py` **tidak idempoten**: aturan yang disahkan di langkah 14
tersimpan di audit log, jadi run kedua terhadap log yang sama membuat langkah
12 BLOCKED (seharusnya READY). Untuk video/bukti: hentikan server, pindahkan
`backend/logs/audit.jsonl`, nyalakan lagi, baru jalankan demo sekali.

Di Windows jangan jalankan skrip repo dengan `python -I`: flag itu mengabaikan
`PYTHONUTF8`, dan output demo (karakter `↳`, `⚠`) crash di konsol cp1252.
- **Tim:** Muhammad Izzat (izzatbey): backend, skill, sistem. Farrez: frontend
  dan test case UI/UX + core. Wafi: anggota tim. Komunikasi dalam Bahasa Indonesia.
- **Repo:** `izzatbey/tencent-hackathon`, **harus tetap private** —
  `knowledge-base/source/topology.md` §6 berisi teks restricted asli.
  Handbook meminta source code public **atau** ekspor workflow WorkBuddy
  dengan bukti pemakaian: belum diputuskan jalur mana.
- **Alur git:** Farrez kerja di branch `farrez/...` + PR; Izzat kadang langsung
  ke `main`. Selalu `git fetch` dan cek file yang disentuh kedua sisi sebelum
  push; selesaikan conflict dengan mempertahankan perubahan kedua pihak, lalu
  jalankan semua tes.

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

- `.codebuddy/skills/security-sahabat/` = project skill WorkBuddy, salinan
  persis hasil `tools/pack_skill.py --project`. Jalankan ulang perintah itu
  setiap mengubah `skill/`, `backend/scripts/` atau `knowledge-base/kb/`;
  `test_skill_sync.py` merah bila lupa. Panduan WorkBuddy: `docs/workbuddy.md`.

- `backend/` berperan sebagai "skill dir": skrip mencari `config.json` di
  `backend/`, lalu KB di `backend/kb/` → fallback `knowledge-base/kb/`
  (`REPO_KB` di `search_kb.py`). Jangan pindahkan `scripts/` keluar `backend/`.
- `tools/pack_skill.py` merakit `dist/security-sahabat.skill` dari `skill/` +
  `backend/` + `knowledge-base/kb/` (52 file per 27 Okt). `knowledge-base/source/` sengaja
  tidak ikut. `dist/` di-gitignore.
- `process_query()` di `backend/scripts/search_kb.py` = satu-satunya pintu
  masuk. Urutan tidak boleh ditukar: injection guard → PII mask → identitas +
  permission gate → retrieval → karantina context injection → flag konflik.
- Status/rc: `OK` 0 · `NO_MATCH` 3 · `INJECTION_DETECTED` 4. Tidak ada
  status khusus untuk topik restricted (sejak 27 Okt, ADR 0002).

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
- **Existence leak = non-interference** (ADR 0002, diputuskan Farrez 27 Okt):
  dokumen yang tidak boleh dibaca penanya (restricted tanpa project yang cocok,
  zona di luar akses) dilewati SEBELUM penilaian dan tidak ikut idf, jadi
  keluarannya sama persis dengan bila dokumen itu tidak ada. Jangan kembalikan
  pembungkaman berbasis kata kunci: "Project Garuda" vs "Project Falcon" dulu
  bocor karena itu. Diuji `NonInterferenceTest` + kasus `HIDDEN` di verify_matrix.
- **Identitas API** hanya dari `user` yang persis terdaftar; klaim di teks
  pertanyaan diabaikan (`identity_from_text=False`). Mode skill tetap membaca
  identitas dari teks karena tidak punya sumber lain.
- **Field yang tidak boleh keluar ke frontend:** `kb_root`,
  `permission_gate` (termasuk `readable_ids`), isi `quarantined`, `mask_log`,
  `injection_check`, `permissions.allowed_projects`.
- Kutipan selalu verbatim; PII hanya disamarkan di pertanyaan.

## Tes

- `python backend/tests/verify_matrix.py` — **46 kasus, wajib 0 gagal**
  sebelum commit (phase2 13, phase3 14, injection 10, pii 4, ctx 1, leak 4).
- `python -m unittest discover -s backend/tests` — core + API + Pra-CAB
  (`test_pracab.py`) + policy register (`test_policy.py`); 153 tes per 27 Okt.
  Kegagalan yang diketahui ditulis `@unittest.expectedFailure` (tes #7 SLA
  crane, spesifikasi `test_brief_pending.py`). Status matriks brief dan
  katalog edge case: `docs/testing.md`.
- `test_api` kasus `DELETE` kadang `ConnectionAbortedError` saat suite penuh
  berjalan di Windows; lulus bila dijalankan sendiri. Ulang dulu sebelum
  menganggapnya regresi.
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
- Setiap cek punya `basis` (`sop`/`standar`/`interpretasi`/`sistem`);
  interpretasi wajib diberi label, bukan disamarkan sebagai bunyi SOP. Daftar
  interpretasi yang perlu disahkan owner ada di ADR 0003.
- `kb/cmdb.csv` dan `kb/directory.csv` (tanpa email/telepon) ditambahkan ke KB.
- **Tujuan akhir = CAB decision brain** (`docs/vision-v2.md`): KB perusahaan di
  atas KB global (ISO/NIST/GDPR), aturan jadi data (policy register), LLM
  mengusulkan aturan dan manusia mengesahkan. Jangan merombak sebelum 1 Nov.
- **Policy register v0** (ADR 0004, `policy_register.py`): `ACCESS-SCOPE` dan
  `EXPOSURE` sudah data di `kb/_policies.json` (16 aturan seed; awalan `_`
  supaya tidak diindeks `search_kb`). Perubahan aturan = event `policy.*` di
  audit chain. Hanya pemilik dokumen sumber yang mengesahkan, bukan pengusul.
  Kolom `allowed_departments` CMDB tetap ada sebagai **sumber kutipan** aturan
  seed; kalau kolomnya diubah, perbarui juga seed-nya. `mail-jkt-01` sengaja
  tanpa aturan perusahaan → aturan standar `POL-g001`. Persona Marketing:
  Lina Kartika (direktori saja, bukan permissions).
- Jangan tambah cek per-aset baru sebagai kode di `cab_rules.py`; tambahkan
  sebagai aturan register.

## Belum dikerjakan (per 27 Okt)

- Pra-CAB: UI frontend (termasuk register); klarifikasi "dua Budi" di intake;
  usulan jendela waktu alternatif; data hari libur nasional (belum ada di
  dataset); provider WorkBuddy; ekstraksi aturan belum dicoba dengan Claude
  sungguhan; migrasi cek built-in lain ke register.
- Tes #7: pertanyaan di luar data tetap mendapat bukti tak relevan (butuh
  ambang relevansi atau S4).
- S1 parser LLM dan S4 answer synthesizer untuk `/api/ask`; S5 approval gate
  untuk aksi yang tersirat di pertanyaan `/api/ask`. Spesifikasinya ada sebagai
  tes `expectedFailure` di `backend/tests/test_brief_pending.py` (#2, #6, #9,
  #10, #14, #18, #19). Pra-CAB sudah punya intake LLM, approval gate, dan
  undo sendiri; belum disambungkan ke `/api/ask`.
- Indexing `cmdb.csv`, `chat_exports.jsonl`; klarifikasi "dua Budi"
  (`contacts.csv`, brief test #9).
- Autentikasi: API mempercayai `user` dari request (pemilih persona demo).

## Catatan / jebakan

- Karena tidak ada lagi pembungkaman, "Siapa owner Proyek Garuda?" dari Sari
  bisa mendapat bukti lemah yang tak relevan (SOP-14), persis seperti untuk
  proyek fiktif. Itu bukan kebocoran; itu masalah ambang relevansi (tes #7).
- `allowed_projects` berisi nama proyek restricted — jangan pernah
  ditampilkan di UI atau log yang bisa dibaca user lain.
- Pencocokan identitas: nama (3) > role (2) > dept (1). "Saya Budi dari
  Finance" kini cocok ke Dewi lewat dept karena tak ada Budi di
  permissions.csv.
- `docs/specs/` dan `docs/workbuddy-memory/` adalah catatan historis WorkBuddy;
  nama persona lama (Rina, Joko) di sana sudah tidak berlaku.
