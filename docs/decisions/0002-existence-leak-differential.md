# 0002: Restricted terms leak through response differences

- Date: 2026-10-27
- Status: Accepted

## Context

Found by `backend/tests/test_accountability.py`. For an unauthorized asker, a
question that mentioned a restricted keyword was silenced as a whole
(`RESTRICTED_SILENCED`), while the same question with an unknown project name
was answered normally:

| Asker: Ragil | Engine result (before) |
| --- | --- |
| "Who owns Project Garuda?" | `RESTRICTED_SILENCED`, no hits |
| "Who owns Project Falcon?" | `OK` with weak hits |
| "Boleh remote ke firewall Makassar? Garuda" | silenced |
| "Boleh remote ke firewall Makassar? Falcon" | `OK`, SOP-7 |

Mapping the status to `NO_MATCH` in the API did not help: the difference
between "no answer" and "an answer" was itself the leak. The handbook treats
exposing restricted information as a critical failure (ethics score capped at
5/10). Follow-up analysis found two more channels of the same kind: documents
in zones the asker cannot read were searched and then dropped (post-filter,
visible as `PERMISSION_FILTERED` and Template 6 "di luar akses Anda"), and
term weights (idf) were computed over documents the asker cannot read, so the
ranking they saw depended on those documents existing (the STRESS attack,
Wang et al., IEEE S&P 2017).

## Options considered

1. Treat restricted terms as unknown words: skip unreadable documents before
   scoring so they cannot influence the answer.
2. Silence any question naming any capitalised unknown project.
3. Keep the behaviour and document it as a known failure.

## Decision (decided by: Farrez)

Option 1, extended to every document the asker cannot read (locked restricted
projects and zones outside `allowed_zones`). Documents are skipped before
scoring, idf is computed from readable documents only, conflict flags never
name an unreadable document, and the web API takes identity only from the
selected persona, never from the question text.

## Reasoning (Farrez's words)

"Garuda dan proyek fiktif harus lewat jalur kode yang sama supaya responsnya
pasti identik, bukan bergantung daftar kata. Pelanggaran kritis membatasi skor
etika di 5/10, jadi kebocoran harus tertutup sebelum tes kejutan juri."

## Consequences

- `RESTRICTED_SILENCED` (rc 2), the trigger lists, `NEVER_BLOCK` and the
  "proyek" over-blocking are gone. Skill instructions updated.
- A question about Garuda from an unauthorized persona may now return weak,
  unrelated public evidence, exactly as for a fake project. That is a relevance
  problem (brief test #7), not a leak.
- `PERMISSION_FILTERED` only appears for `risk_gate: enforce`.
- Property guarded by `NonInterferenceTest` (full KB vs KB without unreadable
  documents must give identical output) and `HIDDEN` cases in verify_matrix.

## Revisit when

- A generative answer composer (S4) is added: its prompt must only ever see
  readable documents, and response length must not depend on hidden ones.
- Latency becomes observable to users: all documents are still loaded for
  every request, so timing does not depend on the asker, but this is not
  measured by a test.
