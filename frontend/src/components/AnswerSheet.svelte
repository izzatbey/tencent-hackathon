<script lang="ts">
  import type { AskResponse } from '../lib/types'
  import { flagLabel, flagTone, personaLabel } from '../lib/labels'
  import EvidenceCard from './EvidenceCard.svelte'
  import Icon, { type IconName } from './Icon.svelte'

  let { response }: { response: AskResponse } = $props()

  const STAMPS: Record<AskResponse['status'], { label: string; icon: IconName; tone: string }> = {
    OK: { label: 'Bukti ditemukan', icon: 'sealCheck', tone: 'found' },
    NO_MATCH: { label: 'Tidak tahu', icon: 'question', tone: 'unknown' },
    INJECTION_DETECTED: { label: 'Ditolak', icon: 'prohibit', tone: 'deny' },
  }
  const stamp = $derived(STAMPS[response.status] ?? STAMPS.NO_MATCH)
  const count = $derived(response.citations.length)
</script>

<article class="sheet" data-status={response.status} aria-label="Jawaban {response.q_id}">
  <header class="head">
    <span class="stamp {stamp.tone}">
      <Icon name={stamp.icon} size={16} />
      {stamp.label}
    </span>
    <span class="record">
      <span class="visually-hidden">Nomor catatan audit</span>
      <span aria-hidden="true">No. catatan</span>
      <span class="q-id">{response.q_id}</span>
    </span>
  </header>

  {#if response.status === 'OK'}
    {#if response.answer}
      <p class="answer">{response.answer}</p>
    {:else}
      <p class="answer">
        Ditemukan {count} kutipan yang relevan. Baca landasannya sebelum bertindak; kesimpulan boleh
        atau tidak tetap dikonfirmasi ke pemilik dokumen.
      </p>
    {/if}

    {#if response.flags.length}
      <section class="flags" aria-label="Perlu perhatian">
        <h3>Perlu perhatian</h3>
        <ul>
          {#each response.flags as flag, i (i)}
            <li class={flagTone(flag)}>
              <Icon name={flagTone(flag) === 'conflict' ? 'gitDiff' : 'warning'} size={18} />
              <div>
                <strong>{flagLabel(flag)}</strong>
                <span class="flag-doc">{flag.doc}</span>
                <p>{flag.detail}</p>
              </div>
            </li>
          {/each}
        </ul>
      </section>
    {/if}

    <section class="evidence-list" aria-label="Landasan">
      <h3>Landasan</h3>
      {#each response.citations as citation, i (citation.doc_id + i)}
        <EvidenceCard {citation} index={i} />
      {/each}
    </section>
  {:else}
    <p class="answer">{response.answer}</p>
  {/if}

  {#if response.escalation}
    <p class="next">
      <span class="label">Langkah berikutnya:</span>
      konfirmasi ke <strong>{response.escalation}</strong>.
    </p>
  {/if}

  <footer>
    <span class="who">
      <Icon name="idCard" size={16} />
      Dijawab untuk {personaLabel(response.identity)}
    </span>
    {#if response.pii_masked}
      <span class="pii">
        <Icon name="eyeSlash" size={16} />
        Data pribadi disamarkan ({response.pii_masked})
      </span>
    {/if}
  </footer>
</article>

<style>
  .sheet {
    background: var(--sheet);
    border: 1px solid var(--rule);
    border-radius: var(--r-sheet);
    padding: 18px 20px 14px;
    animation: rise 260ms var(--ease-out);
  }
  @keyframes rise {
    from {
      opacity: 0;
      transform: translateY(6px);
    }
  }
  .head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 8px 16px;
  }
  .stamp {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 9px 3px 7px;
    border: 1.5px solid currentColor;
    border-radius: var(--r-stamp);
    font: 600 0.75rem/1.4 var(--font-mono);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  .stamp.found {
    color: var(--accent);
  }
  .stamp.unknown {
    color: var(--ink-2);
  }
  .stamp.deny {
    color: var(--deny);
  }
  .record {
    display: inline-flex;
    gap: 6px;
    font-size: 0.8125rem;
    color: var(--ink-3);
  }
  .q-id {
    font-family: var(--font-mono);
    color: var(--ink-2);
  }
  .answer {
    margin: 14px 0 0;
    font: 400 1.125rem/1.5 var(--font-serif);
    font-optical-sizing: auto;
    text-wrap: pretty;
  }
  h3 {
    margin: 20px 0 6px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--ink-3);
  }
  .flags ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 8px;
  }
  .flags li {
    display: flex;
    gap: 10px;
    padding: 10px 12px;
    border-radius: var(--r-control);
    background: var(--unknown-soft);
  }
  .flags li.conflict {
    background: var(--warn-soft);
    color: var(--warn);
  }
  .flags li > div {
    min-inline-size: 0;
  }
  .flags strong {
    font-weight: 600;
  }
  .flag-doc {
    margin-inline-start: 6px;
    font: 500 0.8125rem var(--font-mono);
  }
  .flags p {
    margin: 2px 0 0;
    font-size: 0.875rem;
    color: var(--ink-2);
    overflow-wrap: anywhere;
  }
  .next {
    margin: 16px 0 0;
    padding-block-start: 12px;
    border-block-start: 1px solid var(--rule);
    font-size: 0.9375rem;
  }
  .next .label {
    color: var(--ink-3);
  }
  footer {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 16px;
    margin-block-start: 12px;
    font-size: 0.8125rem;
    color: var(--ink-3);
  }
  footer span {
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }
  @media (max-width: 480px) {
    .sheet {
      padding: 16px 14px 12px;
    }
  }
</style>
