<script>
  import { pendingConfirm, sendConfirm } from '../lib/socket.js'
</script>

{#if $pendingConfirm}
  <div class="overlay">
    <div class="dialog">
      <div class="dialog-header">
        {#if $pendingConfirm.type === 'review'}
          <span class="title">Ревью документов</span>
        {:else}
          <span class="title">Подтверждение операции</span>
        {/if}
      </div>

      <div class="message">{$pendingConfirm.message || ''}</div>

      {#if $pendingConfirm.tool}
        <div class="field">
          <span class="label">Инструмент</span>
          <code>{$pendingConfirm.tool}</code>
        </div>
      {/if}
      {#if $pendingConfirm.args}
        <div class="field">
          <span class="label">Аргументы</span>
          <code class="target">{$pendingConfirm.args}</code>
        </div>
      {/if}

      <div class="actions">
        <button class="btn-deny" on:click={() => sendConfirm($pendingConfirm, false)}>
          Отклонить
        </button>
        <button class="btn-allow" on:click={() => sendConfirm($pendingConfirm, true)}>
          {$pendingConfirm.type === 'review' ? 'Подтвердить' : 'Выполнить'}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,.55);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
  }
  .dialog {
    background: #1e1e2e;
    border: 1px solid #f38ba8;
    border-radius: 10px;
    padding: 1.5rem;
    min-width: 380px;
    max-width: 560px;
    display: flex;
    flex-direction: column;
    gap: .9rem;
  }
  .dialog-header {
    display: flex;
    align-items: center;
    gap: .5rem;
    font-size: 1.05rem;
    font-weight: 600;
    color: #f38ba8;
  }
  .message {
    color: #bac2de;
    font-size: .88rem;
    line-height: 1.5;
  }
  .field {
    display: flex;
    flex-direction: column;
    gap: .2rem;
  }
  .label {
    font-size: .7rem;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: #6c7086;
  }
  code {
    background: #181825;
    padding: .3rem .5rem;
    border-radius: 4px;
    font-size: .82rem;
    color: #cdd6f4;
    word-break: break-all;
  }
  .target { color: #fab387; }
  .actions {
    display: flex;
    justify-content: flex-end;
    gap: .75rem;
    margin-top: .3rem;
  }
  button {
    padding: .45rem 1.1rem;
    border: none;
    border-radius: 6px;
    font-size: .88rem;
    cursor: pointer;
    font-weight: 600;
  }
  .btn-deny  { background: #313244; color: #cdd6f4; }
  .btn-deny:hover  { background: #45475a; }
  .btn-allow { background: #f38ba8; color: #1e1e2e; }
  .btn-allow:hover { background: #eb6f7a; }
</style>
