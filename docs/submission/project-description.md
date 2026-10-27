# SecuritySahabat — Project Description

**"Tanya boleh atau tidak. Dapat jawaban dengan bukti."**

Tencent Cloud Hackathon Indonesia 2026 · Challenge A — The Workplace Brain

## Overview

SecuritySahabat adalah "otak kepatuhan" untuk perusahaan Indonesia. Karyawan
bisa **bertanya** apakah suatu tindakan boleh dilakukan, atau **mengajukan
change request / permintaan akses**. Sistem menjawab dari knowledge base
perusahaan sendiri — SOP, kontrol ISO 27001 ↔ NIST CSF, topologi jaringan,
CMDB — dengan kutipan verbatim untuk setiap klaim, hanya dari dokumen yang
boleh dilihat penanya, dan menahan setiap aksi sampai approver yang benar
menyetujuinya.

Studi kasus: PT Nusantara Logistik Prima (fiktif), kantor Jakarta (WIB),
Makassar (WITA), Jayapura (WIT), ~120 karyawan.

## Insight

Di korporasi Indonesia, jawaban atas *"boleh saya buka port ini?"*, *"boleh
kirim file ini ke vendor?"*, *"siapa yang harus approve?"* tersebar di SOP,
grup chat, dan ingatan senior staff. Tiga akibatnya:

1. **Keputusan tidak konsisten** — jawaban bergantung pada siapa yang ditanya.
2. **Security awareness rendah** — orang "tanya teman dulu", bukan "tanya sistem".
3. **CAB jadi bottleneck** — change request datang tidak lengkap, salah
   approver, atau bentrok jadwal; dikembalikan berkali-kali.

Masalahnya bukan kurang dokumen, tapi dokumen tidak bisa ditanya, saling
bertentangan (SOP Maret vs memo Oktober), dan sebagian tidak boleh dilihat
semua orang. Chatbot RAG biasa memperburuk ini: ia mengarang saat bukti tipis,
dan membocorkan keberadaan proyek rahasia lewat perbedaan jawaban.

## Solution design

Dua jalur di atas satu inti penjaga yang sama:

| Jalur | Untuk apa | Keluaran |
| --- | --- | --- |
| **Tanya-jawab** (`/api/ask`) | "Boleh atau tidak?" | Kutipan verbatim + flag konflik + "tidak tahu" + SME untuk eskalasi |
| **Pra-CAB** (`/api/requests`) | Change request & permintaan akses | Risiko + allowance (boleh / tidak / dengan syarat) + approver + kutipan + `basis`, lalu ditahan sampai disetujui |
| **Policy register** (`/api/policies`) | Aturan baru dari memo | Aturan diusulkan (manual atau LLM) → disahkan **pemilik dokumen** → keputusan berikutnya berubah |

Inti penjaga, urutannya tetap: deteksi prompt injection (termasuk varian
Unicode) → penyamaran PII → identitas dari persona terdaftar → permission
gate **sebelum** retrieval → retrieval → karantina dokumen berinstruksi →
flag konflik → audit log berantai hash.

Prinsip desain:

- **LLM tidak pernah memutus.** Izin, risiko, approver, dan verdict selalu dari
  kode/aturan deterministik. LLM hanya menyalin tiket bebas ke field dan
  mengusulkan aturan — keduanya wajib berkutipan dan disahkan manusia. Tanpa
  LLM pun sistem tetap berjalan (default `off`).
- **Non-interference, bukan kata kunci terlarang.** Dokumen yang tidak boleh
  dibaca penanya dilewati sebelum penilaian, jadi jawaban untuk "Proyek
  Garuda" identik dengan proyek fiktif. Diuji dengan hypertest untuk semua
  persona.
- **Aturan adalah data.** Kebijakan baru = aturan di register, bukan kode baru.
  Perusahaan > standar global; lebih baru > lebih lama; konflik ditampilkan.
- **Setiap kesimpulan menyebut tingkat kepastiannya** (`sop` / `standar` /
  `interpretasi` / `sistem`) — tafsiran tim tidak disamarkan sebagai bunyi SOP.
- **Semua tercatat dan bisa diputar ulang.** State change request = replay
  audit log; rantai hash mendeteksi baris yang diubah atau dihapus.

Stack: Python stdlib (tanpa dependensi) untuk engine dan API, Svelte 5 + TS
untuk UI, skill WorkBuddy/Claude dari engine yang sama.

## Business value

- **Konsisten dan cepat:** pertanyaan yang sama mendapat jawaban dan kutipan
  yang sama, detik itu juga, 24 jam — tanpa menunggu senior staff.
- **CAB lebih efisien:** change request tiba lengkap, sudah diklasifikasi
  risikonya, sudah dirutekan ke approver yang benar, dan sudah dicek terhadap
  jendela maintenance, replikasi WMS, dan memo terbaru.
- **Kepatuhan yang bisa dibuktikan:** setiap keputusan membawa kutipan dan
  tercatat di audit log yang bisa diverifikasi — siap untuk audit ISO 27001
  dan kewajiban UU PDP.
- **Aman untuk data sensitif:** proyek rahasia tidak bocor, PII disamarkan,
  instruksi tersembunyi ditolak, tidak ada aksi tanpa persetujuan.
- **Jujur saat tidak tahu:** "tidak tahu" + nama SME lebih bernilai daripada
  jawaban yang terdengar yakin tapi salah.

## Status & bukti

- 173 unit test + 46 kasus regresi, semuanya hijau; kegagalan yang diketahui
  ditulis apa adanya (`expectedFailure`).
- Matriks 20 tes brief: 16 lulus, 1 sebagian, 2 gagal, 5 belum dibangun di
  jalur tanya-jawab — `docs/test-results/README.md`.
- Pra-CAB end-to-end 16 langkah — `docs/test-results/pracab.md`.
- Accountability sheet — `docs/submission/accountability-sheet.md`.
- Arsitektur & trust boundary — `docs/architecture-diagram.svg`; roadmap —
  `docs/vision-v2.md`.
