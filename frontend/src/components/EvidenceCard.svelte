<script lang="ts">
  import type { Citation } from '../lib/types'
  import { formatDate, riskLabel } from '../lib/labels'

  let { citation, index }: { citation: Citation; index: number } = $props()

  const date = $derived(formatDate(citation.effective_date))
  const risk = $derived(riskLabel(citation.risk_level))
  // Section sering sama dengan judul dokumen; jangan ditulis dua kali.
  const place = $derived(
    [...new Set([citation.title, citation.section].map((s) => s?.trim()).filter(Boolean))].join(', '),
  )
</script>

<article class="evidence" aria-labelledby="ev-{index}">
  <header>
    <span class="doc-id" id="ev-{index}">{citation.doc_id}</span>
    {#if place}<span class="place">{place}</span>{/if}
  </header>

  <!-- Kutipan verbatim: tidak diringkas, tidak dipotong (frontend/README.md). -->
  <blockquote>{citation.quote}</blockquote>

  <dl>
    {#if citation.owner}<div><dt>Pemilik</dt><dd>{citation.owner}</dd></div>{/if}
    {#if date}<div><dt>Berlaku</dt><dd>{date}</dd></div>{/if}
    {#if citation.status}<div><dt>Status</dt><dd>{citation.status}</dd></div>{/if}
    {#if risk}<div><dt>Klasifikasi</dt><dd>{risk}</dd></div>{/if}
  </dl>
</article>

<style>
  .evidence {
    padding-block: 14px;
    border-block-start: 1px solid var(--rule);
  }
  .evidence:first-child {
    border-block-start: 0;
    padding-block-start: 4px;
  }
  header {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 4px 10px;
  }
  .doc-id {
    font: 500 0.8125rem/1.3 var(--font-mono);
    color: var(--accent);
    background: var(--accent-soft);
    border-radius: var(--r-chip);
    padding: 2px 7px;
    letter-spacing: 0.02em;
  }
  .place {
    font-size: 0.875rem;
    color: var(--ink-2);
    overflow-wrap: anywhere;
  }
  blockquote {
    margin: 10px 0 0;
    padding-inline-start: 1.1em;
    text-indent: -0.45em;
    font: 400 1.0625rem/1.55 var(--font-serif);
    font-optical-sizing: auto;
    overflow-wrap: anywhere;
    white-space: pre-line;
  }
  blockquote::before {
    content: '\201C';
  }
  blockquote::after {
    content: '\201D';
  }
  dl {
    display: flex;
    flex-wrap: wrap;
    gap: 2px 18px;
    margin: 10px 0 0;
    padding-inline-start: 1.1em;
    font-size: 0.8125rem;
    color: var(--ink-3);
  }
  dl div {
    display: flex;
    gap: 5px;
  }
  dt::after {
    content: ':';
  }
  dd {
    margin: 0;
    color: var(--ink-2);
  }
</style>
