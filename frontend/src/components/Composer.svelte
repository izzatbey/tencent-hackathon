<script lang="ts">
  import { MAX_QUESTION } from '../lib/api'
  import Icon from './Icon.svelte'

  let {
    busy = false,
    onsubmit,
    value = $bindable(''),
  }: { busy?: boolean; onsubmit: (question: string) => void; value?: string } = $props()

  let textarea: HTMLTextAreaElement | undefined = $state()
  const trimmed = $derived(value.trim())
  const nearLimit = $derived(value.length > MAX_QUESTION - 200)
  const canSend = $derived(!busy && trimmed.length > 0 && value.length <= MAX_QUESTION)

  function send() {
    if (!canSend) return
    onsubmit(trimmed)
    value = ''
  }

  function onkeydown(event: KeyboardEvent) {
    // Enter mengirim, Shift+Enter baris baru. Saat IME masih menyusun kata, Enter milik IME.
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
      event.preventDefault()
      send()
    }
  }

  export function focus() {
    textarea?.focus()
  }
</script>

<form
  class="composer"
  onsubmit={(e) => {
    e.preventDefault()
    send()
  }}
>
  <label for="question" class="visually-hidden">Pertanyaan</label>
  <textarea
    id="question"
    bind:this={textarea}
    bind:value
    {onkeydown}
    rows="2"
    maxlength={MAX_QUESTION}
    placeholder="Contoh: Boleh buka port 22 dari internet ke db-hr-jkt-01?"
    aria-describedby="composer-hint"
  ></textarea>
  <div class="bar">
    <p id="composer-hint" class="hint">
      NIK dan nomor HP disamarkan otomatis. Enter untuk kirim, Shift+Enter untuk baris baru.
    </p>
    {#if nearLimit}
      <span class="count" aria-live="polite">{value.length}/{MAX_QUESTION}</span>
    {/if}
    <button type="submit" disabled={!canSend}>
      <Icon name="send" size={20} />
      <span>Tanya</span>
    </button>
  </div>
</form>

<style>
  .composer {
    background: var(--sheet);
    border: 1px solid var(--rule-strong);
    border-radius: var(--r-sheet);
    padding: 10px 10px 8px 14px;
    transition: border-color 160ms var(--ease-out);
  }
  .composer:focus-within {
    border-color: var(--accent);
  }
  textarea {
    display: block;
    inline-size: 100%;
    min-block-size: 3.2em;
    max-block-size: 40vh;
    field-sizing: content;
    resize: none;
    border: 0;
    padding: 4px 0;
    background: transparent;
    line-height: 1.5;
  }
  textarea:focus-visible {
    outline: none;
  }
  textarea::placeholder {
    color: var(--ink-3);
  }
  .bar {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-block-start: 6px;
  }
  .hint {
    flex: 1;
    margin: 0;
    font-size: 0.75rem;
    color: var(--ink-3);
  }
  .count {
    font: 0.75rem var(--font-mono);
    color: var(--warn);
  }
  button {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-block-size: 44px;
    padding: 0 16px;
    border: 0;
    border-radius: var(--r-control);
    background: var(--accent);
    color: var(--sheet);
    font-weight: 600;
    cursor: pointer;
    transition: opacity 160ms var(--ease-out);
  }
  button:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
  button:not(:disabled):active {
    transform: translateY(1px);
  }
  @media (max-width: 480px) {
    /* disembunyikan secara visual saja: tetap jadi deskripsi isian untuk pembaca layar */
    .hint {
      position: absolute;
      inline-size: 1px;
      block-size: 1px;
      overflow: hidden;
      clip-path: inset(50%);
    }
    .bar {
      justify-content: flex-end;
    }
  }
</style>
