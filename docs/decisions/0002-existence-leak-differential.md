# 0002: Restricted terms leak through response differences

- Date: 2026-10-27
- Status: Proposed (needs Izzat + Farrez)

## Context

Found by `backend/tests/test_accountability.py` (two `expectedFailure` tests).
For an unauthorized asker, a question that mentions a restricted keyword is
silenced as a whole (`RESTRICTED_SILENCED`), while the same question with an
unknown project name is answered normally:

| Asker: Ragil | Engine result |
| --- | --- |
| "Who owns Project Garuda?" | `RESTRICTED_SILENCED`, no hits |
| "Who owns Project Falcon?" | `OK` with weak hits |
| "Boleh remote ke firewall Makassar? Garuda" | silenced |
| "Boleh remote ke firewall Makassar? Falcon" | `OK`, SOP-7 |

The API maps `RESTRICTED_SILENCED` to `NO_MATCH`, but the difference between
"no answer" and "an answer" is itself the leak: an employee can confirm that
Garuda exists by comparing two questions. The handbook treats exposing
restricted information as a critical failure (ethics score capped at 5/10).
The Indonesian form "Siapa owner Proyek X?" is safe only because the word
"proyek" alone already silences everything.

## Options

1. **Treat restricted terms as unknown words (recommended).** Scrub the trigger
   words from the query and answer the rest normally, exactly as an unknown
   word would be. Garuda and Falcon then produce the same output by
   construction. Cost: change in `search()`/`process_query()` and the
   restricted-handling docs; `RESTRICTED_SILENCED` becomes an internal audit
   flag only. Risk: a question that is only a restricted name returns weak
   hits on the remaining words, same as for Falcon.
2. **Silence any question naming any capitalised unknown project.** Keeps the
   current model but must guess what a "project name" is; easy to miss
   variants (English, typos, other entity types).
3. **Keep current behaviour and document it** as a known failure in the test
   results. Cheapest; judges may find it in the live test.

## Recommendation

Option 1. It is the only one where indistinguishability is a property of the
code path rather than of a word list. Wrong choice if the team wants the demo
to visibly "refuse" restricted questions; the handbook asks for the opposite.

## Decision

Pending. Tests stay `expectedFailure` until this is decided, then flip to
normal tests.
