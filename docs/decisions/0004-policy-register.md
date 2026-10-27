# 0004: Policy register — aturan perusahaan sebagai data

- Date: 2026-10-27
- Status: Accepted (decided by: Izzat)

## Context

Pra-CAB (ADR 0003) memutus boleh/tidak dengan aturan yang ditulis sebagai
kode di `cab_rules.py`. Untuk satu perusahaan fiktif itu cukup, tetapi visi
produknya ([vision-v2.md](../vision-v2.md)) adalah "CAB decision brain" yang
bisa diisi kebijakan perusahaan mana pun. Selama aturan berupa kode, setiap
kebijakan baru berarti perubahan kode, dan tidak ada jejak siapa yang
mengesahkan aturan itu.

## Decision

1. **Aturan = data** dalam skema kecil: `subject` (aset/zona/site/tipe),
   `action`, `condition` (AND), `effect` (`BLOCK`/`WARN`/`REQUIRE_APPROVER`),
   `sources` berkutipan, `owner`, `effective_date`, `tier`.
2. **Dua tingkat.** `tier: perusahaan` menutup `tier: standar` untuk topik dan
   aset yang sama. Tanpa aturan perusahaan, standar global (ISO/NIST lewat
   `CTRL-xx`) yang dipakai, dan cek diberi `basis: standar`.
3. **Register = seed + log.** `kb/_policies.json` memuat aturan yang
   dimigrasi dari kode (`origin: seed`, dianggap sudah disahkan saat
   migrasi). Semua perubahan berikutnya (`proposed`, `approved`, `rejected`,
   `retired`, `denied`, dokumen sumber) adalah event `policy.*` di audit
   chain yang sama dengan Pra-CAB; register dibangun ulang dari log.
4. **LLM mengusulkan, manusia mengesahkan, kode menerapkan.** Usulan
   (manual atau `/api/policies/extract`) masuk sebagai `draft`. Hanya
   **pemilik dokumen sumber** yang bisa mengesahkan, dan bukan pengusulnya.
5. **Bukti diverifikasi di tiga titik:** saat diusulkan, saat disahkan, dan
   setiap kali aturan dipakai precheck. Sumber yang hilang → aturan tidak
   dipakai dan precheck menampilkan `WARN`.
6. **Keputusan terikat ke isi aturan.** Precheck menyimpan `policies[]`
   (id + hash isi aturan). Aturan yang disahkan berlaku untuk pengajuan
   berikutnya; CR yang sudah diajukan tidak berubah.
7. **Dokumen berinstruksi ke AI ditolak** dan tidak dikirim ke LLM; PII di
   dokumen sumber disamarkan sebelum disimpan.

## Migrasi

| Cek | Sebelum | Sesudah |
| --- | --- | --- |
| `ACCESS-SCOPE` | kode membaca kolom `allowed_departments` CMDB | 12 aturan per aset (kutipan sel CMDB + CTRL-02) + 1 aturan standar `POL-g001` |
| `EXPOSURE` | kode + `SENSITIVE_ZONES` | 3 aturan per segmen (kutipan TOPO-SEGMENTS + CTRL-09) |
| `FRIDAY-PRAYER` (fase 2b, 27 Okt) | kode + `PRAYER` | 2 aturan per site (`POL-w001`, `POL-w002`) dengan kondisi baru `schedule_overlaps`; kutipan TOPO-PRAYER-TIMES |
| `BRANCH-FW-MEMO` (fase 2b, 27 Okt) | kode + kunci `memo.*` | 1 aturan `POL-m001` (subjek firewall Makassar, berlaku 1 Okt 2026) dengan approver baru `cab_meeting` dan `approver_sources` |
| Lainnya (kelengkapan, risiko, approver SOP-14, jendela WMS & firewall cabang, emergency, SoD) | kode | tetap kode ("built-in"), dimigrasi bertahap |

Semua tes Pra-CAB lama lulus tanpa diubah setelah migrasi ACCESS-SCOPE dan
EXPOSURE. Untuk FRIDAY-PRAYER, kesetaraan dibuktikan dengan membandingkan
`precheck` lengkap untuk 408 kombinasi aset × jadwal × jenis CR sebelum dan
sesudah migrasi: identik, kecuali `rule_id` dan `policies[]` yang memang
bertambah. Dua tes yang mendaftar isi register ikut diperbarui (daftar topik
seed; aturan yang dievaluasi untuk aset Jakarta).

Untuk BRANCH-FW-MEMO matriksnya diperlebar menjadi 1.020 kombinasi (ditambah
firmware upgrade dan emergency, supaya slot CAB dari risiko HIGH, dari memo
pada risiko MEDIUM, dan emergency tanpa CAB ikut teruji): identik, termasuk
urutan kutipan di slot CAB. Tiga perubahan yang disengaja:

- Subjek `{asset_type: Firewall, site: Makassar}` menggantikan "Firewall dan
  bukan Jakarta"; sama untuk CMDB sekarang. Firewall cabang baru butuh aturan
  sendiri.
- Aturan berlaku sejak 1 Okt 2026 (tanggal memo); pengajuan bertanggal lebih
  awal kembali ke SOP-7. Kode lama menerapkan memo tanpa melihat tanggal.
- Bila kutipan memo hilang, kode lama turun ke peringatan MFA dari CMDB saja.
  Sekarang berlaku aturan umum register: aturan tidak dipakai, `WARN` agar
  owner meninjau, dan tidak ada slot CAB tambahan.

Kondisi `schedule_overlaps` dievaluasi per aset dalam waktu lokal site-nya;
engine menyaring pesan yang identik, jadi aturan per site/zona tidak
mengulang peringatan untuk setiap aset di site yang sama.

## Konsekuensi

- Seed bernama `_policies.json` karena `search_kb` mengindeks semua `.json`
  di `kb/`; awalan `_` dilewati loader.
- Aturan seed yang owner-nya bukan persona demo (mis. Fajar Ramadhan untuk
  `core-sw-jkt-01`) belum bisa dipensiunkan lewat aplikasi.
- Engine v0 hanya mengerti dua jenis aturan untuk ekstraksi LLM
  (`access_scope`, `internet_exposure`). Jenis lain dikembalikan sebagai
  catatan untuk owner, bukan dipaksakan.
- Semua persona bisa membaca register. Aturan tentang aset restricted
  belum ada; bila nanti ada, register perlu ikut permission gate.
- Ekstraksi LLM sudah diuji dengan `FakeProvider`, belum dengan Claude
  sungguhan.

## Revisit when

- Upload dokumen utuh (chunking + metadata) dibangun: dokumen `submitted`
  menjadi dokumen KB biasa.
- Cek built-in berikutnya dimigrasi: perluas `condition` dan `effect`.
- Ada login: `owner` dan pengesah diambil dari identitas sesi.
