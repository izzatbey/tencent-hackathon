<script lang="ts">
  import { onMount, tick } from 'svelte'
  import { ask, loadPersonas, ApiError } from './lib/api'
  import type { AskResponse, Persona } from './lib/types'
  import { personaLabel } from './lib/labels'
  import AnswerSheet from './components/AnswerSheet.svelte'
  import Composer from './components/Composer.svelte'
  import PersonaPicker from './components/PersonaPicker.svelte'
  import Icon from './components/Icon.svelte'

  type Turn = {
    id: number
    persona: Persona | null
    // Teks mentah hanya disimpan di memori untuk "Coba lagi"; tidak pernah
    // ditampilkan atau ditulis ke storage, karena bisa memuat NIK/nomor HP.
    question: string
    state: 'pending' | 'done' | 'error'
    response?: AskResponse
    error?: string
  }

  const EXAMPLES = [
    'Boleh buka port 22 dari internet ke db-hr-jkt-01?',
    'Boleh remote ke firewall Makassar dari rumah?',
    'Siapa owner Proyek Garuda?',
    'Boleh bawa hewan peliharaan ke kantor?',
  ]

  let personas: Persona[] = $state([])
  let personasError = $state(false)
  let persona: Persona | null = $state(null)
  let turns: Turn[] = $state([])
  let draft = $state('')
  let nextId = 0
  let composer: Composer | undefined = $state()

  const busy = $derived(turns.some((t) => t.state === 'pending'))

  onMount(async () => {
    try {
      personas = await loadPersonas()
    } catch {
      personasError = true
    }
  })

  async function run(turn: Turn) {
    turn.state = 'pending'
    turn.error = undefined
    try {
      turn.response = await ask(turn.question, turn.persona)
      turn.state = 'done'
    } catch (err) {
      turn.error = err instanceof ApiError ? err.message : 'Terjadi kesalahan yang tidak terduga.'
      turn.state = 'error'
    }
    await tick()
    composer?.focus()
  }

  async function submit(question: string) {
    if (busy) return
    turns.push({ id: nextId++, persona, question, state: 'pending' })
    const turn = turns[turns.length - 1]
    await tick()
    document.getElementById(`turn-${turn.id}`)?.scrollIntoView({ block: 'start', behavior: 'smooth' })
    await run(turn)
  }

  function questionShown(turn: Turn): string | null {
    return turn.response ? turn.response.question_masked : null
  }
</script>

<svelte:head>
  <title>SecuritySahabat</title>
</svelte:head>

<header class="topbar">
  <div class="brand">
    <Icon name="shield" size={22} />
    <span class="name">SecuritySahabat</span>
  </div>
  <PersonaPicker {personas} bind:selected={persona} disabled={busy} />
</header>

