# Checklist submission (handbook §7)

Tenggat tertulis **1 Nov 2026** lewat formulir di handbook §9; Demo Day
**27 Nov 2026**. Keputusan 27 Okt (Izzat): item *Source code* memakai jalur
**ekspor workflow WorkBuddy + bukti pemakaian**; repo GitHub tetap privat.

Keputusan 6 Nov (hari terakhir): **demo video dikerjakan paling akhir**. Semua
dokumen lain diselesaikan dulu dan dikonsolidasikan ke satu
[dokumen template .docx](SecuritySahabat-Submission-Template.docx) berisi
seluruh isian formulir; bagian yang memang harus diisi tim (link, Request ID,
tanggal) ditandai `[ISI: …]` di dalamnya.

| Item | Wajib | Status | Lokasi / catatan |
| --- | --- | --- | --- |
| Project title | ya | ✅ | SecuritySahabat |
| Short blurb (< 10 kata) | ya | ✅ | "Tanya boleh atau tidak. Dapat jawaban dengan bukti." (8 kata) |
| Project description | ya | ✅ | [project-description.md](project-description.md) |
| Accountability sheet | ya | ✅ | [accountability-sheet.md](accountability-sheet.md) |
| Test results + screenshot | ya | ✅ | Challenge A: [../test-results/README.md](../test-results/README.md) — 23 lulus / 1 gagal (#7) dengan screenshot per kasus; kegagalan ditulis apa adanya. Pra-CAB: [../test-results/pracab.md](../test-results/pracab.md) + [pracab-demo.txt](../test-results/pracab-demo.txt) (transkrip terminal). Screenshot UI Pra-CAB tidak dibuat karena alur CAB di luar scope demo 6 Nov |
| Architecture diagram | ya | ✅ | [../architecture-diagram.svg](../architecture-diagram.svg) + [../architecture.md](../architecture.md); footer angka uji diselaraskan 6 Nov |
| Demo video 5-8 menit | ya | ⚠️ | **Dikerjakan paling akhir** sesuai keputusan 6 Nov. Naskah siap rekam: [demo-script.md](demo-script.md) — 6 adegan, output diverifikasi dari run sungguhan, mencakup menolak / minta klarifikasi / menunggu approval. Link video diisi di template |
| Product sharing | ya | ✅ | Final 6 Nov: [product-sharing.md](product-sharing.md). Tiga catatan draf diputuskan (angka uji 27 Okt tetap, transparansi alat ditambahkan, ringkasan bahasa Inggris untuk formulir tersedia) |
| Source code | ya | ✅ | Paket ekspor dirakit dari commit bersih (di bawah); link Google Drive diisi di template |
| Template dokumen terpadu (.docx) | bantu | ✅ | [SecuritySahabat-Submission-Template.docx](SecuritySahabat-Submission-Template.docx) — semua item di atas dalam satu dokumen, dengan `[ISI: …]` untuk field tim. Sumber Markdown: [SecuritySahabat-Submission-Template.md](SecuritySahabat-Submission-Template.md) |
| Cover image 16:9 | tidak | ❌ | 380×216 px; opsional, placeholder tersedia di template |
| Project link | bonus | ❌ | WorkBuddy Sites ([../workbuddy.md](../workbuddy.md) §3), keputusan tim; placeholder tersedia di template |

## Source code: paket ekspor WorkBuddy

```bash
python tools/export_submission.py
```

Menghasilkan `dist/submission/SecuritySahabat-workbuddy-export.zip` dari commit
terakhir (skrip menolak bila ada perubahan yang belum di-commit). Isi dan cara
pakainya: [export-readme.md](export-readme.md), yang menjadi `README.md` di
dalam zip. Ringkasnya:

- `workflow/` — skill WorkBuddy siap impor + project skill `.codebuddy`.
- `evidence/` — screenshot WorkBuddy, catatan memori agen WorkBuddy,
  [workbuddy-provenance.md](workbuddy-provenance.md) (48 artifact tugas
  skill-creator → file repo dengan hash, 35 masih identik), hasil tes.
- `submission/` — dokumen di tabel atas.
- `source/` — seluruh source code repo (`git ls-files`).
- `SHA256SUMS.txt`, `VERSION.txt` (commit).

Unggah zip ke Google Drive dengan akses "siapa pun yang punya link" (bukan
publik di pencarian) dan tempel link-nya di formulir. Zip memuat teks mock
Proyek Garuda; itu data fiktif dari dataset kita sendiri.

## Isian yang masih menjadi pekerjaan tim

Bukti yang sudah ada kuat untuk "kode lahir di WorkBuddy" (tugas skill-creator,
47 artifact, provenance). Yang masih lemah adalah "workflow-nya dipakai di
WorkBuddy", karena uji online hanya tiga pertanyaan dan dari akun lain. Empat
item di bawah **tidak bisa diisi dari repo** — semuanya sudah disediakan sebagai
tabel isian di Lampiran A template .docx, dan tidak perlu membuat file baru:

1. **Rekam satu sesi** di WorkBuddy dengan `/security-sahabat`: Q-001 (Andini),
   Proyek Garuda oleh Sari, lalu oleh Andini. Tambahkan "Jawab dalam bahasa
   Indonesia". Rekaman ini sekaligus bahan demo video (dikerjakan terakhir).
2. **Tangkap dialog izin** saat WorkBuddy meminta menjalankan
   `scripts/search_kb.py` (bukti "menunggu persetujuan sebelum bertindak").
3. **Catat Request ID** tiap jawaban (menu ⋯ → *Copy Request ID*) ke tabel
   Lampiran A. Tencent bisa memverifikasinya di sisi mereka; ini bukti paling
   sulit dipalsukan.
4. Simpan screenshot baru di `docs/test-results/workbuddy/`, commit, lalu rakit
   ulang zip. Folder itu otomatis ikut ke `evidence/workbuddy-screenshots/`.

Selain itu, field yang hanya tim yang tahu: link video demo, link Google Drive
paket zip, tanggal & jam submit, nama lengkap/email anggota, dan — bila jadi
dibuat — cover image serta link WorkBuddy Sites. Semua ada di bagian
"Daftar isian" pada template.

Batasan yang ditulis apa adanya di paket: WorkBuddy web belum punya fitur
ekspor/share tugas (dicek 27 Okt), jadi transkrip lengkap tidak bisa diambil;
Pra-CAB dan UI web berjalan dari `source/`, bukan sebagai skill.
