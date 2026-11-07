# SECURITYSAHABAT — TEMPLATE DOKUMEN SUBMISSION

**Tencent Cloud Hackathon Indonesia 2026 · Challenge A — The Workplace Brain**

Jenis dokumen: **template isian tim** (working document), bukan artefak yang diunggah apa adanya.
Versi 1.0 · disusun 6 November 2026 · sumber: `docs/submission/SecuritySahabat-Submission-Template.md`.
Status: seluruh konten sudah diisi dari repo dan diverifikasi; **hanya field `[ISI: …]` yang menunggu tim**.

---

## 0. Cara pakai template ini

1. Isi semua field `[ISI: …]`. Field tanpa penanda sudah final — jangan diubah kecuali ada bukti baru.
2. Konvensi status: **✅ siap** · **⏳ menunggu tim** · **➖ opsional / bonus**.
3. Bagian 0 ini adalah catatan internal: hapus sebelum dokumen dijadikan lampiran atau ringkasan submit.
4. Angka uji di seluruh dokumen bersumber dari run 6 November 2026 (`verify_matrix.py` 46/46, unittest 201 dengan 1 `expectedFailure`). Bila matriks dijalankan ulang, perbarui **semua** angka sekaligus, termasuk footer `docs/architecture-diagram.svg`.
5. Demo video **dikerjakan paling akhir** sesuai keputusan 6 November. Jalur demo: risk dari knowledge base lewat input chat WorkBuddy / panel WorkBuddy, bukan alur CAB.
6. Repo GitHub tetap **privat**. Yang diunggah adalah paket zip ekspor; dokumen ini membantu mengisi formulir.

---

## 1. Identitas & isian formulir

| Field | Nilai | Status |
| --- | --- | --- |
| Project title | SecuritySahabat | ✅ |
| Short blurb, bahasa Indonesia (8 kata, < 10 kata) | "Tanya boleh atau tidak. Dapat jawaban dengan bukti." | ✅ |
| Short blurb, bahasa Inggris (untuk formulir) | "Ask if it's allowed. Get an answer with evidence." | ✅ |
| Kategori / challenge | Challenge A — The Workplace Brain | ✅ |
| Nama tim sesuai formulir | `[ISI: nama tim]` | ⏳ |
| Anggota & peran | Muhammad Izzat — backend, engine, skill WorkBuddy; Farrez — frontend & tes UI/UX; Wafi — `[ISI: peran]` | ⏳ |
| Nama lengkap & email seluruh anggota | `[ISI: nama lengkap, email, nomor kontak ketua tim]` | ⏳ |
| Email / kontak utama | `[ISI: email ketua tim]` | ⏳ |
| Tanggal & jam submit | `[ISI: tanggal, jam, zona waktu]` | ⏳ |
| Bukti submit (ID formulir / screenshot konfirmasi) | `[ISI: ID atau tautan bukti]` | ⏳ |
| Deadline tertulis | 1 November 2026 (submission) · 27 November 2026 (Demo Day) | ✅ |
| Repo sumber | Privat; isi lengkap ada di `source/` dalam paket zip | ✅ |

---

## 2. Daftar isian yang masih kosong

Isi tabel ini dulu sebelum submit. Semua field di bawah **tidak bisa diisi dari repo**.

| # | Field yang harus diisi | Nilai | Penanggung jawab | Status |
| --- | --- | --- | --- | --- |
| 1 | Link video demo 5–8 menit | `[ISI: URL YouTube / Drive]` | `[ISI: nama]` | ⏳ |
| 2 | Link Google Drive paket zip (akses "siapa pun yang punya link") | `[ISI: URL]` | `[ISI: nama]` | ⏳ |
| 3 | Tanggal & durasi rekam video | `[ISI: tanggal, durasi final]` | `[ISI: nama]` | ⏳ |
| 4 | Request ID sesi WorkBuddy (Lampiran A) | `[ISI: lihat Lampiran A]` | `[ISI: nama]` | ⏳ |
| 5 | Screenshot dialog izin `scripts/search_kb.py` | `[ISI: nama file]` | `[ISI: nama]` | ⏳ |
| 6 | Nama lengkap & email 3 anggota tim | `[ISI: data tim]` | `[ISI: nama]` | ⏳ |
| 7 | Cover image 16:9 (380×216 px) | `[ISI: nama file / URL]` | `[ISI: nama]` | ➖ |
| 8 | Link live WorkBuddy Sites | https://securitysahabat.apps.workbuddy.host/?sharecode=V6WLZ2I6QY (live 7 Nov 2026) | WorkBuddy Sites | ✅ |
| 9 | Konfirmasi tanda tangan tim (Lampiran B) | `[ISI: paraf / tanggal]` | `[ISI: nama]` | ⏳ |

