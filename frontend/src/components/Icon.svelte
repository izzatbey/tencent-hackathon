<script lang="ts" module>
  // Phosphor Icons (MIT), diambil saat build sebagai SVG mentah: hanya ikon
  // yang dipakai yang ikut ke bundle.
  import sealCheck from '@phosphor-icons/core/assets/regular/seal-check.svg?raw'
  import question from '@phosphor-icons/core/assets/regular/question.svg?raw'
  import prohibit from '@phosphor-icons/core/assets/regular/prohibit.svg?raw'
  import warning from '@phosphor-icons/core/assets/regular/warning.svg?raw'
  import gitDiff from '@phosphor-icons/core/assets/regular/git-diff.svg?raw'
  import userCircle from '@phosphor-icons/core/assets/regular/user-circle.svg?raw'
  import send from '@phosphor-icons/core/assets/regular/paper-plane-tilt.svg?raw'
  import retry from '@phosphor-icons/core/assets/regular/arrow-clockwise.svg?raw'
  import eyeSlash from '@phosphor-icons/core/assets/regular/eye-slash.svg?raw'
  import shield from '@phosphor-icons/core/assets/regular/shield-check.svg?raw'
  import idCard from '@phosphor-icons/core/assets/regular/identification-card.svg?raw'

  const ICONS = { sealCheck, question, prohibit, warning, gitDiff, userCircle, send, retry,
    eyeSlash, shield, idCard }
  export type IconName = keyof typeof ICONS
</script>

<script lang="ts">
  let { name, size = 20 }: { name: IconName; size?: number } = $props()
</script>

<span class="icon" aria-hidden="true" style:--size="{size}px">{@html ICONS[name]}</span>

<style>
  .icon {
    display: inline-flex;
    inline-size: var(--size);
    block-size: var(--size);
    flex: none;
  }
  .icon :global(svg) {
    inline-size: 100%;
    block-size: 100%;
  }
</style>
