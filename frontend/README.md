# Frontend — SecuritySahabat Chat UI

Belum dimulai. Stack bebas dipilih oleh owner frontend.

## Yang perlu dibangun

- Input pertanyaan (+ opsional identitas: nama / role).
- Tampilan jawaban sesuai `status` dari API:
  - `OK` → jawaban, daftar kutipan (`doc_id`, judul, quote verbatim, owner), badge flag.
  - `NO_MATCH` → "Tidak tahu" + nama SME untuk eskalasi. Status ini juga
    dipakai untuk topik restricted — frontend tidak boleh bisa membedakannya.
  - `INJECTION_DETECTED` → minta pengguna memparafrasekan pertanyaan.

## Kontrak

Lihat [docs/architecture.md §4](../docs/architecture.md#4-kontrak-api--draf-untuk-disepakati-fe--be).
Selama API belum ada, gunakan contoh response di sana sebagai mock.

## Aturan UI

- Jangan menampilkan atau me-log teks pertanyaan mentah yang berisi PII.
- Kutipan ditampilkan apa adanya (verbatim), jangan diringkas.
