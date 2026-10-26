# DESIGN: SecuritySahabat UI

Mode: Operate. Satu tugas: bertanya, membaca bukti, tahu harus menghubungi siapa.

## Arah

Gabungan "meja bukti" dan gaya Apple, dipilih Farrez 2026-10-27.

- Jangkar dunia nyata: lembar disposisi kantor dan stempel tinta biru. Jawaban
  adalah lembar di atas meja abu-dingin; statusnya adalah stempel berbingkai
  (Bukti ditemukan, Tidak tahu, Ditolak); setiap lembar bernomor catatan
  (`q_id`) seperti nomor agenda surat.
- Dari Apple: latar abu-dingin, ruang lega, header tembus pandang, kontrol
  native (`<select>` asli untuk persona), animasi pendek yang menghormati
  reduced motion.
- Dihindari dengan sengaja: krem/parchment (klaster "dibuat AI"), ungu, Inter,
  lucide, bayangan, garis kiri berwarna di kartu, emoji.

## Token (src/app.css)

| Token | Terang | Gelap | Peran |
| --- | --- | --- | --- |
| `--surface` | #f2f3f6 | #101114 | meja |
| `--sheet` | #fefefd | #1a1c21 | lembar jawaban, kotak tanya |
| `--ink` / `--ink-2` / `--ink-3` | #16181d / #474c57 / #636978 | #eceef1 / #b6bac3 / #9299a6 | teks utama, sekunder, keterangan |
| `--accent` | #2440a0 | #a3b5f4 | tinta stempel: satu-satunya aksen |
| `--deny` | #b42318 | #f59b90 | ditolak, galat |
| `--warn` | #8f4500 | #f3b86c | konflik antar sumber |

Arti tidak pernah hanya dari warna: setiap stempel dan flag punya ikon dan
label teks. Kontras diuji axe (WCAG 2.2 AA) di kedua tema.

## Tipografi

- UI: font sistem (SF di Apple, Segoe di Windows), tanpa unduhan.
- Serif `Source Serif 4` (variable, optical size): judul, kalimat jawaban,
  dan kutipan. Kutipan adalah bukti, jadi tampil seperti teks dokumen.
- Mono `IBM Plex Mono`: `doc_id`, nomor catatan, stempel. Mengingatkan pada
  nomor surat dan kode kontrol.
- Angka tabular di seluruh halaman.

## Bentuk

Radius per peran: lembar 14px, kontrol 10px, chip `doc_id` 6px, stempel 3px.
Batas 1px, tanpa bayangan. Target sentuh minimal 44px.

## Ikon

Phosphor regular (MIT), diambil per ikon saat build lewat `?raw`.

## Aturan perilaku

- Kutipan verbatim, tidak dipotong (`white-space: pre-line`).
- Pertanyaan yang tampil adalah versi tersamarkan dari server. Selama
  menunggu, yang tampil hanya keterangan, bukan teks mentah.
- Tidak ada yang ditulis ke localStorage/sessionStorage.
- `NO_MATCH` untuk topik restricted dan topik fiktif harus menghasilkan markup
  yang identik; UI tidak boleh menambah pembeda apa pun.
