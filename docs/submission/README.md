# Checklist submission (handbook §7)

Tenggat **1 Nov 2026** lewat formulir di handbook §9. Keputusan 27 Okt (Izzat):
item *Source code* memakai jalur **ekspor workflow WorkBuddy + bukti pemakaian**;
repo GitHub tetap privat.

| Item | Wajib | Status | Lokasi / catatan |
| --- | --- | --- | --- |
| Project title | ya | ✅ | SecuritySahabat |
| Short blurb (< 10 kata) | ya | ✅ | "Tanya boleh atau tidak. Dapat jawaban dengan bukti." (8 kata) |
| Project description | ya | ✅ | [project-description.md](project-description.md) |
| Accountability sheet | ya | ✅ | [accountability-sheet.md](accountability-sheet.md) |
| Test results + screenshot | ya | ⚠️ | Challenge A: [../test-results/README.md](../test-results/README.md) (screenshot per kasus). Pra-CAB: [../test-results/pracab.md](../test-results/pracab.md) baru transkrip terminal; tambahkan screenshot setelah UI Pra-CAB jadi |
| Architecture diagram | ya | ✅ | [../architecture-diagram.svg](../architecture-diagram.svg) + [../architecture.md](../architecture.md) |
| Demo video 5-8 menit | ya | ❌ | Tim. Wajib memperlihatkan menolak / minta klarifikasi / menunggu approval: Garuda Sari vs Andini, injection Q-006, Pra-CAB langkah 3-4. Rekam demo Pra-CAB dari audit log kosong |
| Product sharing | ya | ⚠️ | Draf: [product-sharing.md](product-sharing.md). Tim perlu meninjau catatan di akhir file (bahasa formulir, perlu tidaknya menyebut alat lain, angka uji bila sesi direkam ulang) |
| Source code | ya | ⚠️ | Paket ekspor siap dirakit (di bawah); bukti pemakaian masih bisa diperkuat |
| Cover image 16:9 | tidak | ❌ | 380×216 px |
| Project link | bonus | ❌ | WorkBuddy Sites ([../workbuddy.md](../workbuddy.md) §3), keputusan tim |

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

## Memperkuat bukti pemakaian (perlu dikerjakan di WorkBuddy, memakai kredit)

Bukti yang sudah ada kuat untuk "kode lahir di WorkBuddy" (tugas skill-creator,
47 artifact, provenance). Yang masih lemah adalah "workflow-nya dipakai di
WorkBuddy", karena uji online hanya tiga pertanyaan dan dari akun lain.

1. **Rekam satu sesi** di WorkBuddy dengan `/security-sahabat`: Q-001 (Andini),
   Proyek Garuda oleh Sari, lalu oleh Andini. Tambahkan "Jawab dalam bahasa
   Indonesia". Rekaman ini sekaligus bahan demo video.
2. **Tangkap dialog izin** saat WorkBuddy meminta menjalankan
   `scripts/search_kb.py` (bukti "menunggu persetujuan sebelum bertindak").
3. **Kumpulkan Request ID** tiap jawaban (menu ⋯ → *Copy Request ID*) ke
   `docs/test-results/workbuddy/request-ids.md`. Tencent bisa memverifikasinya
   di sisi mereka; ini bukti paling sulit dipalsukan.
4. Simpan screenshot-nya di `docs/test-results/workbuddy/`, commit, lalu rakit
   ulang zip. Folder itu otomatis ikut ke `evidence/workbuddy-screenshots/`.

Batasan yang ditulis apa adanya di paket: WorkBuddy web belum punya fitur
ekspor/share tugas (dicek 27 Okt), jadi transkrip lengkap tidak bisa diambil;
Pra-CAB dan UI web berjalan dari `source/`, bukan sebagai skill.