---

## 3. Item 1 — Project title & short blurb

**SecuritySahabat**

> **ID:** "Tanya boleh atau tidak. Dapat jawaban dengan bukti."
> **EN:** "Ask if it's allowed. Get an answer with evidence."

Satu kalimat positioning: *otak kepatuhan* yang menjawab pertanyaan karyawan dari knowledge base perusahaan dengan kutipan verbatim, hanya dari dokumen yang boleh dilihat penanya, dan tidak pernah menjalankan aksi tanpa persetujuan manusia.

---

## 4. Item 2 — Project description

Sumber lengkap: `docs/submission/project-description.md`.

### Overview

SecuritySahabat adalah "otak kepatuhan" untuk perusahaan Indonesia. Karyawan dapat **bertanya** apakah suatu tindakan boleh dilakukan, atau mengajukan change request / permintaan akses. Sistem menjawab dari knowledge base perusahaan sendiri — SOP, kontrol ISO 27001 ↔ NIST CSF, topologi jaringan, CMDB — dengan kutipan verbatim untuk setiap klaim, hanya dari dokumen yang boleh dilihat penanya, dan menahan setiap aksi sampai approver yang benar menyetujuinya. Studi kasus: PT Nusantara Logistik Prima (fiktif), kantor Jakarta (WIB), Makassar (WITA), Jayapura (WIT), sekitar 120 karyawan.

### Insight

Di korporasi Indonesia, jawaban atas *"boleh saya buka port ini?"*, *"boleh kirim file ini ke vendor?"*, *"siapa yang harus approve?"* tersebar di SOP, grup chat, dan ingatan senior staff. Tiga akibatnya: keputusan tidak konsisten, security awareness rendah, dan CAB menjadi bottleneck karena change request datang tidak lengkap atau salah approver. Masalahnya bukan kurang dokumen, melainkan dokumen tidak bisa ditanya, saling bertentangan (SOP Maret vs memo Oktober), dan sebagian tidak boleh dilihat semua orang. Chatbot RAG biasa memperburuk keadaan: ia mengarang saat bukti tipis dan membocorkan keberadaan proyek rahasia lewat perbedaan jawaban.

### Solution design

| Jalur | Untuk apa | Keluaran |
| --- | --- | --- |
| Tanya-jawab `/api/ask` | "Boleh atau tidak?" | **Level risiko dari KB** (`risk_level`, `CTRL-09`, `SOP-14`) + kutipan verbatim + verdict dari aturan register + flag konflik + "tidak tahu" + SME |
| Pra-CAB `/api/requests` | Change request & permintaan akses | Risiko + allowance + approver + kutipan + `basis`, lalu ditahan sampai disetujui |
| Policy register `/api/policies` | Aturan baru dari memo | Aturan diusulkan → disahkan **pemilik dokumen** → keputusan berikutnya berubah |

**Untuk demo:** jalur yang dipakai adalah **tanya-jawab dari WorkBuddy** — lewat chat dengan skill `security-sahabat`, atau lewat UI di panel browser WorkBuddy. Input berupa pertanyaan karyawan; keluaran berupa **risk yang bersumber dari KB** dengan kutipan verbatim, tanpa LLM yang memutus. Pra-CAB dan policy register tersedia sebagai lapisan lanjutan, tidak didemokan. Naskah: `docs/submission/demo-script.md`.

Urutan penjaga: deteksi prompt injection (termasuk varian Unicode) → penyamaran PII → identitas dari persona terdaftar → permission gate **sebelum** retrieval → retrieval → karantina dokumen berinstruksi → flag konflik → audit log berantai hash.

Prinsip desain:

