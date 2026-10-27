# Tes SecuritySahabat

Empat lapis, dari yang paling murah:

| Suite | Perintah | Isi |
| --- | --- | --- |
| Regresi CLI | `python backend/tests/verify_matrix.py` | 44 kasus lama (wajib 0 gagal) |
| Core + API | `python -m unittest discover -s backend/tests -v` | `test_accountability.py` (5 aturan, edge case), `test_api.py` (DTO, log, validasi, HTTP) |
| Komponen UI | `cd frontend && npm test` | Vitest + Testing Library, jsdom |
| End-to-end | `cd frontend && npm run e2e` | Playwright, build produksi + API Python asli, desktop dan Pixel 7, axe WCAG 2.2 AA |

Di Windows set `PYTHONUTF8=1` dan `PYTHONIOENCODING=utf-8` dulu. E2E butuh
`npx playwright install chromium` sekali.

## Rancangan

| Bagian | Isi |
| --- | --- |
| Kontrak | Pertanyaan + persona masuk, keluar jawaban berkutipan verbatim hanya dari dokumen yang boleh dilihat penanya, "tidak tahu" bila tak ada bukti, setiap pertanyaan tercatat. |
| Risiko terbesar | Existence leak topik restricted (pelanggaran kritis handbook), field internal bocor ke browser, PII di layar atau log. |
| Teknik | Partisi per status (OK, NO_MATCH, RESTRICTED, INJECTION), tabel keputusan persona x proyek, nilai batas panjang pertanyaan (0, 1, 2000, 2001), transisi status izin (cabut, beri, cabut), skenario demo end-to-end, tebak galat dari probe. |
| Edge case dari katalog | Unicode zero-width dan fullwidth, soft hyphen, emoji, RTL, NUL; NIK/HP berspasi, bertitik, bertanda hubung, +62; tanggal mustahil (31 Februari); klik ganda; IME Enter; timeout 30 detik; koneksi putus; 500 non-JSON; path traversal; body raksasa; permintaan bersamaan; XSS di kutipan. |
| Oracle | Teks dokumen di disk (kutipan harus substring verbatim), pasangan proyek nyata vs fiktif (relasi metamorfik: hasil harus identik), konstanta tertulis untuk masking dan tanggal. |
| Kualitas tes | Setiap tambalan dan pengaman dirusak sementara (normalisasi Unicode, regex NIK, pemetaan status, penyaring field, traversal, teks mentah saat menunggu, `{@html}`, pencegah klik ganda); semua tes terkait merah, lalu dikembalikan. |
| Tidak bisa dites di sini | Agent WorkBuddy, voice note, answer composer LLM (S4), approval gate (S5), klarifikasi dua Budi: belum dibangun. |

## Status terhadap test matrix brief (§6)

Kolom "Lapis" menyebut di mana kasus itu diuji otomatis.

| # | Kasus | Status | Lapis |
| --- | --- | --- | --- |
| 1 | Q-001 port 22 ke HR DB | Lulus (kutipan CTRL-09; kesimpulan "tidak boleh" menunggu S4) | core, API, e2e |
| 2 | Q-002 firmware Makassar | Belum dites (butuh S4 untuk saran jendela waktu) | - |
| 3 | Garuda oleh persona berwenang | Lulus | core, API, e2e |
| 4 | Garuda oleh Sari | Lulus untuk "Siapa owner Proyek Garuda?"; **gagal** untuk "Project Garuda" dan nama proyek yang ditempel ke pertanyaan sah (ADR 0002) | core, API, e2e |
| 5 | Izin berubah lalu tanya ulang | Lulus | core |
| 6 | Konflik SOP-7 | Sebagian: flag REVIEW muncul; memo Oktober ada di chat export yang belum di-index | core, API, e2e |
| 7 | SLA crane Jayapura | **Gagal**: retrieval mengembalikan bukti tak relevan, bukan "tidak tahu" | core (expectedFailure) |
| 8 | Injection Q-006 | Lulus, termasuk varian Unicode setelah tambalan | core, API, e2e |
| 9 | Dua Budi | Belum dibangun | - |
| 10 | Jumat siang WIB/WITA | Belum dibangun | - |
| 11 | Transkrip voice note | Belum dites | - |
| 12 | NIK/HP di pertanyaan dan log | Lulus setelah tambalan format berspasi/bertanda hubung | core, API, e2e |
| 13 | Campur bahasa | Lulus di retrieval | core |
| 14 | "server yang itu" | Belum dibangun | - |
| 15 | Konflik berbeda tanggal | Lulus (dokumen sintetis Rp500.000 vs Rp750.000) | core |
| 16 | Bukti tipis/tidak ada | Lulus | core, API, UI, e2e |
| 17 | Replay dari audit log | Sebagian: setiap pertanyaan tercatat dengan `q_id`, belum ada perintah replay | API |
| 18 | Aksi tanpa approval | Belum dibangun (S5) | - |
| 19 | Approve lalu undo | Belum dibangun (S5) | - |
| 20 | Dokumen baru, jawaban berubah | Lulus | core |

Kegagalan ditulis sebagai `@unittest.expectedFailure` dengan alasan di
docstring, supaya suite tetap hijau tapi kegagalannya tidak hilang dari laporan.
Begitu diperbaiki, Python melaporkan "unexpected success" dan dekoratornya harus
dicabut.
