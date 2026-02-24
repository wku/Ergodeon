<script>
  import { sendInput, connected } from '../lib/socket.js'

  let text = ''
  let inputEl

  const COMMANDS = [
    { cmd: 'project',  hint: 'project /path - открыть проект' },
    { cmd: 'resume',   hint: 'resume - продолжить прерванный пайплайн' },
    { cmd: 'analyze',  hint: 'analyze - проанализировать проект' },
    { cmd: 'reset',    hint: 'reset - сбросить контекст' },
  ]

  let suggestions = []

  function onInput() {
    const val = text.trim().toLowerCase()
    if (val.startsWith('/') || val.length < 1) {
      suggestions = []
      return
    }
    suggestions = COMMANDS.filter(c => c.cmd.startsWith(val) && c.cmd !== val)
  }

  function applySuggestion(cmd) {
    text = cmd + ' '
    suggestions = []
    inputEl?.focus()
  }

  function submit() {
    const val = text.trim()
    if (!val || !$connected) return
    sendInput(val)
    text = ''
    suggestions = []
  }

  function onKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
    if (e.key === 'Escape') {
      suggestions = []
    }
  }
</script>

<div class="input-area">
  {#if suggestions.length}
    <div class="suggestions">
      {#each suggestions as s}
        <button class="sug-item" on:click={() => applySuggestion(s.cmd)}>
          <code>{s.cmd}</code>
          <span>{s.hint}</span>
        </button>
      {/each}
    </div>
  {/if}

  <div class="row">
    <textarea
      bind:this={inputEl}
      bind:value={text}
      on:input={onInput}
      on:keydown={onKeydown}
      placeholder={$connected ? 'Напишите задачу или команду...' : 'Нет соединения с сервером'}
      disabled={!$connected}
      rows="1"
    ></textarea>
    <button on:click={submit} disabled={!$connected || !text.trim()}>
      Отправить
    </button>
  </div>
</div>

<style>
  .input-area {
    padding: .6rem 1rem;
    border-top: 1px solid #313244;
    background: #1e1e2e;
    position: relative;
  }

  .suggestions {
    position: absolute;
    bottom: 100%;
    left: 1rem;
    right: 1rem;
    background: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    overflow: hidden;
    z-index: 10;
  }
  .sug-item {
    display: flex;
    align-items: center;
    gap: .75rem;
    padding: .4rem .75rem;
    cursor: pointer;
    font-size: .82rem;
    color: #bac2de;
    background: none;
    border: none;
    width: 100%;
    text-align: left;
  }
  .sug-item:hover { background: #313244; }
  .sug-item code {
    color: #89b4fa;
    background: #1e1e2e;
    padding: .1rem .35rem;
    border-radius: 4px;
    font-size: .8rem;
    min-width: 60px;
  }
  .sug-item span { color: #6c7086; }

  .row {
    display: flex;
    gap: .5rem;
    align-items: flex-end;
  }

  textarea {
    flex: 1;
    background: #181825;
    border: 1px solid #313244;
    border-radius: 8px;
    color: #cdd6f4;
    font-size: .9rem;
    padding: .55rem .75rem;
    resize: none;
    line-height: 1.5;
    font-family: inherit;
    max-height: 160px;
    overflow-y: auto;
    field-sizing: content;
  }
  textarea:focus {
    outline: none;
    border-color: #89b4fa;
  }
  textarea::placeholder { color: #45475a; }
  textarea:disabled { opacity: .4; cursor: not-allowed; }

  button {
    background: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 8px;
    padding: .55rem 1.1rem;
    font-weight: 700;
    font-size: .88rem;
    cursor: pointer;
    flex-shrink: 0;
    align-self: flex-end;
  }
  button:hover:not(:disabled) { background: #74c7ec; }
  button:disabled { opacity: .4; cursor: not-allowed; }
</style>