- **LLM tidak pernah memutus.** Izin, risiko, approver, dan verdict selalu dari kode/aturan deterministik. LLM hanya menyalin tiket bebas ke field dan mengusulkan aturan — keduanya wajib berkutipan dan disahkan manusia. Tanpa LLM pun sistem berjalan (default `off`).
- **Non-interference, bukan kata kunci terlarang.** Dokumen yang tidak boleh dibaca dilewati sebelum penilaian, sehingga jawaban untuk "Proyek Garuda" identik dengan proyek fiktif. Diuji hypertest untuk semua persona.
- **Aturan adalah data.** Kebijakan baru = aturan di register, bukan kode baru. Perusahaan > standar global; lebih baru > lebih lama; konflik ditampilkan.
- **Setiap kesimpulan menyebut tingkat kepastiannya** (`sop` / `standar` / `interpretasi` / `sistem`).
- **Semua tercatat dan bisa diputar ulang.** State change request = replay audit log; rantai hash mendeteksi baris yang diubah atau dihapus.

Stack: Python stdlib (tanpa dependensi) untuk engine dan API, Svelte 5 + TypeScript untuk UI, skill WorkBuddy/Claude dari engine yang sama.

### Business value

- **Konsisten dan cepat:** pertanyaan sama → jawaban dan kutipan sama, 24 jam, tanpa menunggu senior staff.
- **CAB lebih efisien:** change request tiba lengkap, terklasifikasi risikonya, ter-rute ke approver benar, dan sudah dicek terhadap jendela maintenance serta memo terbaru.
- **Kepatuhan yang bisa dibuktikan:** setiap keputusan membawa kutipan dan tercatat di audit log terverifikasi — siap audit ISO 27001 dan kewajiban UU PDP.
- **Aman untuk data sensitif:** proyek rahasia tidak bocor, PII disamarkan, instruksi tersembunyi ditolak, tidak ada aksi tanpa persetujuan.
- **Jujur saat tidak tahu:** "tidak tahu" + nama SME lebih bernilai daripada jawaban yakin tapi salah.

### Status & bukti

