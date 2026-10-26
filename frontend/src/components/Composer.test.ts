import { fireEvent, render, screen } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import Composer from './Composer.svelte'
import { MAX_QUESTION } from '../lib/api'

function setup(props: { busy?: boolean } = {}) {
  const onsubmit = vi.fn()
  render(Composer, { onsubmit, ...props })
  return {
    onsubmit,
    box: screen.getByLabelText('Pertanyaan') as HTMLTextAreaElement,
    button: screen.getByRole('button', { name: /Tanya/ }),
    user: userEvent.setup(),
  }
}

describe('Composer', () => {
  it('tombol mati selama isian kosong atau hanya spasi', async () => {
    const { box, button, user } = setup()
    expect(button).toBeDisabled()
    await user.type(box, '   ')
    expect(button).toBeDisabled()
  })

  it('Enter mengirim teks yang sudah dirapikan lalu mengosongkan isian', async () => {
    const { box, onsubmit, user } = setup()
    await user.type(box, '  boleh install Chrome?  {Enter}')
    expect(onsubmit).toHaveBeenCalledExactlyOnceWith('boleh install Chrome?')
    expect(box.value).toBe('')
  })

  it('Shift+Enter menambah baris, tidak mengirim', async () => {
    const { box, onsubmit, user } = setup()
    await user.type(box, 'baris satu{Shift>}{Enter}{/Shift}baris dua')
    expect(onsubmit).not.toHaveBeenCalled()
    expect(box.value).toBe('baris satu\nbaris dua')
  })

  it('Enter saat IME masih menyusun kata tidak mengirim', async () => {
    const { box, onsubmit, user } = setup()
    await user.type(box, 'kanji')
    await fireEvent.keyDown(box, { key: 'Enter', isComposing: true })
    expect(onsubmit).not.toHaveBeenCalled()
  })

  it('selama menunggu jawaban, kirim ulang tidak bisa', async () => {
    const { box, button, onsubmit, user } = setup({ busy: true })
    await user.type(box, 'pertanyaan{Enter}')
    expect(button).toBeDisabled()
    expect(onsubmit).not.toHaveBeenCalled()
  })

  it('klik ganda pada tombol hanya mengirim sekali', async () => {
    const { box, button, onsubmit, user } = setup()
    await user.type(box, 'pertanyaan')
    await user.dblClick(button)
    expect(onsubmit).toHaveBeenCalledTimes(1)
  })

  it('panjang dibatasi di 2000 karakter dan penghitung muncul menjelang batas', async () => {
    const { box } = setup()
    expect(box.maxLength).toBe(MAX_QUESTION)
    expect(screen.queryByText(/\/2000$/)).not.toBeInTheDocument()
    await fireEvent.input(box, { target: { value: 'a'.repeat(1801) } })
    expect(screen.getByText('1801/2000')).toBeInTheDocument()
  })

  it('isian punya label dan petunjuk untuk pembaca layar', () => {
    const { box } = setup()
    expect(box).toHaveAccessibleDescription(/disamarkan otomatis/)
  })
})
