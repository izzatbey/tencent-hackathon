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
| Lainnya (kelengkapan, risiko, approver SOP-14, jendela waktu, memo SOP-7, emergency, SoD) | kode | tetap kode ("built-in"), dimigrasi bertahap |

Semua tes Pra-CAB lama lulus tanpa diubah setelah migrasi.

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