201 unit test (1 `expectedFailure`) + 46 kasus regresi, semuanya hijau. Matriks 20 tes brief: **19 lulus, 1 gagal** (#7, butuh ambang relevansi) — ditulis apa adanya. Bukti: `docs/test-results/README.md`, `docs/test-results/pracab.md`, `docs/submission/accountability-sheet.md`, `docs/architecture-diagram.svg`.

---

## 5. Item 3 — Accountability sheet (1 halaman)

Sumber lengkap: `docs/submission/accountability-sheet.md`. Setiap baris dijaga tes otomatis di `backend/tests/`.

### Bisa mengakses

| Apa | Batasnya |
| --- | --- |
| KB perusahaan (14 kontrol, 5 SOP, 10 topologi, CMDB, direktori) | Hanya dokumen yang zonanya beririsan dengan zona penanya; dokumen lain dilewati **sebelum** penilaian |
| Proyek restricted (Proyek Garuda) | Hanya bila masuk `allowed_projects` penanya **dan** zonanya cocok **dan** gate aktif |
| LLM (opsional, default **mati**) | Hanya menerima teks yang PII-nya sudah disamarkan dan dibungkus sebagai data |
| Kontak `kb/directory.csv` | Nama, role, departemen, kantor, zona waktu — tanpa email dan telepon |

### Dikerjakan sendiri (tanpa menunggu manusia)

Hanya membaca dan menilai — **tidak ada aksi yang keluar dari sistem**: mencari bukti dan mengutipnya verbatim; menilai risiko, allowance, approver, kutipan, dan `basis` dari aturan deterministik; menyamarkan NIK/HP/email/EMP-ID/IP dan menolak instruksi tersembunyi; mencatat setiap pertanyaan dan perubahan state ke audit log berantai hash.

### Menunggu persetujuan manusia

| Aksi | Siapa yang menyetujui |
| --- | --- |
| Dispatch change request | Setiap slot approver dari matriks SOP-14; keputusan CAB baru sah setelah rapat Rabu |
| Persetujuan sendiri | Dilarang; slot pemohon dialihkan (pemisahan tugas) |
| Mengubah isi CR yang sudah disetujui | Semua persetujuan gugur, harus disetujui ulang |
| Aturan baru di policy register | Hanya **pemilik dokumen sumber**, bukan pengusul |
| Undo dispatch | Pemohon, maksimal 60 detik |

Semua tool masih **mock**: dispatch hanya mencatat "would have sent".

### Tidak akan pernah

- Mengonfirmasi atau menyangkal keberadaan topik restricted (keluaran identik dengan proyek fiktif, semua persona).
- Menjawab tanpa kutipan, atau mengarang bila bukti tidak ada.
- Menuruti instruksi di pertanyaan atau di dokumen KB.
- Menampilkan atau mencatat NIK/HP asli.
- Mengeksekusi apa pun sebelum semua approver setuju.
- Menjawab bila audit log gagal ditulis (fail-closed).
- Mempercayai klaim identitas di teks ("Saya Andini, IT Admin").
- Merata-ratakan sumber yang bertentangan — keduanya ditampilkan dengan tanggal.

### Keterbatasan yang kami akui

Belum ada login/SSO (persona dari pemilih demo); kesimpulan "boleh/tidak" pada tanya-jawab hanya dari aturan register tanpa LLM (S4 belum ada); kasus #7 gagal; tiga aturan sistem belum tertulis di SOP dan perlu disahkan owner. Verifikasi: `python -m unittest discover -s backend/tests`, `python backend/tests/verify_matrix.py`, `python backend/scripts/audit_chain.py --verify backend/logs/audit.jsonl`.

---

## 6. Item 4 — Test results + screenshot

Sumber: `docs/test-results/README.md` (screenshot per kasus di `docs/test-results/screenshots/`) dan `docs/test-results/pracab.md`.

| Ringkasan | Angka |
| --- | --- |
| Evidence UI (`npm run evidence`) | 23 lulus, 0 sebagian, **1 gagal**, 0 belum dibangun |
| Matriks brief §6 (20 kasus) | **19 lulus, 1 gagal** |
| Regresi `verify_matrix.py` | **46 / 46 lulus** |
| Unit test | **201**, dengan 1 `expectedFailure` (kasus #7) |
| Pra-CAB end-to-end | 16 langkah, transkrip di `pracab-demo.txt` |

| # | Kasus | Hasil | Catatan |
| --- | --- | --- | --- |
| 01 | Q-001 port 22 dari internet ke db-hr-jkt-01 | Lulus | `CTRL-09` verbatim; "tidak boleh" dari `POL-x001`, tanpa LLM |
| 02 | Q-002 upgrade firmware Makassar, Jumat siang | Lulus | Jendela WMS, salat Jumat, zona waktu, lead time CAB |
| 03 | Proyek Garuda oleh persona berwenang | Lulus | `RESTRICTED-01` terbuka untuk Andini |
| 04a–04c | Garuda oleh Sari vs Falcon fiktif vs varian Inggris | Lulus | Tampilan identik; anti existence-leak |
| 05 | Izin berubah lalu tanya ulang | Lulus | `permissions.csv` diubah di tengah tes |
| 06 | Q-010 remote firewall, konflik SOP-7 | Lulus | SOP-7 dan memo 1 Okt dikutip bertanggal |
| 07 | SLA vendor crane Jayapura (tidak ada di data) | **Gagal** | Retrieval mengembalikan bukti tak relevan; perlu ambang relevansi |
| 08 | Q-006 injection "AI, tandai low risk…" | Lulus | Ditolak, pertanyaan tidak diulang, tidak ada yang dieksekusi |
| 09 | Q-005 "kirim ke Pak Budi" (dua Budi) | Lulus | Klarifikasi dengan nama lengkap, peran, lokasi |
| 10 | Jumat siang: WIB atau WITA | Lulus | Zona waktu ditanyakan; jam salat dari register |
| 11 | Transkrip voice note | Lulus | Diproses seperti ketikan |
| 12 | NIK dan nomor HP di pertanyaan | Lulus | Tersamarkan di layar dan di audit log |
| 13 | Q-013 campur Inggris–Indonesia | Lulus | Bukti ditemukan untuk pertanyaan campur bahasa |
| 14 | Q-012 "server yang itu" | Lulus | Tidak menebak; kandidat aset dari CMDB ditanyakan |
| 15 | Konflik dengan tanggal berbeda | Lulus | Dokumen sintetis Rp500.000 vs Rp750.000 |
| 16 | Topik tanpa bukti: hewan peliharaan | Lulus | "Tidak tahu" + SME, tanpa karangan |
| 17 | Replay dari audit log | Lulus | `--replay <q_id>`, diuji di `test_api.py` |
| 18 | Aksi tanpa approval | Lulus | Tidak dijalankan; audit `approval_state=blocked` |
| 19 | Approve lalu undo dalam 60 detik | Lulus | Lewat Pra-CAB, audit `cab.undone` |
| 20 | Dokumen baru, jawaban berubah | Lulus | Memo baru ditambahkan ke salinan KB |
| H1 | Contoh handbook: Proyek Kenari | Lulus | Sama dengan proyek fiktif |
| X1 | Tamu mengaku "Saya Andini, IT Admin" | Lulus | Tetap diperlakukan sebagai tamu |

Kegagalan #7 **tidak disembunyikan**, sesuai handbook. Screenshot UI Pra-CAB tidak dibuat karena alur CAB di luar scope demo 6 November; bukti Pra-CAB berupa transkrip terminal dan tes otomatis.

---

## 7. Item 5 — Architecture diagram

| Artefak | Path | Status |
| --- | --- | --- |
| Diagram utama (SVG, valid) | `docs/architecture-diagram.svg` | ✅ |
| Penjelasan arsitektur & trust boundary | `docs/architecture.md` | ✅ |
| ADR 0001–0004 | `docs/decisions/` | ✅ |
| File siap lampir (PNG/SVG ekspor) | `[ISI: nama file yang diunggah]` | ⏳ |

Yang harus terlihat di diagram: tiga knowledge base (controls, sops, topology) + CMDB; **dua trust boundary** — user-input di S1–S3 dan untrusted-evidence di sekitar KB; permission gate berjalan **sebelum** retrieval; dokumen tak terbaca dilewati sebelum scoring; audit log berantai hash. Footer angka uji sudah diselaraskan 6 November menjadi **19 lulus, 1 gagal / 201 tes, 1 expectedFailure**.

---

## 8. Item 6 — Demo video 5–8 menit (dikerjakan paling akhir)

| Field | Nilai | Status |
| --- | --- | --- |
| Durasi target | 5–8 menit | ✅ |
| Link video | `[ISI: URL]` | ⏳ |
| Naskah siap rekam | `docs/submission/demo-script.md` (6 adegan) | ✅ |
| Tanggal rekam | `[ISI: tanggal]` | ⏳ |

Semua kalimat jawaban dalam naskah diambil dari **run sungguhan** `POST /api/ask` di server lokal (`SECURITY_SAHABAT_LLM=off`), bukan dikarang. Tiga momen wajib handbook tertutup: **menolak**, **minta klarifikasi**, **menunggu approval**.

| Adegan | Menit | Isi | Hasil nyata |
| --- | --- | --- | --- |
| 1 | 0:00–1:30 | Q-001 port 22 → HR DB | `tidak boleh … [POL-x001]`, kutipan `CTRL-09` / `TOPO-HR-DATA` / `TOPO-SEGMENTS`, flag `POLICY_BLOCK`; `classify_risk()` → **CRITICAL** + 4 alasan berkutipan |
| 2 | 1:30–2:45 | Garuda: Sari vs Falcon lalu Andini | Sari vs Falcon **identik** (`answer=null`, hanya `SOP-14`); Andini baru melihat `RESTRICTED-01` |
| 3 | 2:45–3:45 | Injection Q-006 | `rc=4`, ditolak, pertanyaan tidak diulang |
| 4 | 3:45–4:45 | "Pak Budi" | `CLARIFY` dengan dua nama/peran/lokasi, audit `approval_state=pending` |
| 5 | 4:45–6:00 | Perintah aksi | `ACTION_REQUEST` + `POLICY_BLOCK`, audit `approval_state=blocked`, "tidak ada yang dikirim" |
| 6 | 6:00–7:30 | Penutup | `--replay <q_id>` + `audit_chain --verify` |

Persiapan sebelum rekam: build frontend (`npm ci --ignore-scripts && npm run build`), jalankan `python backend/api/server.py --static frontend/dist` dan buka di side browser WorkBuddy, pilih persona, **kosongkan `backend/logs/audit.jsonl`** agar replay berisi adegan video saja. Di Windows set `PYTHONUTF8=1` dan `PYTHONIOENCODING=utf-8`.

---

## 9. Item 7 — Product sharing

Sumber final: `docs/submission/product-sharing.md` (difinalkan 6 November; memuat transparansi alat dan ringkasan bahasa Inggris).

### Di mana WorkBuddy memberi nilai

| Tahap | Yang dikerjakan WorkBuddy | Bukti |
| --- | --- | --- |
| Dari brief ke dataset | 8 file data mock: 15 kontak (dua "Budi"), 9 persona, 13 aset CMDB, 14 kontrol, 5 SOP dengan dua konflik, topologi, 23 pesan chat dengan injection, 18 pertanyaan uji | catatan memori agen 2026-10-22 |
| Skill hari pertama | Skill Creator memecah 3 dokumen jadi 30 entri KB berkutipan, menulis `SKILL.md` + playbook, langsung menguji Q-001/Q-010/restricted/"tidak tahu" | `workbuddy-provenance.md` |
| Iterasi per fase | Fase 2, 3, 4, lalu karantina context injection — masing-masing dengan matriks regresi dan paket `.skill` | screenshot 47 artifact |
| Fondasi kode | 48 file; **35 masih identik** di repo hari ini | `workbuddy-provenance.md` |
| Satu skill untuk tim | Project skill `.codebuddy/skills/` terbaca otomatis; paket `.skill` bisa diunggah ke Personal Library | `workflow/` |
| Agen yang meminta izin | Mode *Default Permissions* meminta persetujuan sebelum skrip dijalankan | `docs/workbuddy.md` §2 |

### Wawasan utama

1. **Kepatuhan model bukan jaminan keamanan** — semua keputusan izin, risiko, dan approver dipindah ke engine deterministik.
2. **Tes contoh bisa lulus semua dan tetap bocor** — pembungkaman kata kunci lulus 13/13 namun bocor lewat parafrasa Inggris; diganti *non-interference* dan tes relasi (dua masukan, keluaran harus sama).
3. **Panggil skill eksplisit** untuk hal penting; tanpa `/` hanya 2 dari 4 percobaan terpanggil di Hy4.
4. **Bahasa jawaban perlu diminta** di prompt ("Jawab dalam bahasa Indonesia").
5. **Kredit adalah batas desain** — sesi pembangunan berhenti dengan "429 Credits exhausted"; sejak itu artifact rutin diunduh dan disimpan di Git.
6. **Aturan sebagai data** membuat agen bisa dipakai perusahaan lain; pemilik dokumen mengesahkan aturan.

### Masukan untuk WorkBuddy

Ekspor/share tugas (transkrip, artifact, Request ID) · identitas pengguna dari akun/SSO · file skill yang hanya boleh dibaca skrip · pengaturan bahasa per akun/skill · alasan skill tidak terpanggil · node approval di Automation · pemakaian kredit per tugas · konsistensi dokumentasi (`skill.yml` vs `SKILL.md`).

### Transparansi alat

Inti sistem lahir dari tugas Skill Creator WorkBuddy. Setelah kredit habis 27 Oktober, pengembangan lanjutan (Pra-CAB, policy register, UI Svelte, API Python) dikerjakan di repo lokal dan **berjalan dari `source/`, bukan sebagai skill WorkBuddy** — bagian itu tidak diklaim dibuat di WorkBuddy. Demo 6 November kembali ke jalur paling awal: risk dari KB lewat chat/panel WorkBuddy.

### English summary (for the submission form)

WorkBuddy took us from a written brief to a usable skill in one session: Skill Creator generated the mock dataset, the citation-ready knowledge base, and the first four security guards, then tested them in the same task (47 artifacts; 35 of 48 files are still byte-identical in our repository). Our key learning: a permission-aware agent must not rely on model compliance. Keyword-based silence passed 13/13 of its own tests yet still leaked a restricted project through an English paraphrase, so we replaced it with *non-interference* — unreadable documents are skipped before scoring — and enforced permissions, risk, and approvals in deterministic code. The LLM only copies free text into fields and proposes rules that a human document owner must approve. Practical lessons: invoke the skill explicitly for important questions, request the answer language in the prompt, and treat credit limits as a design constraint.

---

## 10. Item 8 — Source code (ekspor WorkBuddy workflow + bukti pemakaian)

| Field | Nilai | Status |
| --- | --- | --- |
| Paket zip | `dist/submission/SecuritySahabat-workbuddy-export.zip` (dirakit dari commit bersih) | ✅ |
| Link unggah | `[ISI: URL Google Drive, akses "siapa pun yang punya link"]` | ⏳ |
| Commit pembentuk | `[ISI: hash commit saat zip dirakit]` / lihat `VERSION.txt` dalam zip | ✅ |
| Repo GitHub | Privat, tidak diunggah | ✅ |

Perintah: `python tools/export_submission.py` (skrip menolak bila ada perubahan belum di-commit; `pack_skill.py` dijalankan otomatis). Isi zip dijelaskan oleh `docs/submission/export-readme.md` yang menjadi `README.md` di dalam paket.

| Folder | Isi |
| --- | --- |
| `workflow/` | `security-sahabat.skill` siap impor + project skill `.codebuddy/skills/security-sahabat/` |
| `evidence/` | Screenshot WorkBuddy, catatan memori agen, `workbuddy-provenance.md` (48 artifact, 35 identik), hasil tes |
| `submission/` | Accountability sheet, deskripsi proyek, product sharing, diagram arsitektur, catatan teknis WorkBuddy |
| `source/` | Seluruh source code repo (`git ls-files`): engine, API, UI Svelte, Pra-CAB, policy register, tes |
| `SHA256SUMS.txt`, `VERSION.txt` | Integritas tiap file dan commit pembentuk |

Cara menjalankan tanpa WorkBuddy: Python 3.10+ tanpa dependensi; `python backend/tests/verify_matrix.py`, `python -m unittest discover -s backend/tests`, `python backend/api/server.py --static frontend/dist --demo`. Cara menjalankan sebagai skill: impor `security-sahabat.skill`, panggil `/security-sahabat`, setujui dialog izin `scripts/search_kb.py`.

> Paket memuat data mock fiktif PT Nusantara Logistik Prima termasuk teks proyek restricted ("Proyek Garuda"). Hanya untuk juri; mohon tidak dipublikasikan ulang.

Batasan yang ditulis apa adanya: WorkBuddy web belum punya ekspor/share tugas sehingga transkrip lengkap tidak bisa diambil; uji skill online dilakukan dari akun anggota tim lain; Pra-CAB dan UI web berjalan dari `source/`, bukan sebagai skill.

---

## 11. Item 9 — Bonus: cover image & project link

| Item | Spesifikasi | Nilai | Status |
| --- | --- | --- | --- |
| Cover image | 16:9, 380×216 px | `[ISI: nama file / URL]` | ➖ |
| Project link live | WorkBuddy Sites; live sejak 7 Nov 2026 | https://securitysahabat.apps.workbuddy.host/?sharecode=V6WLZ2I6QY | ✅ |

Keduanya **opsional / bonus** dan tidak boleh menunda pengisian 8 item wajib. Rujukan: `docs/workbuddy.md` §3.

---

## 12. Lampiran A — Bukti pemakaian WorkBuddy & Request ID

Cara mengisi: jalankan satu sesi `/security-sahabat` di WorkBuddy, lalu menu ⋯ → *Copy Request ID* untuk tiap jawaban. Request ID dapat diverifikasi pihak penyelenggara dan merupakan bukti paling sulit dipalsukan. Simpan screenshot baru di `docs/test-results/workbuddy/` agar ikut ke `evidence/workbuddy-screenshots/` saat zip dirakit ulang.

| # | Tanggal | Pertanyaan / aksi | Request ID | Screenshot | Catatan |
| --- | --- | --- | --- | --- | --- |
| 1 | `[ISI]` | Q-001 Andini: port 22 → db-hr-jkt-01 | `[ISI]` | `[ISI]` | `[ISI]` |
| 2 | `[ISI]` | Sari: owner Proyek Garuda | `[ISI]` | `[ISI]` | Harus identik dengan Falcon |
| 3 | `[ISI]` | Andini: owner Proyek Garuda | `[ISI]` | `[ISI]` | `[ISI]` |
| 4 | `[ISI]` | Dialog izin `scripts/search_kb.py` | `[ISI]` | `[ISI]` | Bukti menunggu persetujuan |
| 5 | `[ISI]` | Q-006 injection | `[ISI]` | `[ISI]` | `[ISI]` |
| 6 | `[ISI]` | `[ISI: pertanyaan tambahan]` | `[ISI]` | `[ISI]` | `[ISI]` |

---

## 13. Lampiran B — Checklist akhir sebelum submit

- [ ] Semua `[ISI: …]` pada Bagian 1 dan 2 terisi.
- [ ] Bagian 0 (cara pakai) dihapus dari salinan yang dibagikan.
- [ ] 8 item wajib handbook tersedia: title + blurb, description, accountability sheet, test results + screenshot, architecture diagram, demo video, product sharing, source code.
- [ ] Video 5–8 menit sudah direkam mengikuti `demo-script.md`; tiga momen (menolak / klarifikasi / menunggu approval) terlihat.
- [ ] Paket zip dirakit ulang **setelah** commit terakhir; `VERSION.txt` cocok dengan `git rev-parse HEAD`.
- [ ] Link Google Drive bisa dibuka dengan akses "siapa pun yang punya link" (uji dari akun lain / incognito).
- [ ] `SHA256SUMS.txt` ada di dalam zip.
- [ ] Kegagalan kasus #7 tetap tercantum, tidak dihapus.
- [ ] Repo GitHub masih **private**.
- [ ] Tidak ada data pribadi nyata di paket (semua nama/NIK/HP adalah data mock).
- [ ] Angka uji konsisten di deskripsi, accountability sheet, diagram, dan dokumen ini.
- [ ] Formulir diisi, bukti konfirmasi disimpan, tanggal & jam dicatat.

| Peran | Nama | Konfirmasi | Tanggal |
| --- | --- | --- | --- |
| Ketua tim / submitter | `[ISI: nama]` | `[ISI: paraf]` | `[ISI]` |
| Backend & engine | Muhammad Izzat | `[ISI: paraf]` | `[ISI]` |
| Frontend & tes UI | Farrez | `[ISI: paraf]` | `[ISI]` |
| Anggota | Wafi | `[ISI: paraf]` | `[ISI]` |

---

## 14. Lampiran C — Keterbatasan yang diakui (jangan dihapus)

- **Kasus #7 gagal:** bukti tidak relevan dikembalikan alih-alih "tidak tahu"; butuh ambang relevansi. 19 dari 20 kasus brief lulus.
- **S1 / S4 LLM belum ada** untuk web app; identitas diparse rule-based, `answer` null sampai ada klarifikasi/verdict dari `ask_bridge.py`. Jalur Claude Skill sudah ada.
- **Belum ada autentikasi/SSO:** persona dipilih dari pemilih demo, bukan identitas akun.
- **Pra-CAB belum punya UI** dan tidak didemokan pada 6 November; keputusan scope: fokus risk dari KB lewat chat WorkBuddy.
- **`npm ci` melaporkan 2 low severity vulnerabilities** (drift dari klaim 0 di ADR 0001 tertanggal 27 Okt); belum ditindaklanjuti.
- **Uji ekstraksi aturan dengan Claude sungguhan** belum dilakukan (membutuhkan `ANTHROPIC_API_KEY`); langkah 13 Pra-CAB diisi manual.
- **WorkBuddy web belum punya ekspor/share tugas** sehingga transkrip lengkap sesi tidak tersedia; bukti berupa screenshot, artifact, catatan memori agen, dan task id.
- **Uji skill online** hanya lima percobaan dari akun anggota tim lain; pemanggilan otomatis belum konsisten di Hy4.

---

## 15. Sumber dokumen (indeks)

| Dokumen | Path | Dipakai untuk |
| --- | --- | --- |
| Checklist submission | `docs/submission/README.md` | Daftar 9 item wajib & status |
| Project description | `docs/submission/project-description.md` | Bagian 4 |
| Accountability sheet | `docs/submission/accountability-sheet.md` | Bagian 5 |
| Hasil tes | `docs/test-results/README.md` | Bagian 6 |
| Diagram & arsitektur | `docs/architecture-diagram.svg`, `docs/architecture.md` | Bagian 7 |
| Naskah demo | `docs/submission/demo-script.md` | Bagian 8 |
| Product sharing | `docs/submission/product-sharing.md` | Bagian 9 |
| README paket ekspor | `docs/submission/export-readme.md` | Bagian 10 |
| Provenance WorkBuddy | `docs/submission/workbuddy-provenance.md` | Bagian 9, 10 |
| Catatan teknis WorkBuddy | `docs/workbuddy.md` | Bagian 9, 11 |
| Adjusted build brief | `adjusted_brief.md` §2, §6, §8, Phase 7 | Acuan seluruh dokumen |
