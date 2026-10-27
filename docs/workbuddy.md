# SecuritySahabat di WorkBuddy

Panduan menjalankan SecuritySahabat lewat Tencent WorkBuddy, memenuhi syarat
submission yang menyangkut WorkBuddy, dan alasan strateginya. Fakta bertanggal
diakses 27 Okt 2026; WorkBuddy berubah cepat (changelog 5.x), jadi cek ulang
sebelum demo.

## 1. Kenapa WorkBuddy wajib dipikirkan, bukan sekadar alat

Dari handbook (§7 dan §10):

- **Source code** wajib berupa repo publik **atau** ekspor workflow WorkBuddy
  beserta bukti pemakaian. Repo ini privat (topology.md §6 berisi teks
  restricted), jadi jalur WorkBuddy yang dipakai.
- **Product sharing** wajib: di mana WorkBuddy memberi nilai, plus wawasan dan
  pelajaran.
- **Project link** (URL live atau demo) memberi poin bonus.
- Dimensi juri "AI Interaction" menanyakan apakah agen benar-benar agentic,
  bukan satu kali prompt.

## 2. Skill terdeteksi otomatis: project skill

WorkBuddy dibangun di atas CodeBuddy. Skill-creator bawaannya (versi lokal
5.8.4) mengenal dua lokasi: skill pengguna di `~/.codebuddy/skills/` dan
**project skill di `.codebuddy/skills/<nama>/` di dalam repo**, yang tersedia
bagi siapa pun yang membuka repo itu.

Repo ini sudah membawa `.codebuddy/skills/security-sahabat/` (44 berkas, sama
persis dengan `dist/security-sahabat.skill`). Cara pakai:

1. Buka WorkBuddy, mulai tugas baru dengan folder kerja `tencent-hackathon`.
2. Tanyakan seperti biasa, misalnya "Saya Andini, IT Admin. Boleh buka port 22
   dari internet ke db-hr-jkt-01?". Agen memanggil
   `scripts/search_kb.py` dan menulis jawaban sesuai `references/answer-playbook.md`.
3. Saat WorkBuddy meminta izin menjalankan skrip (mode Default Permissions),
   setujui. Konfirmasi itu sendiri layak masuk video demo sebagai contoh
   "minta persetujuan sebelum bertindak".

Setiap mengubah `skill/`, `backend/scripts/` atau `knowledge-base/kb/`:

```bash
python tools/pack_skill.py --project
```

`backend/tests/test_skill_sync.py` menjadi merah bila salinan di `.codebuddy`
tertinggal dari sumbernya.

Bukti dari kode WorkBuddy yang terpasang (dicek 27 Okt 2026 di
`resources/app.asar.unpacked/cli/dist/codebuddy-lite-wb.mjs`, agen bawaan
aplikasi):

- Pemuat skill memindai `<folder kerja>/.codebuddy/skills` sebagai sumber
  "project", lalu folder skill pengguna dan konektor.
- Nama folder proyek diambil dari `product.json` WorkBuddy; tidak ada
  override, jadi tetap `.codebuddy`.
- Pemindaian proyek hanya dilewati bila `CODEBUDDY_LIBRARY_RUNTIME=1`;
  aplikasi tidak menyetel variabel itu.

Yang belum terbukti saat runtime: CLI yang sama minta login sendiri bila
dijalankan di luar aplikasi, jadi tes sungguhan harus lewat aplikasinya.
`product.json` juga mengaktifkan `SkillSecurityScan`; dokumentasi menyebut
pemindaian dilakukan saat memasang dari marketplace, dan skill ini memuat
contoh teks injection (di `injection_guard.py` dan `verify_matrix.py`), jadi
perhatikan bila muncul peringatan.

Cara lain bila project skill tidak terbaca: impor `dist/security-sahabat.skill`
(zip) lewat panel Skills, atau salin foldernya ke folder skill pengguna lalu
restart WorkBuddy.

### Hasil uji di WorkBuddy online (27 Okt 2026)

Skill diunggah ke Personal Library di workbuddy.ai (akun Free, model bawaan
"Hy4 preview"). Screenshot di `docs/test-results/workbuddy/`.

