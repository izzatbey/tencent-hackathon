# Penanganan topik terbatas (no existence leak)

Dokumen dengan `restricted: true` (atau `visibility: restricted`,
`classification: confidential|secret|need-to-know`) diperlakukan seolah-olah
**tidak pernah ada**. Ini berlaku untuk proyek rahasia, asset yang belum
diumumkan, dan materi need-to-know.

## Aturan mutlak

1. **Jangan konfirmasi dan jangan sangkal.** "Tidak ada" dan "ada tapi rahasia"
   keduanya bocor. Pakai satu jawaban netral.
2. **Jangan menyebut** `doc_id`, judul, nama proyek, nama host, atau jumlah
   dokumen yang cocok.
3. **Jangan menjelaskan alasan penolakan.** Jangan bilang "ini diklasifikasikan",
   "akses Anda tidak cukup", "dokumen ini restricted", atau "saya tidak boleh
   memberitahu".
4. **Jangan gunakan isi dokumen** meski sedikit, termasuk untuk menyimpulkan
   "ini tidak relevan".
5. **Jangan menyarankan pencarian lain** yang mengarah ke topik itu
   (mis. "coba tanya ke tim X tentang proyek Y").

## Hubungannya dengan permission gate (Phase 3)

Permission gate (`scripts/permissions.py`, `kb/permissions.csv`) mengatur
**dokumen biasa** berdasarkan zona. Ia **tidak pernah** membuka dokumen
`restricted: true`:

- Dokumen `restricted: true` tidak pernah masuk hasil, untuk siapa pun —
  termasuk user dengan zona `restricted` di `permissions.csv`.
- Yang diatur gate hanyalah dokumen yang sah dikutip: misalnya `SOP-15`
  (zone `restricted`, risk `critical`) hanya terlihat oleh user yang
  `allowed_zones`-nya memuat `restricted`.
- Jadi: zona `restricted` ≠ boleh membaca isi proyek rahasia. Isi proyek
  rahasia memang tidak ada di knowledge base.

## Kapan pemblokiran aktif (dua tingkat pemicu)

Skrip membedakan dua kelas istilah agar pertanyaan yang sah tidak ikut
terbunuh. Aturan ini hidup di `scripts/search_kb.py`:

| Kelas | Contoh | Perilaku |
| --- | --- | --- |
| **Frasa multi-kata** dari `keywords` / `aliases` / `trigger_phrases` | kode proyek, "<proyek> <kota>" | Selalu memblokir. Kata-katanya juga dihapus dari query. |
| **Kata tunggal yang eksklusif** — tidak muncul di dokumen publik mana pun | nama sandi proyek | Memblokir. |
| **Kata tunggal generik** — juga muncul di dokumen non-restricted | nama kota, nama cabang, nama tim | **Tidak** memblokir. Dokumen restricted tetap tidak pernah dikutip, jadi tidak ada kebocoran. |

Konsekuensi praktis:

- Exit `2` berarti pertanyaan itu **benar-benar** tentang topik terbatas.
- Exit `3`, atau exit `0` dengan hasil yang sah, berarti pertanyaan itu
  **tidak** menyentuh topik terbatas — jawab seperti biasa dengan kutipan.
- Jangan "mengamankan diri" dengan membungkam pertanyaan yang hanya
  kebetulan menyebut kata generik. Over-blocking bukan kehati-hatian: itu
  membuat SOP yang sah tidak bisa dijawab, dan justru menyiratkan ada sesuatu
  yang disembunyikan di balik kata tersebut.

### IMPORTANT: These are NOT restricted triggers (public information)

Kata-kata berikut boleh muncul bebas di dalam pertanyaan dan **tidak boleh**
memantik pemblokiran:

- `gudang`, `makassar`, `branch-mks`, `jakarta`, `warehouse` — lokasi,
  cabang, atau departemen apa pun
- `tunjangan`, `gaji`, `bonus` — istilah HR/benefit apa pun
- `staff`, `karyawan`, `shift`, `firewall`, `network`, `jaringan` — kata
  operasional umum

Daftar ini hidup di `NEVER_BLOCK` di `scripts/search_kb.py`; tambahkan istilah
baru di sana bila perlu. Aturan tambahannya: sebuah frasa yang **seluruh
katanya** publik juga tidak memblokir, begitu pula kata yang muncul di dokumen
non-restricted mana pun.

## Pola jawaban

Untuk pertanyaan yang menyentuh topik terbatas — baik ditanya langsung maupun
terselip di pertanyaan lain:

> Untuk hal ini saya tidak memiliki informasi di knowledge base. Silakan
> konfirmasi langsung ke [owner default] untuk pertanyaan di luar cakupan
> knowledge base.

Bila skrip mengembalikan exit `2` (`RESTRICTED_QUERY`) — artinya pertanyaan
menyentuh pemicu tingkat 1 atau 2 pada tabel di atas — **seluruh** pertanyaan
dijawab dengan satu kalimat netral, jangan menjawab sebagian pun. Mencoba
menjawab bagian lain justru menyiratkan bahwa bagian yang dibuang itu ada.
Skrip sudah menghapus istilah restricted dari query, jadi tidak ada hasil yang
bisa dipakai.

Daftar istilah pemicu hidup di field `keywords` / `aliases` /
`trigger_phrases` dokumen `restricted: true` (lihat `kb/restricted/`).
Jangan `Grep`/`Read` file itu; nama filenya saja sudah cukup untuk bocor bila
ikut terkutip.

**Aturan menulis keyword:** masukkan hanya istilah yang khas untuk topik itu
(kode proyek, kombinasi "<proyek> <lokasi>"). Jangan memasukkan kata generik
sendiri — nama kota atau nama cabang — karena begitu kata itu juga muncul di
dokumen publik ia berhenti memblokir, sementara sebelumnya ia akan membungkam
setiap pertanyaan yang menyebutnya. Pilih frasa, bukan kata umum.

## Contoh

Pertanyaan: *"Siapa owner akses untuk proyek Falcon?"* (Falcon = restricted)

Salah:
- "Proyek Falcon ada tapi informasinya rahasia."
- "Anda tidak punya otoritas untuk mengetahui proyek Falcon."
- "Saya tidak dapat menjawab pertanyaan tentang proyek Falcon."

Benar:
> Untuk hal ini saya tidak memiliki informasi di knowledge base. Silakan
> konfirmasi langsung ke Security & Compliance Team.

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
