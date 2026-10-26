# Frontend: SecuritySahabat Chat UI

Vite + Svelte 5 + TypeScript (keputusan: [docs/decisions/0001](../docs/decisions/0001-frontend-svelte-dan-api-tipis.md)).
Arah visual dan token: [DESIGN.md](DESIGN.md).

## Menjalankan

Butuh Node 22 dan Python 3.10+.

```bash
npm ci --ignore-scripts
```

Mode pengembangan (dua terminal; Vite meneruskan `/api` ke port 8787):

```bash
python ../backend/api/server.py
```

```bash
npm run dev
```

Satu proses untuk demo (UI hasil build dilayani API, satu origin dengan CSP):

```bash
npm run build && python ../backend/api/server.py --static dist
```

## Tes

```bash
npm run check   # svelte-check, gagal bila ada warning
npm test        # Vitest: komponen + klien API
npm run e2e     # Playwright terhadap build + API asli (sekali: npx playwright install chromium)
```

Rancangan tes dan status terhadap test matrix brief: [docs/testing.md](../docs/testing.md).

## Struktur

| Path | Isi |
| --- | --- |
| `src/App.svelte` | Persona, percakapan, state menunggu/galat/coba lagi |
| `src/components/AnswerSheet.svelte` | Lembar jawaban per status: stempel, nomor catatan, flag, landasan, eskalasi |
| `src/components/EvidenceCard.svelte` | Satu kutipan verbatim + metadata dokumen |
| `src/components/Composer.svelte` | Kotak tanya (Enter kirim, Shift+Enter baris baru, batas 2000) |
| `src/lib/api.ts` | Klien `/api/ask` dan `/api/personas`, timeout 30 detik |
| `e2e/` | Skenario demo end-to-end + axe |

## Aturan UI

- Status yang ditampilkan hanya `OK`, `NO_MATCH`, `INJECTION_DETECTED`. Topik
  restricted datang sebagai `NO_MATCH` yang identik; jangan menambah pembeda.
- Kutipan ditampilkan apa adanya, tidak diringkas atau dipotong.
- Pertanyaan mentah tidak pernah ditampilkan atau disimpan; yang tampil adalah
  `question_masked` dari server.
- `answer` bernilai `null` untuk `OK` sampai answer composer (S4) ada; UI tidak
  boleh mengarang kesimpulan boleh atau tidak.
