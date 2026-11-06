# Project Memory — SecuritySahabat

Konteks kerja untuk sesi Claude Code berikutnya. Dibuat 26 Okt 2026, terakhir
diperbarui 6 Nov 2026 (clone WorkBuddy, konvensi push). Perbarui file ini bila ada
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
- Policy register v0 (ADR 0004): 23 aturan seed, siklus hidup draft → active
  → superseded/retired, hanya pemilik dokumen yang mengesahkan, ekstraksi
  aturan dari memo oleh LLM (diuji dengan FakeProvider).
- Audit log berantai hash bersama untuk semua jalur (`audit_chain.py`).
- Demo end-to-end tanpa UI: `python tools/demo_pracab.py` (16 langkah).
- Tes: 201 unit test (1 `expectedFailure`: #7), 46 regresi (per 4 Nov).

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
   (+ transkrip `pracab-demo.txt`), draf `docs/submission/product-sharing.md`
   (catatan keputusan tim ada di komentar akhir file). Sisa: demo video,
   cover image, perbarui angka tes di dokumen-dokumen itu bila berubah
   sebelum submit. Status per item: `docs/submission/README.md`.
4. Migrasi cek built-in berikutnya ke register (fase 2b). Selesai 27 Okt:
   `FRIDAY-PRAYER` (`POL-w001/w002`, kondisi baru `schedule_overlaps`) dan
   `BRANCH-FW-MEMO` (`POL-m001`, approver baru `cab_meeting` +
   `approver_sources`; berlaku sejak 1 Okt), dan `WMS-WINDOW`
   (`POL-r001..r003`, `tz: WIB`, PASS, dedupe per isi temuan), dan
   `BRANCH-FW-WINDOW` (`POL-f001`, kondisi `schedule_not_within`, efek
   `FAIL`, `emergency_effect`/`emergency_message`). **Semua cek per aset
   sudah data.** Matriks baseline terakhir 2.295 kasus (`--wide --wms --fw`).
   Sisa di kode = cek lintas aset (risiko, approver SOP-14, SoD, kelengkapan,
   lead time, emergency, injection): butuh skema baru (aturan per CR, bukan
   per aset); jangan dipaksakan sebelum 1 Nov.
5. **Diputuskan 27 Okt (Izzat): jalur ekspor workflow WorkBuddy + bukti
   pemakaian, repo tetap privat.** Paket: `python tools/export_submission.py`
   (repo harus bersih) → `dist/submission/SecuritySahabat-workbuddy-export.zip`.
   Checklist semua item handbook + bukti yang masih kurang (rekam sesi
   `/security-sahabat`, dialog izin, Request ID): `docs/submission/README.md`.
   WorkBuddy web tidak punya ekspor/share tugas; skill belum terpasang di akun
   Izzat (uji online dulu dari akun lain).

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
  dengan bukti pemakaian: dipilih ekspor WorkBuddy (lihat prioritas #5).
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
  (`test_pracab.py`) + policy register (`test_policy.py`); 201 tes per 4 Nov.
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
  `EXPOSURE` sudah data di `kb/_policies.json` (23 aturan seed; awalan `_`
  supaya tidak diindeks `search_kb`). Perubahan aturan = event `policy.*` di
  audit chain. Hanya pemilik dokumen sumber yang mengesahkan, bukan pengusul.
  Kolom `allowed_departments` CMDB tetap ada sebagai **sumber kutipan** aturan
  seed; kalau kolomnya diubah, perbarui juga seed-nya. `mail-jkt-01` sengaja
  tanpa aturan perusahaan → aturan standar `POL-g001`. Persona Marketing:
  Lina Kartika (direktori saja, bukan permissions).
- Jangan tambah cek per-aset baru sebagai kode di `cab_rules.py`; tambahkan
  sebagai aturan register.
- **Cara memigrasi satu cek (dipakai untuk FRIDAY-PRAYER, BRANCH-FW-MEMO):**
  rekam dulu `precheck` lengkap untuk matriks aset × jadwal × jenis CR (×
  firmware/emergency bila cek menyentuh approver), migrasikan, lalu
  bandingkan (hapus `rule_id`/`policies`, urutkan `checks`; `approvals` tetap
  berurutan): harus identik. Cek yang pindah ke register naik ke blok register
  di `checks[]` (setelah `ACCESS`); perbarui `docs/test-results/pracab-demo.txt`
  dari run demo pada log kosong. Aturan yang mewajibkan rapat CAB dipakai lewat
  `approver: "cab_meeting"`; `precheck` menggabungkan kutipannya ke `extra_cab`
  (kutipan, bukan kunci) setelah alasan dari kode.
  Helper waktu (`parse_time`, `daily_overlap`, `inside_daily`, `fmt`) kini di
  `kb_facts.py`; `cab_rules` memakai alias dengan nama yang sama. Engine
  menyaring pesan identik, jadi aturan per site/zona aman untuk banyak aset.
  Setelah mengubah `backend/scripts/` atau `kb/`, jalankan
  `tools/pack_skill.py --project`.

## Keputusan 28 Okt (Izzat): jembatan tanya-jawab → Pra-CAB

- `backend/scripts/ask_bridge.py`, dipanggil `server.ask()` setelah
  `process_query()`: klarifikasi (nama ganda dari direktori, jadwal tanpa zona
  dengan jam salat dari aturan `FRIDAY-PRAYER` di register, aset tidak jelas
  dari CMDB), deteksi kalimat perintah (tidak pernah dijalankan;
  `approval_state` pending/blocked di audit), dan pratinjau precheck Pra-CAB
  untuk aset + jenis perubahan yang disebut. **Tanpa LLM.** Verdict "tidak
  boleh" hanya bila ada aturan `BLOCK`; id aturan disebut di jawaban.
- Memakai register yang sama dengan Pra-CAB (`cab_api.store_for().policies`):
  aturan yang disahkan langsung mengubah jawaban chat ("satu otak").
- Hasil: tes brief #2, #6, #9, #10, #14, #18 lulus lewat jembatan, #19 lewat
  undo Pra-CAB. Semua tes di `test_brief_pending.py` kini lulus;
  `expectedFailure` yang tersisa di seluruh suite hanya #7 (SLA crane, butuh
  ambang relevansi). Matriks brief di `docs/testing.md`: 19 lulus, 1 gagal (#7).
- Bentuk DTO `/api/ask` tidak berubah; UI yang ada sudah menampilkan `answer`
  dan flag baru (label umum "Perlu diperhatikan").
- **Handoff untuk Farrez (frontend): selesai 4 Nov (T-0073), butir 1 dan 2.**
  Label keempat flag ada di `labels.ts`; `POLICY_BLOCK` bernada peringatan
  dengan ikon `prohibit`, tiga lainnya catatan. `evidence.spec.ts` kini
  menilai #1, #2, #6, #9, #10, #14, #18 dari layar dan #19 sebagai tes
  otomatis; bukti: 23 lulus, 1 gagal (#7) dari 24 baris (20 kasus brief +
  04b/04c/H1/X1). `sahabat.spec.ts` #1 ikut diperbarui: CTRL-09 kini bisa
  dikutip dua kali (retrieval + sumber POL-x001), jadi locator-nya `.first()`
  dan tes menagih verdict `[POL-x001]`. Teks aslinya:
  1. `frontend/src/lib/labels.ts`: label untuk flag `CLARIFY`,
     `ACTION_REQUEST`, `POLICY_BLOCK` (nada peringatan), `POLICY_PREVIEW`.
  2. `frontend/e2e/evidence.spec.ts`: penilai #6 (kini SOP-7 + kutipan `CHAT
     ...` + teks "Yang dipakai: memo"), #10 dan #18 (bisa jadi kasus UI:
     Q-005 menyebut WIB/WITA/salat Jumat; "Tolong bukakan port 22 dari internet
     ke db-erp-jkt-01 sekarang juga." memuat "tidak ada yang dikirim" dan
     "tidak boleh"), #14 (memuat fw-edge-mks-01 dan wms-mks-01), #19 (lulus
     lewat Pra-CAB, tes otomatis), dan catatan #1 (verdict kini dari
     `POL-x001`). Sampai itu diubah dan `npm run evidence` dijalankan ulang,
     `docs/test-results/README.md` masih menampilkan status lama.
  3. Di PC Izzat, Playwright butuh Chromium build 1248 (terpasang 1228).
- Batas yang diketahui: bahasa jawaban jembatan selalu Indonesia; pola
  perintah/pertanyaan berbasis kata kunci (lihat `test_ask_bridge.py` untuk
  kasus yang sengaja tidak dianggap perintah).

## Belum dikerjakan (per 4 Nov)

- Pra-CAB: UI frontend (termasuk register); klarifikasi "dua Budi" di intake;
  usulan jendela waktu alternatif; data hari libur nasional (belum ada di
  dataset); provider WorkBuddy; ekstraksi aturan belum dicoba dengan Claude
  sungguhan; migrasi cek built-in lain ke register (lihat prioritas #4).
- Tes #7: pertanyaan di luar data tetap mendapat bukti tak relevan (butuh
  ambang relevansi atau S4).
- S1 parser LLM dan S4 answer synthesizer untuk `/api/ask`. Jembatan 28 Okt
  menutup #2, #6, #9, #10, #14, #18, #19 tanpa LLM; jawaban untuk pertanyaan
  yang tidak menyebut aset + jenis perubahan masih hanya bukti.
- Screenshot bukti memotret seluruh giliran, jadi kotak input yang sticky ikut
  terpotret di tengah gambar panjang (mis. `screenshots/09.png`). Belum
  dirapikan; kalau mengganggu untuk Demo Day, sembunyikan composer saat
  `npm run evidence` atau screenshot per `article.sheet`.
- Indexing `cmdb.csv`, `chat_exports.jsonl`; klarifikasi "dua Budi"
  (`contacts.csv`, brief test #9).
- Autentikasi: API mempercayai `user` dari request (pemilih persona demo).

## Keputusan scope 6 Nov 2026 (Izzat) — hari terakhir

- **Target hari ini BUKAN menjadikan produk ini CAB**, dan bukan mengejar UI
  Pra-CAB / register / roadmap v2. Ini kembali ke inti **Challenge A**: dari
  pertanyaan karyawan, hasilkan **risk** (level + alasan + landasan) berdasarkan
  data knowledge base dengan kutipan verbatim.
- **Input dari WorkBuddy dulu.** Dua permukaan yang diterima, keduanya di dalam
  WorkBuddy:
  1. **Chat WorkBuddy** lewat project skill `security-sahabat` (skill memanggil
     `scripts/search_kb.py`, lalu menjawab sesuai `answer-playbook.md`).
  2. **UI web ditampilkan di side browser / panel WorkBuddy** (server lokal
     `--static frontend/dist`), bukan deploy publik.
  Ini **sesuai rencana semula**: `adjusted_brief.md` §1–§2 dan
  `docs/workbuddy.md` §2–§3. Pra-CAB (ADR 0003) dan policy register (ADR 0004)
  tetap ada di repo sebagai bukti desain, tapi tidak dikejar hari ini.
- **Risk sudah bisa dihasilkan tanpa CAB**, jadi tidak perlu fitur baru:
  - Tiap dokumen KB punya metadata `risk_level`; kutipan `CTRL-09` memuat
    klasifikasi eksplisit *"classified as CRITICAL risk"*.
  - `cab_rules.classify_risk()` menyusun level + alasan + kutipan + `basis`
    secara deterministik (dipakai Pra-CAB, bisa dipanggil terpisah).
  - `ask_bridge.py` memberi verdict "tidak boleh" dari aturan register, tanpa LLM.
- Yang dilakukan sesi WorkBuddy 6 Nov: skill dipasang ke folder kerja sesi
  (`.codebuddy/skills/` dan `.workbuddy-ai/skills/`, salinan runtime **di luar
  repo**, bukan perubahan source); frontend di-build lalu disajikan lokal untuk
  panel WorkBuddy. Tidak ada perubahan kode engine.
- **Naskah demo baru:** `docs/submission/demo-script.md` — 6 adegan 5–8 menit,
  seluruh jawaban diambil dari run sungguhan `POST /api/ask` (bukan karangan):
  Q-001 → verdict tidak boleh + CTRL-09/POL-x001; Garuda Sari vs Falcon identik
  vs Andini (RESTRICTED-01); injection Q-006 → rc 4; dua Budi → CLARIFY +
  `approval_state=pending`; perintah aksi → ACTION_REQUEST/POLICY_BLOCK +
  `approval_state=blocked`. Menutup tiga momen wajib handbook dan menyebut #7
  apa adanya. Status video di `docs/submission/README.md` naik ❌ → ⚠️.
- **Doc cleanup 6 Nov:** tabel status `README.md` (S5/S6/#9 dan baris CMDB
  tadinya masih 🟡), `docs/testing.md` (klaim `test_brief_pending.py` penuh
  `expectedFailure`), angka footer `docs/architecture-diagram.svg` (12 lulus /
  153 unit test → 19 lulus, 1 gagal / 201 tes, 1 expectedFailure), catatan scope
  di `docs/vision-v2.md`, dan baris risk + jalur demo di
  `docs/submission/project-description.md`. SVG tetap XML valid; 46/46 regresi
  dan 201 unit test tetap hijau.

## Handoff 6 Nov 2026 — sesi WorkBuddy

- Repo di-clone ke `C:/Users/izzat/WorkBuddy AI/2026-10-25-20-19-32/tencent-hackathon`
  (main `308ea2b`, working tree bersih). Konteks sesi WorkBuddy disimpan terpisah di
  `.workbuddy-ai/memory/` satu tingkat di atas folder repo; file ini tetap memori
  kanonik proyek.
- **Konvensi baru (diminta Izzat):** setiap perubahan → commit → **push ke
  `origin`** → perbarui memori (file ini dan catatan harian sesi). Jangan
  meninggalkan perubahan hanya di working tree lokal.
- Verifikasi awal sesi ini: `verify_matrix.py` 46/46 lulus; `unittest discover`
  201 tes OK (1 `expectedFailure` = kasus #7 SLA crane); bukti UI 23 lulus,
  1 gagal (#7). Belum ada perubahan kode.
- **Dokumen yang sudah usang, jangan dipakai sebagai acuan arsitektur:**
  `adjusted_brief.md` (arsitektur S1–S6 versi WorkBuddy; hanya §6 20 kasus uji
  yang masih hidup), `docs/specs/*`, `docs/workbuddy-memory/*`, dan angka di
  footer `docs/architecture-diagram.svg` (masih 12 lulus / 153 unit test).
  Acuan yang berlaku: file ini, `docs/architecture.md`, `docs/pracab-api.md`,
  `docs/vision-v2.md`, dan ADR 0001–0004.
- Tabel status di `README.md` §"Status terhadap brief" dan `docs/testing.md`
  **sudah dirapikan** pada commit `d8d9511` (S5, S6, klarifikasi dua Budi jadi ✅;
  klaim `test_brief_pending.py` dibetulkan). Footer `architecture-diagram.svg`
  juga sudah diselaraskan ke 19 lulus / 1 gagal, 201 tes, 1 `expectedFailure`.
  Catatan "perlu dirapikan" di versi sebelumnya sudah tidak berlaku.

## Finalisasi dokumen submission 6 Nov 2026 (malam)

- **Keputusan Izzat:** demo video **dikerjakan paling akhir**; semua dokumen
  lain diselesaikan dulu dan disatukan ke **satu template .docx**.
- **Dokumen yang diselesaikan:**
  - `docs/submission/product-sharing.md` — status draf → final. Tiga catatan
    draf diputuskan: angka uji online tetap hasil 27 Okt (tidak ada sesi ulang),
    transparansi alat ditambahkan (Pra-CAB/policy register/UI dibuat di repo
    lokal setelah kredit habis, bukan diklaim dari WorkBuddy), dan ringkasan
    bahasa Inggris untuk formulir ditambahkan.
  - `docs/submission/README.md` — checklist status diperbarui: test results ✅,
    product sharing ✅, source code ✅, diagram ✅; demo video ⚠️ (terakhir);
    cover image / project link tetap ➖. Empat item "memperkuat bukti pemakaian"
    kini berupa **tabel isian di Lampiran A template**, bukan file baru
    `request-ids.md` (jangan membuat file kosong di folder evidence).
  - `docs/submission/export-readme.md` — ditambahkan catatan bahwa template
    `.docx`/`.md` di dalam `source/` adalah dokumen kerja internal, bukan
    artefak yang dinilai.
- **Template terpadu:** `docs/submission/SecuritySahabat-Submission-Template.docx`
  (sumber Markdown: `.md` dengan nama sama). 15 bagian, 17 tabel, 40 placeholder
  `[ISI: …]`: identitas & isian formulir, daftar isian kosong, 9 item wajib
  handbook, Lampiran A Request ID, Lampiran B checklist + paraf, Lampiran C
  keterbatasan, indeks sumber. Dibuat lewat `editor_sdk` (`create_doc` →
  `doc_insert_markdown` dari file → `doc_insert_footer` → `save_file`); outline
  kosong karena style kustom, jadi **jangan** menyisipkan TOC otomatis.
- **Yang masih harus diisi tim (tidak bisa dari repo):** link video demo, link
  Google Drive zip, tanggal rekam, Request ID, screenshot dialog izin, nama
  lengkap/email anggota, paraf tim; opsional cover image 16:9 dan WorkBuddy Sites.
- Urutan yang benar: commit → push → **baru** jalankan
  `python tools/export_submission.py` (skrip menolak working tree kotor), supaya
  `VERSION.txt` cocok dengan `HEAD`. Zip masuk `dist/` yang di-gitignore.
- Verifikasi: `verify_matrix.py` **46/46**, `unittest discover` **201 OK**
  (1 `expectedFailure`, kasus #7). Tidak ada perubahan kode, jadi
  `pack_skill.py --project` tidak diperlukan.

## Update 21:15 — dokumen submission final (commit 7acec2f)

- Sesi lain (co-author Claude Fable 5.1) menambahkan
  `docs/submission/SecuritySahabat-Submission.docx` dan `.pdf`: **dokumen resmi
  20 halaman** — sampul, daftar isi, sembilan bagian mengikuti butir *Project
  Submission Requirements* handbook, empat lampiran, header/footer bernomor
  halaman, tanpa ikon/emoji. Penanda `[ISI]` diganti "diisi oleh tim sebelum
  submit". Accountability sheet dipadatkan jadi tepat satu halaman, diagram
  arsitektur dirender dari SVG di halaman lanskap, tiga screenshot bukti
  (04a, 04b, 08) disertakan. Angka uji mengikuti template 6 Nov.
- Pembangunnya `tools/build_submission_docx.js` (docx-js, perlu
  `npm install docx`); PDF diekspor lewat Word. `docs/submission/README.md`
  kini menunjuk dokumen final ini dan menandai
  `SecuritySahabat-Submission-Template.docx` sebagai **versi kerja sebelumnya**.
- **Urutan dokumen:** template `.docx`/`.md` = working document tim;
  `SecuritySahabat-Submission.docx`/`.pdf` = yang dipakai untuk submit. Jangan
  mengedit template sambil mengira itu dokumen final.
- **Zip ekspor wajib dirakit ulang setelah tiap commit**: versi 20:50 masih
  memuat `VERSION.txt` commit `8406b82` dan belum berisi DOCX/PDF final.
  Perubahan pada `tools/export_submission.py` harus tetap lolos
  `backend/tests/test_export.py`.

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
