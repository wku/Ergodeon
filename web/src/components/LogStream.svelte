<script>
  import { logs, clearLogs } from '../lib/socket.js'
  import { afterUpdate } from 'svelte'

  let open = false
  let logEl

  afterUpdate(() => {
    if (open && logEl) logEl.scrollTop = logEl.scrollHeight
  })

  const levelColor = {
    INFO:    '#89b4fa',
    WARNING: '#f9e2af',
    ERROR:   '#f38ba8',
    TOOL:    '#a6e3a1',
    DEBUG:   '#6c7086',
  }
</script>

<div class="logstream" class:open>
  <div class="log-header" on:click={() => open = !open}>
    <span>Лог агента</span>
    <span class="count">{$logs.length}</span>
    <span class="arrow">{open ? '▼' : '▲'}</span>
    {#if open}
      <button class="clear-btn" on:click|stopPropagation={clearLogs}>очистить</button>
    {/if}
  </div>

  {#if open}
    <div class="log-body" bind:this={logEl}>
      {#each $logs as entry (entry.ts + entry.msg)}
        <div class="log-line">
          <span class="lvl" style="color:{levelColor[entry.level] || '#cdd6f4'}">
            {entry.level.padEnd(7)}
          </span>
          <span class="msg">{entry.msg}</span>
        </div>
      {/each}
      {#if $logs.length === 0}
        <div class="empty">логов нет</div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .logstream {
    border-top: 1px solid #313244;
    background: #11111b;
    flex-shrink: 0;
  }
  .log-header {
    display: flex;
    align-items: center;
    gap: .5rem;
    padding: .35rem .8rem;
    cursor: pointer;
    user-select: none;
    font-size: .75rem;
    color: #6c7086;
  }
  .log-header:hover { color: #cdd6f4; }
  .count {
    background: #313244;
    padding: .1rem .4rem;
    border-radius: 10px;
    font-size: .7rem;
  }
  .arrow { margin-left: auto; }
  .clear-btn {
    background: none;
    border: 1px solid #45475a;
    color: #6c7086;
    border-radius: 4px;
    padding: .1rem .5rem;
    font-size: .7rem;
    cursor: pointer;
  }
  .clear-btn:hover { color: #f38ba8; border-color: #f38ba8; }

  .log-body {
    height: 180px;
    overflow-y: auto;
    padding: .3rem .5rem;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: .72rem;
  }
  .log-line {
    display: flex;
    gap: .5rem;
    line-height: 1.5;
  }
  .lvl  { flex-shrink: 0; font-weight: 600; }
  .msg  { color: #bac2de; word-break: break-all; }
  .empty { color: #45475a; padding: .5rem; }
</style>
