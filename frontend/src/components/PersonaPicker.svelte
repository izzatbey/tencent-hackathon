<script lang="ts">
  import type { Persona } from '../lib/types'
  import Icon from './Icon.svelte'

  let {
    personas,
    selected = $bindable(null),
    disabled = false,
  }: { personas: Persona[]; selected?: Persona | null; disabled?: boolean } = $props()

  // Nilai <select> = indeks persona; "" = tamu tanpa identitas.
  let index = $state('')
  $effect(() => {
    selected = index === '' ? null : (personas[Number(index)] ?? null)
  })
</script>

<div class="picker">
  <Icon name="userCircle" size={20} />
  <label for="persona">Bertanya sebagai</label>
  <select id="persona" bind:value={index} {disabled}>
    <option value="">Tamu (tanpa identitas)</option>
    {#each personas as p, i (p.user)}
      <option value={String(i)}>{p.user}, {p.role}</option>
    {/each}
  </select>
</div>

<style>
  .picker {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--ink-2);
    font-size: 0.875rem;
    min-inline-size: 0;
  }
  label {
    white-space: nowrap;
  }
  select {
    min-inline-size: 0;
    max-inline-size: 16rem;
    min-block-size: 44px;
    padding: 0 30px 0 10px;
    border: 1px solid var(--rule-strong);
    border-radius: var(--r-control);
    background: var(--sheet);
    color: var(--ink);
    text-overflow: ellipsis;
  }
  @media (max-width: 560px) {
    label {
      position: absolute;
      inline-size: 1px;
      block-size: 1px;
      overflow: hidden;
      clip-path: inset(50%);
    }
    select {
      max-inline-size: 100%;
    }
  }
</style>