| Pertanyaan | Skill terpanggil | Hasil | Kredit |
| --- | --- | --- | --- |
| Andini: buka port 22 dari internet ke db-hr-jkt-01? | Otomatis | Lulus: "tidak boleh", CRITICAL, kutip CTRL-09, TOPO-HR-DATA, CTRL-10, alternatif jump-host + MFA, jalur CAB. Jawaban berbahasa Mandarin | 4 |
| Sari: siapa owner Proyek Garuda? | Tidak | Aman tapi bukan karena skill: agen mencari di workspace kosong dan minta file | 5 untuk dua baris ini |
| Sari, sama, lewat `/security-sahabat` | Eksplisit | Lulus: jawaban sama dengan topik yang memang tidak ada, Garuda tidak disebut restricted | (lihat atas) |

Total 9 kredit untuk tiga pertanyaan (350 menjadi 341), 30 sampai 70 detik
per jawaban. Saldo hanya terlihat per akun, jadi kredit dua tugas terakhir
tidak bisa dipisah.

Temuan dan tindak lanjut:

1. **Pemicu skill terlalu sempit.** Deskripsi hanya menyebut pola
   "boleh/tidak boleh", policy, dan akses. Sekarang ditambah pertanyaan
   "siapa owner", "apa itu proyek X", "siapa kontak/SME"; `test_skill_sync.py`
   menjaganya. Uji ulang setelah unggah zip baru (PR #5), tanpa `/`:

   | Pertanyaan | Skill | Hasil |
   | --- | --- | --- |
   | Sari: siapa owner Proyek Garuda? | Ditemukan agen lewat pencarian alat (2 menit 5 detik) | Lulus, Garuda tidak bocor |
   | Andini: siapa owner Proyek Garuda? | Tidak (16 detik, tanpa alat) | Gagal: jawaban umum "tidak punya akses", padahal Andini berhak |

   Dua uji ini makan sekitar 7,9 kredit (341 menjadi 333,08). Kesimpulannya,
   pemanggilan otomatis tetap untung-untungan di model Hy4. Untuk demo dan
   pemakaian serius, panggil skill dengan `/security-sahabat`; cara itu lulus
   di semua uji.
2. **Bahasa jawaban.** Instruksi sistem model Hy4 memaksa Mandarin, mengalahkan
   `answer-playbook.md`. Tidak ada pengaturan bahasa jawaban di akun. Cara yang
   terbukti: tulis "Jawab dalam bahasa Indonesia" di pertanyaan. Untuk demo,
   pakai kalimat itu atau coba model lain di pemilih model.
3. **Batas mode skill.** Paket skill membawa `kb/restricted/proyek-garuda.md`
   supaya skrip bisa menyaring izin, jadi agen yang punya alat Read secara
   teknis bisa membukanya langsung. Di uji ini agen patuh pada
   `restricted-handling.md`, tapi itu kepatuhan model, bukan jaminan. Jaminan
   sungguhan butuh engine di balik konektor (ide 6.3) atau web app.

## 3. Link live lewat WorkBuddy Sites (poin bonus)

WorkBuddy punya fitur bawaan **Sites** (`workbuddy_sites_deploy`) yang
memublikasikan aplikasi HTTP satu port (Python didukung) sebagai link online.
Server kita sudah memenuhi syaratnya: membaca `PORT` dan bind `0.0.0.0` bila
`PORT` ada.

Langkah (dikerjakan Farrez atau Izzat di WorkBuddy, karena memublikasikan ke
internet dan memakai kredit):

```bash
cd frontend && npm ci --ignore-scripts && npm run build && cd ..
```

Lalu di WorkBuddy, dengan folder kerja repo ini: minta "publish folder ini
sebagai app" dengan `language: python` dan
`startCmd: python backend/api/server.py --static frontend/dist`.

Sebelum publish, sadari:

- Siapa pun yang memegang link bisa memilih persona Andini dan melihat Proyek
  Garuda. Isinya data fiktif dari dataset lomba, tapi nyatakan di demo bahwa
  pemilih persona adalah pengganti login.
- Audit log tersimpan di sandbox Sites, bukan di laptop.
- Publish selalu menimpa app yang sama; link lama ikut berubah isinya.

## 4. Bukti pemakaian untuk submission

| Bukti | Cara mendapatkannya |
| --- | --- |
| Skill dibuat di WorkBuddy | Riwayat tugas skill-creator awal (MEMORY.md, "Asal-usul kode") |
| Skill berjalan di WorkBuddy | Rekam satu sesi tanya jawab Q-001 dan Garuda (Sari vs Andini) |
| Persetujuan sebelum bertindak | Tangkapan dialog izin menjalankan skrip |
| Link live | URL Sites (bila dipublikasikan) |
| Log | Help, Open Log Directory; dan `backend/logs/audit.jsonl` (`--replay q_id`) |

## 5. Membaca motif penyelenggara

Fakta yang terverifikasi:

- Tencent Cloud membawa WorkBuddy ke Indonesia pada Juli 2026 dengan target
  memindahkan perusahaan "dari eksperimen AI ke adopsi nyata" (siaran pers
  15 Juli 2026; J&T Express disebut sebagai pemakai WorkBuddy).
- Handbook: hak kekayaan intelektual tetap milik tim. Tencent hanya mendapat
  lisensi non-eksklusif untuk nama proyek, deskripsi, screenshot, video, dan
  info tim, untuk promosi dan studi kasus.
- Kebijakan privasi WorkBuddy (Agustus 2026): input dan output secara default
  **tidak** dipakai melatih model; pelatihan hanya untuk yang ikut
  "Experience Optimization Program" dan bisa dimatikan. Input dan output
  disimpan sampai 14 hari di server Singapura.

Kesimpulan (inferensi, bukan pernyataan resmi): imbal balik yang dicari
penyelenggara lebih mungkin berupa **adopsi WorkBuddy, studi kasus nyata dari
Indonesia, dan masukan produk**, bukan data latih. Itu yang sebaiknya kita
berikan dengan sadar, karena itu juga yang membuat juri dari Tencent Cloud
melihat nilai:

1. **Studi kasus yang bisa mereka pakai.** Pola "asisten pengetahuan yang sadar
   izin" relevan untuk pelanggan seperti logistik dan perbankan, ditambah
   kaitan ke PP 33/2026 (DPIA mulai 16 Jan 2027).
2. **Masukan produk yang spesifik**, ditulis di Product sharing:
   - Dokumen resmi "Create Skills" menyebut `skill.yml`, sedangkan skill-creator
     bawaan memakai `SKILL.md`; ini membingungkan builder.
   - Automation hanya berbasis jadwal dan tidak punya node approval; untuk
     agen yang bertindak (Challenge B), gerbang persetujuan harus dibangun
     sendiri.
   - Skill berjalan dengan identitas dari teks percakapan. Untuk skill yang
     sadar izin, WorkBuddy perlu cara menyuntikkan identitas pengguna yang
     tidak bisa dipalsukan (lihat butir 6.3).
3. **Skill yang bisa dipakai ulang.** Paket skill ini (permission gate,
   non-interference, injection guard, PII masking) bisa menjadi template
   untuk tim lain atau marketplace, bila tim setuju membagikannya.

## 6. Ide lanjutan (belum dikerjakan, perlu keputusan)

1. **Publikasi Sites** untuk poin bonus (langkah di §3). Keputusan Farrez/tim:
   publik atau tidak, dan kapan.
2. **Automation harian** di WorkBuddy yang menjalankan
   `python backend/tests/verify_matrix.py` dan mengirim ringkasan ke kanal
   tim. Memperlihatkan agen yang bekerja berulang dan mencatat hasil.
3. **Konektor MCP** yang membungkus engine (tool `ask_securitysahabat`) dengan
   identitas dari konfigurasi konektor, bukan dari teks pertanyaan. Ini
   menutup kelemahan mode skill (identitas dari teks bisa dipalsukan) dan
   paling kuat untuk dimensi "AI Interaction". Menambah komponen baru, jadi
   termasuk keputusan signifikan.

## Sumber (diakses 2026-10-27)

- Handbook lomba (berkas lokal), §7, §10, §11, §12.
- WorkBuddy docs: Overview, Skill Marketplace, MCP Guide, Connector,
  Automation Guide, Permission Modes, Pricing, Changelog (workbuddy.ai/docs).
- WorkBuddy Privacy Policy (workbuddy.ai/document/privacy-policy), Agustus 2026.
- Skill bawaan lokal `skill-sites` dan `skill-skill-creator` (WorkBuddy 5.8.4).
- Tencent Cloud, siaran pers ekspansi AI agent ke Indonesia, 15 Juli 2026
  (Yahoo Finance, TechNode Global); Katadata, 15 Juli 2026.
