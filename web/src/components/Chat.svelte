<script>
  import { messages } from '../lib/socket.js'
  import { afterUpdate } from 'svelte'

  let chatEl

  afterUpdate(() => {
    if (chatEl) chatEl.scrollTop = chatEl.scrollHeight
  })

  function renderText(text) {
    return text
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/`(.+?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>')
  }

  const typeLabel = {
    user:      'Вы',
    assistant: 'Агент',
    system:    'Система',
    error:     'Ошибка',
    review:    'Ревью',
    result:    'Результат',
  }
</script>

<div class="chat" bind:this={chatEl}>
  {#each $messages as msg (msg.id)}
    <div class="msg msg-{msg.type}">
      <span class="role">
        {typeLabel[msg.type] ?? msg.type}
        {#if msg.payload?.workflow && msg.type === 'result'}
          <span class="workflow-tag">{msg.payload.workflow}</span>
        {/if}
      </span>
      <div class="body">{@html renderText(msg.text)}</div>
    </div>
  {/each}

  {#if $messages.length === 0}
    <div class="empty">
      Напишите задачу или нажмите <strong>+ Новый</strong> для настройки.<br>
      Примеры: <code>project /path/to/project</code>, <code>resume</code>, <code>проанализируй проект</code>
    </div>
  {/if}
</div>

<style>
  .chat {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: .75rem;
  }

  .msg {
    display: flex;
    flex-direction: column;
    gap: .25rem;
    max-width: 82%;
  }
  .msg-user      { align-self: flex-end; }
  .msg-assistant, .msg-review, .msg-result { align-self: flex-start; }
  .msg-system, .msg-error { align-self: center; max-width: 100%; }

  .role {
    font-size: .68rem;
    text-transform: uppercase;
    letter-spacing: .07em;
    color: #6c7086;
    display: flex;
    align-items: center;
    gap: .4rem;
  }
  .msg-user .role      { text-align: right; color: #89b4fa; }
  .msg-error .role     { color: #f38ba8; }
  .msg-review .role    { color: #f9e2af; }
  .msg-result .role    { color: #a6e3a1; }

  .workflow-tag {
    font-size: .6rem;
    background: #313244;
    padding: 1px 5px;
    border-radius: 3px;
    color: #89b4fa;
  }

  .body {
    padding: .55rem .85rem;
    border-radius: 10px;
    font-size: .9rem;
    line-height: 1.55;
    word-break: break-word;
  }
  .msg-user      .body { background: #313244; color: #cdd6f4; border-bottom-right-radius: 3px; }
  .msg-assistant .body { background: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; border-bottom-left-radius: 3px; }
  .msg-result    .body { background: #1e2e1e; color: #cdd6f4; border: 1px solid #2e4a2e; border-bottom-left-radius: 3px; }
  .msg-system    .body { background: transparent; color: #45475a; font-size: .8rem; text-align: center; }
  .msg-error     .body { background: #2d1b20; color: #f38ba8; border: 1px solid #f38ba8; }
  .msg-review    .body { background: #2d2010; color: #f9e2af; border: 1px solid #f9e2af; }

  :global(.body code) {
    background: #181825;
    padding: .1rem .35rem;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: .82em;
  }
  :global(.body strong) { font-weight: 700; color: #cba6f7; }

  .empty {
    color: #45475a;
    text-align: center;
    margin: auto;
    font-size: .88rem;
    line-height: 2;
  }
  .empty code {
    background: #181825;
    padding: .1rem .4rem;
    border-radius: 4px;
    font-size: .82em;
    color: #89b4fa;
  }
</style>