<main>
  {#if personasError}
    <p class="notice" role="status">
      Daftar persona tidak bisa dimuat. Anda tetap bisa bertanya sebagai tamu.
    </p>
  {/if}

  {#if turns.length > 0}
    <h1 class="visually-hidden">SecuritySahabat</h1>
  {/if}
  <h2 class="visually-hidden">Percakapan</h2>

  {#if turns.length === 0}
    <section class="intro">
      <h1>Tanya boleh atau tidak. Dapat jawaban dengan bukti.</h1>
      <p>
        Setiap jawaban mengutip SOP, kontrol, atau dokumen topologi apa adanya, hanya dari dokumen
        yang boleh Anda lihat. Kalau buktinya tidak ada, jawabannya "tidak tahu" beserta orang yang
        bisa ditanya. Setiap pertanyaan dicatat dengan nomor catatan.
      </p>
      <h2>Coba salah satu</h2>
      <ul class="examples">
        {#each EXAMPLES as example (example)}
          <li>
            <button type="button" onclick={() => (draft = example)}>
              {example}
            </button>
          </li>
        {/each}
      </ul>
    </section>
  {/if}

  <ol class="thread" aria-label="Percakapan">
    {#each turns as turn (turn.id)}
      <li id="turn-{turn.id}" class="turn">
        <div class="ask">
          <span class="asker">{personaLabel(turn.persona ?? { user: null, role: null })}</span>
          {#if turn.state === 'pending'}
            <p class="bubble muted">Pertanyaan terkirim, data pribadi sedang disamarkan.</p>
          {:else if turn.state === 'error'}
            <p class="bubble muted">Pertanyaan belum terjawab.</p>
          {:else if questionShown(turn)}
            <p class="bubble">{questionShown(turn)}</p>
          {:else}
            <p class="bubble muted">Pertanyaan tidak ditampilkan karena berisi perintah ke sistem.</p>
          {/if}
        </div>

        <div aria-live="polite" aria-busy={turn.state === 'pending'}>
          {#if turn.state === 'pending'}
            <div class="skeleton" role="status">
              <span class="visually-hidden">Mencari bukti…</span>
              <span class="bar w30"></span>
              <span class="bar w90"></span>
              <span class="bar w70"></span>
              <span class="bar w80"></span>
            </div>
          {:else if turn.state === 'error'}
            <div class="error" role="alert">
              <Icon name="warning" size={20} />
              <p>{turn.error}</p>
              <button type="button" onclick={() => run(turn)} disabled={busy}>
                <Icon name="retry" size={18} />
                Coba lagi
              </button>
            </div>
          {:else if turn.response}
            <AnswerSheet response={turn.response} />
          {/if}
        </div>
      </li>
    {/each}
  </ol>
</main>

<div class="dock">
  <div class="dock-inner">
    <Composer bind:this={composer} bind:value={draft} {busy} onsubmit={submit} />
  </div>
</div>

<style>
  .topbar {
    position: sticky;
    top: 0;
    z-index: 2;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 10px max(16px, calc((100vw - 760px) / 2));
    background: color-mix(in srgb, var(--surface) 86%, transparent);
    backdrop-filter: saturate(1.4) blur(14px);
    border-block-end: 1px solid var(--rule);
  }
  @media (max-width: 560px) {
    .topbar {
      flex-wrap: wrap;
      row-gap: 8px;
    }
    .topbar > :global(.picker) {
      flex: 1 1 100%;
    }
    .topbar > :global(.picker select) {
      flex: 1;
    }
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--accent);
    flex: none;
  }
  .name {
    font: 600 1.125rem/1 var(--font-serif);
    color: var(--ink);
  }
  main {
    max-inline-size: 760px;
    margin: 0 auto;
    padding: 24px 16px 200px;
  }
  .notice {
    margin: 0 0 16px;
    padding: 10px 12px;
    border-radius: var(--r-control);
    background: var(--warn-soft);
    color: var(--warn);
    font-size: 0.875rem;
  }
  .intro h1 {
    margin: 24px 0 12px;
    font: 600 clamp(1.75rem, 1.2rem + 2.4vw, 2.5rem) / 1.15 var(--font-serif);
    font-optical-sizing: auto;
    letter-spacing: -0.01em;
    text-wrap: balance;
  }
  .intro p {
    margin: 0;
    max-inline-size: 60ch;
    color: var(--ink-2);
    text-wrap: pretty;
  }
  .intro h2 {
    margin: 28px 0 8px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--ink-3);
  }
  .examples {
    list-style: none;
    margin: 0;
    padding: 0;
    border: 1px solid var(--rule);
    border-radius: var(--r-sheet);
    background: var(--sheet);
    overflow: hidden;
  }
  .examples li + li {
    border-block-start: 1px solid var(--rule);
  }
  .examples button {
    display: block;
    inline-size: 100%;
    min-block-size: 48px;
    padding: 12px 16px;
    border: 0;
    background: transparent;
    text-align: start;
    cursor: pointer;
  }
  .examples button:hover {
    background: var(--accent-soft);
  }
  .thread {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 28px;
  }
  .turn {
    display: grid;
    gap: 10px;
    scroll-margin-block-start: 80px;
  }
  .ask {
    display: grid;
    justify-items: end;
    gap: 4px;
  }
  .asker {
    font-size: 0.75rem;
    color: var(--ink-3);
  }
  .bubble {
    margin: 0;
    max-inline-size: min(560px, 92%);
    padding: 10px 14px;
    border-radius: 18px 18px 6px 18px;
    background: var(--unknown-soft);
    overflow-wrap: anywhere;
    white-space: pre-line;
  }
  .bubble.muted {
    color: var(--ink-3);
    font-style: italic;
  }
  .skeleton {
    display: grid;
    gap: 10px;
    padding: 20px;
    border: 1px solid var(--rule);
    border-radius: var(--r-sheet);
    background: var(--sheet);
  }
  .skeleton .bar {
    display: block;
    block-size: 12px;
    border-radius: 4px;
    background: linear-gradient(90deg, var(--unknown-soft), var(--rule), var(--unknown-soft));
    background-size: 200% 100%;
    animation: shimmer 1.3s linear infinite;
  }
  .w30 {
    inline-size: 30%;
  }
  .w70 {
    inline-size: 70%;
  }
  .w80 {
    inline-size: 80%;
  }
  .w90 {
    inline-size: 90%;
  }
  @keyframes shimmer {
    to {
      background-position: -200% 0;
    }
  }
  .error {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
    padding: 14px 16px;
    border-radius: var(--r-sheet);
    background: var(--deny-soft);
    color: var(--deny);
  }
  .error p {
    flex: 1;
    margin: 0;
    min-inline-size: 12rem;
  }
  .error button {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-block-size: 44px;
    padding: 0 14px;
    border: 1px solid currentColor;
    border-radius: var(--r-control);
    background: transparent;
    cursor: pointer;
  }
  .dock {
    position: fixed;
    inset-inline: 0;
    inset-block-end: 0;
    padding: 12px 16px max(12px, env(safe-area-inset-bottom));
    background: linear-gradient(to top, var(--surface) 70%, transparent);
  }
  .dock-inner {
    max-inline-size: 760px;
    margin: 0 auto;
  }
</style>
