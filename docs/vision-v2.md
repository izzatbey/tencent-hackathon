# Visi & roadmap v2 — SecuritySahabat sebagai "CAB decision brain"

Status: draf 27 Okt 2026 (Izzat). Melengkapi `adjusted_brief.md` (Challenge A)
dan ADR 0003 (Pra-CAB). Dipakai untuk bagian *solution design* dan
*feasibility* di submission, dan sebagai rencana setelah 1 Nov.

## 1. Tujuan akhir

Bukan chatbot. Sebuah sistem pendukung keputusan untuk Change Advisory Board:

1. Perusahaan mengunggah **knowledge base**-nya sendiri (SOP, memo, CMDB,
   topologi). Di bawahnya ada **knowledge base global** (ISO 27001, NIST CSF /
   SP 800-53, GDPR, UU PDP) yang berlaku bila perusahaan belum punya aturan.
2. User mengajukan **tiket** (perubahan atau akses) dalam bahasa bebas.
3. **LLM + RAG + agent** menerjemahkan tiket ke bentuk terstruktur, mencari
   aturan dan bukti yang relevan, lalu sistem menghasilkan **risiko** dan
   **allowance** yang jelas: boleh, tidak boleh, atau boleh dengan syarat;
   setiap kesimpulan membawa kutipan dan tingkat kepastiannya.
4. Eksekusi tetap menunggu persetujuan manusia, dan semuanya tercatat di
   audit log yang bisa diverifikasi.

Satu "otak kerja" kepatuhan per perusahaan, yang deterministik dan bisa diaudit.

## 2. Kondisi sekarang (main, 27 Okt)

| Bagian visi | Sudah ada | Belum |
| --- | --- | --- |
| Tiket | intake teks bebas → draft (LLM), field terstruktur, state machine, approval per slot, mock dispatch, undo | UI; kanal email/tiket eksternal |
| KB perusahaan | 30 dokumen markdown + CMDB + direktori, dipecah manual dengan metadata (`zone`, `restricted`, `owner`, `effective_date`) | upload; konfirmasi metadata; versi |
| KB global | 14 kontrol `CTRL-xx` (ISO 27001 ↔ NIST CSF, guidance parafrase) | sisa kontrol ISO; GDPR/UU PDP |
| Retrieval | kata kunci + idf, stdlib, gate sebelum skor (non-interference) | embedding/hybrid untuk KB yang diunggah bebas |
| Penilaian tiket | `cab_rules.py`: 13 jenis cek, 36 kutipan terverifikasi, label `sop`/`standar`/`interpretasi`/`sistem`, dua tingkat (policy perusahaan → standar global) untuk akses | aturan masih kode; belum bisa diisi dari dokumen yang diunggah |
| LLM/agent | intake saja; keputusan 100 % kode | ekstraksi aturan dari dokumen; penilaian fallback berbasis RAG |
| Audit | satu rantai hash, replay, verify, fail-closed | — |

Kerangka akuntabilitasnya selesai. Yang belum ada adalah **lapisan policy yang
diisi data, bukan kode**.

## 3. Contoh: "akses VPN ke Server A untuk marketing"

Dengan `ACCESS-SCOPE` (27 Okt) kedua tingkat sudah bisa didemokan
(`python tools/demo_pracab.py`, langkah 11–12):

| Situasi | Hasil | Basis | Kutipan |
| --- | --- | --- | --- |
| CMDB mencatat `app-erp-prod` hanya untuk IT, Operations, Finance; penerima dari Marketing | **BLOCKED** — "bukan departemen yang boleh mengakses" | `sop` (policy perusahaan) | sel CMDB `allowed_departments` + CTRL-02 |
| Penerima dari Finance | PASS, lanjut ke approver biasa | `sop` | sel CMDB |
| Perusahaan **tidak punya** policy untuk `mail-jkt-01` (kolom kosong) | READY dengan WARN: dinilai dengan standar; owner aset ditambahkan sebagai approver | `standar` (ISO A.5.18 via CTRL-02) | CTRL-02 |
| Penerima tidak ada di direktori | NEEDS_INFO | `sistem` | — |

Jawabannya tetap jelas di kedua tingkat; yang berbeda adalah **tingkat
kepastian**, dan sistem menyebutkannya lewat `basis`.

Batasnya hari ini: policy "siapa boleh mengakses apa" baru bisa dinyatakan
lewat kolom CMDB. Policy lain (jam, eksposur, jenis perubahan) masih kode di
`cab_rules.py`.

## 4. Arsitektur target

```
Dokumen: SOP/memo perusahaan · CMDB · ISO/NIST/GDPR/UU PDP
   │  upload → chunk → metadata (zona, owner, tanggal, restricted)
   │  DIKONFIRMASI manusia; default sebelum dikonfirmasi = restricted
   ▼
KB bertingkat   [1] perusahaan  >  [2] standar global
                (lebih spesifik & lebih baru menang; konflik ditampilkan, tidak dirata-ratakan)
   │
   │  LLM mengekstrak USULAN aturan terstruktur dari chunk, tiap usulan membawa kutipan
   ▼
Policy register   draft → disahkan owner dokumen (lewat approval gate yang sama) → aktif → kedaluwarsa
   │
   ▼
Tiket → intake (LLM) → policy engine (deterministik) → risiko + allowance + approver + kutipan
   │                           │
   │                           └─ tidak ada aturan yang cocok → jalur RAG:
   │                              bukti + penilaian LLM, DILABEL "pendapat, bukan aturan",
   │                              tidak pernah READY tanpa manusia
   ▼
approval → dispatch (mock/konektor) → audit hash-chain  (sudah ada)
```

