# Hasil tes Pra-CAB

Pelengkap [README.md](README.md) (matriks tanya-jawab brief). Bukti mentah:
[pracab-demo.txt](pracab-demo.txt), transkrip `python tools/demo_pracab.py`
terhadap build produksi + API asli, 27 Okt 2026, **log audit kosong** di awal.

Ringkasan: 16/16 langkah sesuai harapan; rantai hash 21 event `ok: true`.
Tidak ada LLM yang dipakai (`SECURITY_SAHABAT_LLM=off`).

| # | Skenario | Harapan | Hasil | Unit test pendamping |
| --- | --- | --- | --- | --- |
| 1 | Ragil membuat CR upgrade firmware fw-edge-mks-01 | `draft`, tombol hanya milik pemohon | Lulus | `test_alur_lengkap_sampai_dispatch_dan_undo` |
| 2 | Ragil mengajukan → precheck SOP-14 | READY, risiko HIGH, semua cek berkutipan + `basis`; konflik SOP-7 vs memo 1 Okt ditandai WARN | Lulus | `test_firmware_cabang_siap_ke_cab` |
| 3 | Dispatch sebelum disetujui | Ditolak 409 `not_approved`, tidak ada tool berjalan | Lulus | `test_diblokir_tidak_bisa_disetujui` |
| 4 | Indah mencatat keputusan CAB sebelum rapat | Ditolak 409 `meeting_not_held` | Lulus | `test_jam_demo_memungkinkan_rapat_cab` |
| 5 | Jam demo maju ke setelah rapat Rabu | Tombol approve muncul untuk Indah | Lulus | `test_jam_demo_memungkinkan_rapat_cab` |
| 6 | Indah mengisi slot CAB + HR Manager | `approved` | Lulus | `test_hanya_assignee_yang_boleh_menyetujui` |
| 7 | Dispatch | 3 mock tool "would_have_sent"; konflik data Hendra Wijaya (SOP-7 vs direktori) ditampilkan | Lulus | `test_alur_lengkap_sampai_dispatch_dan_undo` |
| 8 | Undo dalam 60 detik | `undone` | Lulus | `test_undo_lewat_60_detik_ditolak` |
| 9 | Riwayat dari audit log | 8 event berurutan dengan hash | Lulus | `test_replay_dari_log_memulihkan_state` |
| 10 | Andini minta SSH dari internet ke db-hr-jkt-01 | BLOCKED, CRITICAL | Lulus | `test_ssh_internet_ke_db_hr_diblokir` |
| 11 | Akses app-erp-prod untuk Lina (Marketing) | BLOCKED, `basis: sop`, kutipan sel CMDB | Lulus | `test_akses_departemen_tidak_diizinkan_diblokir` |
| 12 | Akses mail-jkt-01 (tanpa policy perusahaan) | READY + WARN `basis: standar`, owner aset jadi approver | Lulus | `test_aset_tanpa_policy_internal_dinilai_dengan_standar` |
| 13 | Andini mengusulkan aturan dari memo Citra | `draft`, Andini tidak punya tombol sahkan | Lulus | `test_dari_memo_sampai_keputusan_berubah` |
| 14 | Yang tidak berhak mengesahkan, lalu Citra | 403 `not_owner`, 403 `self_approval`, lalu `active` | Lulus | `test_dari_memo_sampai_keputusan_berubah` |
| 15 | Lina mengajukan mail-jkt-01 lagi | BLOCKED oleh aturan baru; CR langkah 12 tetap READY | Lulus | `test_precheck_mencatat_aturan_dan_hash` |
| 16 | Verifikasi rantai hash | `ok: true`, tidak ada baris lama/rusak | Lulus | `AuditChainTest` (5 tes, termasuk ubah/hapus baris) |

## Catatan

- **Demo tidak idempoten.** Aturan yang disahkan di langkah 14 tersimpan di
  audit log. Bila demo dijalankan lagi terhadap log yang sama, langkah 12
  langsung BLOCKED karena aturannya sudah aktif. Untuk rekaman video atau bukti,
  mulai dari log kosong: hentikan server, pindahkan `backend/logs/audit.jsonl`,
  jalankan server lagi.
- Ekstraksi aturan dengan LLM (`--llm`) belum diuji dengan Claude sungguhan;
  langkah 13 di sini diisi manual.
