# Penanganan topik terbatas (no existence leak)

Dokumen dengan `restricted: true` (atau `visibility: restricted`,
`classification: confidential|secret|need-to-know`) diperlakukan seolah-olah
**tidak pernah ada** — kecuali bagi penanya yang tercantum pada proyeknya
(lihat bagian permission gate di bawah). Ini berlaku untuk proyek rahasia,
asset yang belum diumumkan, dan materi need-to-know.

## Aturan mutlak

1. **Jangan konfirmasi dan jangan sangkal.** "Tidak ada" dan "ada tapi rahasia"
   keduanya bocor. Pakai satu jawaban netral.
2. **Jangan menyebut** `doc_id`, judul, nama proyek, nama host, atau jumlah
   dokumen yang cocok. Satu-satunya pengecualian: menggemakan kata-kata
   penanya sendiri di baris "Yang sudah saya cek" Template 3 — persis seperti
   yang dilakukan untuk topik yang memang tidak ada.
3. **Jangan menjelaskan alasan penolakan.** Jangan bilang "ini diklasifikasikan",
   "akses Anda tidak cukup", "dokumen ini restricted", atau "saya tidak boleh
   memberitahu".
4. **Jangan gunakan isi dokumen** meski sedikit, termasuk untuk menyimpulkan
   "ini tidak relevan".
5. **Jangan menyarankan pencarian lain** yang mengarah ke topik itu
   (mis. "coba tanya ke tim X tentang proyek Y").

## Hubungannya dengan permission gate (Phase 3)

Permission gate (`scripts/permissions.py`, `kb/permissions.csv`) mengatur
dokumen biasa berdasarkan zona, dan membuka dokumen `restricted: true`
**hanya** bila ketiga syarat ini terpenuhi:

1. Dokumen punya field `project` (mis. `project: "proyek-garuda"`).
2. `allowed_projects` penanya memuat proyek itu (atau `*`).
3. Gate aktif — `--no-permission-gate` / `skip_permission_gate` tidak pernah
   membuka proyek.

Setelah terbuka, dokumen itu diperlakukan seperti dokumen biasa: dikutip,
tetap melewati filter zona (`allowed_zones` harus memuat zonanya), dan diberi
flag `RISK` bila di atas batas risiko penanya.

| Penanya | Proyek Garuda |
| --- | --- |
| Andini (IT Admin), Indah (HR Manager) — `proyek-garuda` di `allowed_projects` | Terbuka, dengan kutipan `RESTRICTED-01` |
| Siapa pun lainnya, termasuk Citra yang aksesnya luas | Tidak ada: hasil sama dengan proyek fiktif |

Catatan: zona `restricted` saja ≠ boleh membaca isi proyek rahasia. Zona itu
mengatur dokumen seperti `SOP-15`; isi proyek butuh `allowed_projects`.

## Cara kerjanya: tidak dicari sama sekali

Sejak 27 Okt 2026 (docs/decisions/0002) skrip **tidak** lagi membungkam
pertanyaan yang menyebut nama proyek restricted. Dokumen yang tidak boleh
dibaca penanya dilewati sebelum penilaian, dan bobot istilah (idf) hanya
dihitung dari dokumen yang boleh ia baca. Akibatnya, bagi penanya yang tidak
berwenang, jawaban untuk "Proyek Garuda" sama persis dengan jawaban untuk
proyek yang tidak pernah ada, termasuk dalam bahasa Inggris, sebagai prefiks
("Proyek Gar..."), atau ditempel ke pertanyaan lain.

Kenapa pembungkaman lama dihapus: "Who owns Project Garuda?" dibungkam,
sedangkan "Who owns Project Falcon?" dijawab dengan bukti. Selisih itu sendiri
membuktikan Garuda ada. Pembungkaman berbasis daftar kata selalu bisa
dibandingkan dengan nama fiktif; melewati dokumennya tidak.

Konsekuensi praktis:

- Tidak ada exit `2` dan tidak ada baris `RESTRICTED_QUERY`. Jawab dari bukti
  yang ada seperti biasa; bila buktinya tidak menjawab inti pertanyaan, pakai
  Template 3.
- Kata "proyek" tidak lagi membungkam apa pun; "share dokumen proyek ke
  vendor" dijawab dari SOP yang boleh dilihat penanya.
- `keywords` / `aliases` di dokumen restricted sekarang hanya metadata,
  bukan pemicu. Tidak perlu lagi memilih kata khusus supaya tidak
  over-blocking.

## Pola jawaban

Untuk pertanyaan yang menyentuh topik terbatas, jangan menambahkan kalimat
apa pun tentang topik itu. Jawab bagian yang didukung bukti; bila tidak ada,
pakai **Template 3 di `answer-playbook.md` apa adanya**, kata per kata, sama
seperti untuk topik yang memang tidak ada. Jawaban dengan kalimat khusus
(sekalipun netral) sudah membocorkan: penanya bisa membandingkannya dengan
jawaban untuk proyek fiktif.

`verify_matrix.py` (kasus `HIDDEN` dan blok "Existence leak") dan
`tests/test_accountability.py` (`NonInterferenceTest`) menguji ini: keluaran
untuk penanya tak berwenang harus identik dengan dan tanpa dokumen restricted.

Jangan `Grep`/`Read` file di `kb/restricted/`; nama filenya saja sudah cukup
untuk bocor bila ikut terkutip.

## Contoh

Pertanyaan: *"Siapa owner akses untuk proyek Falcon?"* (Falcon = restricted)

Salah:
- "Proyek Falcon ada tapi informasinya rahasia."
- "Anda tidak punya otoritas untuk mengetahui proyek Falcon."
- "Saya tidak dapat menjawab pertanyaan tentang proyek Falcon."

Salah juga (kalimat khusus, beda dengan jawaban untuk proyek fiktif):
- "Untuk hal ini saya tidak memiliki informasi di knowledge base."

Benar — Template 3, identik dengan jawaban untuk proyek yang tidak ada:
> Jawaban langsung: Saya tidak tahu — hal ini belum tercakup di knowledge base
> saya. Saya tidak akan menebak.
>
> Yang sudah saya cek: owner akses proyek Falcon
>
> Langkah selanjutnya:
> 1. Konfirmasi ke SME pemilik materi: Andini Pratama (IT Admin)
> 2. Bila Anda pemilik materinya, tambahkan dokumen ke knowledge base

## Contoh over-blocking (jangan dilakukan)

Pertanyaan: *"Boleh remote ke firewall cabang dari rumah? Cukup verbal
approval?"* — kata cabang/kota juga dipakai di dokumen publik (SOP-7,
topologi).

Salah:
- Membungkam pertanyaan ini hanya karena menyebut nama kota itu.
- Menjawab "untuk bagian ini saya tidak memiliki informasi" padahal SOP-7
  mengaturnya lengkap.

Benar: jawab normal dengan kutipan SOP-7. Dokumen restricted tetap tidak
pernah muncul sebagai hasil, jadi tidak ada yang bocor.