Tiga peran LLM, semuanya di luar jalur keputusan:

| Peran | Masukan | Keluaran | Pengaman |
| --- | --- | --- | --- |
| Intake | teks tiket | field draft + kutipan per field | field tanpa kutipan dibuang; aset dicek ke CMDB (sudah ada) |
| Ekstraksi aturan | chunk dokumen (lolos injection guard) | usulan aturan + kutipan | tidak aktif tanpa pengesahan manusia; kutipan diverifikasi ada di dokumen |
| Penilaian fallback | bukti RAG + tiket | narasi + saran verdict | ditandai `basis: pendapat`, kepercayaan rendah, wajib manusia |

## 5. Skema aturan (usulan)

```json
{"id": "RULE-0042", "status": "active", "basis": "sop",
 "source": {"doc_id": "SOP-21", "section": "3", "quote": "Server A hanya untuk tim infrastruktur dan operasional."},
 "subject": {"asset": "app-erp-prod"},
 "action": "access_grant",
 "condition": {"grantee_department_not_in": ["IT", "Operations"]},
 "effect": "DENY",
 "message": "Hanya IT dan Operations yang boleh mengakses app-erp-prod.",
 "effective_date": "2026-09-01", "expires": null, "approved_by": "Andini Pratama", "approved_at": "..."}
```

- `subject`: aset, zona, jenis perubahan, atau `*`.
- `condition`: departemen/role penerima, jam & hari, eksposur, port, flag tiket.
- `effect`: `DENY` · `ALLOW` · `REQUIRE_APPROVER` · `REQUIRE_FIELD` · `RAISE_RISK` · `WARN`.
- Semua cek yang ada di `cab_rules.py` hari ini bisa dinyatakan dengan skema
  ini, jadi migrasinya bertahap: cek kode → aturan data, satu per satu, dengan
  tes yang sama.

## 6. Keputusan desain yang harus diambil

1. **Aturan = data.** LLM mengusulkan, manusia mengesahkan, kode menerapkan.
   Tanpa ini, setiap perusahaan baru berarti kode baru.
2. **Default restricted saat upload.** Hari ini dokumen tanpa `zone` jatuh ke
   `common` (terlihat semua orang). Untuk upload harus dibalik.
3. **Retrieval hybrid.** Kata kunci + BM25 cukup sampai ribuan chunk; KB bebas
   butuh embedding. Ini dependensi baru; lepaskan prinsip "tanpa dependensi"
   setelah 1 Nov, bukan sebelumnya.
4. **Lisensi standar global.** Teks ISO 27001 berhak cipta dan berbayar: hanya
   ID kontrol + guidance parafrase yang ditandai "simplified" (pola `CTRL-xx`
   sekarang). NIST CSF/SP 800-53 public domain; GDPR dan UU PDP teks hukum
   publik dan boleh dikutip.
5. **Precedence.** Perusahaan > standar; lebih baru > lebih lama; konflik
   ditampilkan, tidak dirata-ratakan (sudah jadi aturan di ADR 0003).
6. **Injection di dokumen.** Chunk lewat `injection_guard` sebelum ke LLM;
   usulan aturan dari dokumen terinjeksi dikarantina, bukan dibuang diam-diam.

## 7. Roadmap

| Fase | Isi | Target |
| --- | --- | --- |
| 0 (selesai 27 Okt) | Pra-CAB, audit hash-chain, adapter LLM, `ACCESS-SCOPE` dua tingkat | submission 1 Nov |
| 1 | UI Pra-CAB (Farrez), demo video, accountability sheet, test results | 1 Nov |
| 2 | Policy register + skema aturan; migrasi cek `cab_rules.py` ke data; engine membaca register | Demo Day 27 Nov |
| 3 | Upload KB: chunking, metadata wajib dikonfirmasi, default restricted, versi dokumen | setelah hackathon |
| 4 | Ekstraksi aturan oleh LLM + pengesahan lewat approval gate; "suntingan manusia → usulan aturan" | setelah hackathon |
| 5 | Retrieval hybrid (BM25 + embedding); KB global lengkap (ISO 27001 A.5–A.8, NIST, GDPR/UU PDP) | setelah hackathon |
| 6 | Konektor nyata (email, kalender, tiket) di belakang approval gate; SSO menggantikan pemilih persona | produk |

## 8. Risiko yang diakui

- **Bocor lewat dokumen unggahan** bila metadata salah. Mitigasi: default
  restricted + konfirmasi owner + tes non-interference dijalankan ke setiap
  dokumen baru.
- **Aturan hasil ekstraksi LLM salah.** Mitigasi: tidak aktif tanpa manusia;
  kutipan diverifikasi; setiap aturan punya `basis` dan sumber.
- **Jalur fallback RAG memberi kesan pasti.** Mitigasi: label `pendapat`,
  tidak pernah menghasilkan `READY`, UI membedakan warnanya.
- **Pergeseran dari Challenge A.** Handbook menilai semua finalis dengan
  dimensi yang sama; 20 tes Challenge A tetap dilaporkan apa adanya.
