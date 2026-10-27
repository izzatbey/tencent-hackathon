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
| Penilaian tiket | `cab_rules.py` + **policy register v0** (ADR 0004): `ACCESS-SCOPE`, `EXPOSURE`, `FRIDAY-PRAYER`, dan `BRANCH-FW-MEMO` sudah data (19 aturan seed), dua tingkat perusahaan → standar, kutipan diverifikasi setiap kali dipakai, label `sop`/`standar`/`interpretasi`/`sistem` | cek lain (kelengkapan, risiko, approver SOP-14, jendela waktu, emergency, SoD) masih kode |
| Policy register | aturan draft → active lewat audit chain; hanya pemilik dokumen sumber yang mengesahkan, bukan pengusul; aturan baru berlaku untuk pengajuan berikutnya | UI; register ikut permission gate bila ada aturan tentang aset restricted |
| LLM/agent | intake tiket; **ekstraksi aturan dari memo** (usulan + kutipan, divalidasi ke CMDB/direktori); keputusan tetap 100 % kode | ekstraksi diuji dengan FakeProvider, belum dengan Claude sungguhan; penilaian fallback berbasis RAG |
| Audit | satu rantai hash, replay, verify, fail-closed | — |

Kerangka akuntabilitas dan lapisan policy berbasis data (v0) sudah ada. Yang
belum: upload dokumen utuh, migrasi cek built-in, dan retrieval hybrid.

## 3. Contoh: "akses VPN ke Server A untuk marketing"

Semua baris di bawah bisa didemokan dengan `python tools/demo_pracab.py`
(langkah 11–16):

| Situasi | Hasil | Basis | Kutipan |
| --- | --- | --- | --- |
| Aturan `POL-s007`: `app-erp-prod` hanya untuk IT, Operations, Finance; penerima dari Marketing | **BLOCKED** — "bukan departemen yang boleh mengakses" | `sop` (policy perusahaan) | sel CMDB `allowed_departments` + CTRL-02 |
| Penerima dari Finance | PASS, lanjut ke approver biasa | `sop` | sel CMDB |
| Perusahaan **tidak punya** aturan untuk `mail-jkt-01` | READY dengan WARN: aturan standar `POL-g001`; owner aset ditambahkan sebagai approver | `standar` (ISO A.5.18 via CTRL-02) | CTRL-02 |
| Citra menerbitkan memo "mail-jkt-01 hanya untuk IT"; Andini mengusulkan aturan; Eka dan Andini ditolak saat mencoba mengesahkan; Citra mengesahkan | permintaan **berikutnya** BLOCKED; permintaan sebelumnya tetap READY | `sop` | kutipan memo |
| Penerima tidak ada di direktori | NEEDS_INFO | `sistem` | — |

Jawabannya tetap jelas di setiap tingkat; yang berbeda adalah **tingkat
kepastian**, dan sistem menyebutkannya lewat `basis`. Kebijakan baru tidak
butuh perubahan kode: dokumen masuk, aturan diusulkan (manual atau LLM),
pemilik dokumen mengesahkan, keputusan berikutnya berubah, dan semuanya
tercatat.

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
| 2a (selesai 27 Okt) | Policy register v0: skema, engine, seed (ACCESS-SCOPE + EXPOSURE), siklus hidup, `/api/policies`, ekstraksi LLM dari memo (ADR 0004) | submission 1 Nov |
| 1 | UI Pra-CAB (Farrez), demo video, accountability sheet, test results | 1 Nov |
| 2b | Migrasi cek built-in lain ke data (jendela waktu, approver SOP-14, memo SOP-7); perluasan `condition`/`effect`; UI register | Demo Day 27 Nov |
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
