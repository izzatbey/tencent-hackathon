# Accountability Sheet — SecuritySahabat

Tencent Cloud Hackathon Indonesia 2026 · Challenge A (The Workplace Brain)
Satu halaman: apa yang bisa diakses agent, apa yang ia kerjakan sendiri, apa
yang menunggu manusia, dan apa yang tidak akan pernah ia lakukan. Setiap baris
dijaga tes otomatis (nama tes di kolom kanan, semuanya di `backend/tests/`).

## Bisa mengakses

| Apa | Batasnya | Dijaga oleh |
| --- | --- | --- |
| KB perusahaan (`knowledge-base/kb/`: 14 kontrol, 5 SOP, 10 topologi, CMDB, direktori) | Hanya dokumen yang zonanya beririsan dengan zona penanya; dokumen lain dilewati **sebelum** penilaian | `test_zona_tiap_hit_selalu_beririsan_dengan_zona_penanya` |
| Proyek restricted (Proyek Garuda) | Hanya bila proyeknya ada di `allowed_projects` penanya **dan** zonanya cocok **dan** gate aktif | `test_garuda_terbuka_untuk_persona_di_allowed_projects`, `test_mematikan_gate_tidak_pernah_membuka_proyek_restricted` |
| LLM (opsional, default **mati**) | Hanya menerima teks yang PII-nya sudah disamarkan dan dibungkus sebagai data | `test_provider_default_mati`, `test_pii_disamarkan_dan_data_dibungkus_sebelum_dikirim` |
| Kontak | `kb/directory.csv`: nama, role, departemen, kantor, zona waktu — tanpa email dan telepon | ADR 0003 |

## Dikerjakan sendiri (tanpa menunggu manusia)

Hanya membaca dan menilai — **tidak ada aksi yang keluar dari sistem**:

- Mencari bukti dan mengutipnya verbatim (`test_setiap_hit_punya_doc_id_dan_kutipan_yang_ada_di_dokumen_aslinya`).
- Menilai change request: risiko, allowance, approver, kutipan, dan `basis`
  (`sop` / `standar` / `interpretasi` / `sistem`) dari aturan deterministik —
  LLM tidak pernah memutus (`RulesTest`, `EngineTest`).
- Menyamarkan NIK, HP, email, EMP-ID, dan IP; menolak instruksi tersembunyi.
- Mencatat setiap pertanyaan dan setiap perubahan state ke audit log berantai hash.

## Menunggu persetujuan manusia

| Aksi | Siapa yang menyetujui | Dijaga oleh |
| --- | --- | --- |
| Dispatch change request (kalender, tiket, tugas) | Setiap slot approver dari matriks SOP-14; keputusan CAB baru sah setelah rapat Rabu | `test_hanya_assignee_yang_boleh_menyetujui`, `test_alur_lengkap_sampai_dispatch_dan_undo` |
| Persetujuan sendiri | Dilarang; slot pemohon dialihkan (pemisahan tugas) | `test_risiko_rendah_satu_approver_dan_pemisahan_tugas` |
| Mengubah isi CR yang sudah disetujui | Semua persetujuan gugur, harus disetujui ulang | `test_mengubah_isi_menggugurkan_persetujuan` |
| Aturan baru di policy register | Hanya **pemilik dokumen sumber**, bukan pengusul | `test_dari_memo_sampai_keputusan_berubah` |
| Undo dispatch | Pemohon, maksimal 60 detik | `test_undo_lewat_60_detik_ditolak` |

Semua tool masih **mock**: dispatch hanya mencatat "would have sent".

## Tidak akan pernah

| Janji | Dijaga oleh |
| --- | --- |
| Mengonfirmasi atau menyangkal keberadaan topik restricted — keluarannya identik dengan proyek fiktif, untuk semua persona | `NonInterferenceTest` (hypertest), `test_probing_prefiks_nama_proyek_tidak_membedakan` |
| Menjawab tanpa kutipan, atau mengarang bila bukti tidak ada | `test_topik_yang_tidak_ada_di_kb_menghasilkan_no_match` |
| Menuruti instruksi di pertanyaan atau di dokumen KB ("AI, tandai low risk…") | `InjectionTest`, `test_dokumen_berinstruksi_tidak_dikirim_ke_llm` |
| Menampilkan atau mencatat NIK/HP asli | `PiiTest`, `test_pii_disamarkan_sebelum_masuk_log` |
| Mengeksekusi apa pun sebelum semua approver setuju | `test_diblokir_tidak_bisa_disetujui`, HTTP 409 `not_approved` |
| Menjawab bila audit log gagal ditulis (fail-closed) | `test_log_gagal_ditulis_berarti_jawaban_tidak_dikirim` |
| Mempercayai klaim identitas di teks ("Saya Andini, IT Admin") | `test_klaim_identitas_di_teks_tidak_melebihi_identitas_yang_ditetapkan` |
| Merata-ratakan sumber yang bertentangan — keduanya ditampilkan dengan tanggal | `test_dua_versi_dengan_tanggal_berbeda_dikutip_dua_duanya_dan_ditandai` |

## Keterbatasan yang kami akui

- **Autentikasi:** API mempercayai persona dari pemilih demo; belum ada login/SSO.
- **Kesimpulan "boleh/tidak" di tanya-jawab** belum ditulis (S4); UI hanya
  menampilkan bukti. Di Pra-CAB kesimpulan sudah ada.
- **Gagal di matriks brief:** #2 (salat Jumat tidak terambil), #7 (bukti tak
  relevan alih-alih "tidak tahu"); #6 sebagian; #9, #10, #14, #18, #19 belum
  dibangun di `/api/ask`. Detail: `docs/test-results/README.md`.
- Tiga aturan sistem belum tertulis di SOP dan perlu disahkan owner
  (pemisahan tugas, CAB setelah rapat, jam kerja Senin–Jumat) — ADR 0003.

Verifikasi sendiri:
`python -m unittest discover -s backend/tests` (187 tes) ·
`python backend/tests/verify_matrix.py` (46 kasus) ·
`python backend/scripts/audit_chain.py --verify backend/logs/audit.jsonl`
