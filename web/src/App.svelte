<script>
  import { onMount } from 'svelte'
  import { connect, clearMessages, activeWorkflow, activeProject, sendInput } from './lib/socket.js'
  import Chat from './components/Chat.svelte'
  import Input from './components/Input.svelte'
  import StatusBar from './components/StatusBar.svelte'
  import LogStream from './components/LogStream.svelte'
  import ConfirmDialog from './components/ConfirmDialog.svelte'
  import OnboardingModal from './components/OnboardingModal.svelte'

  let showOnboarding = false

  const workflowLabels = {
    build: 'Создание',
    modify: 'Правки',
    fix: 'Исправление',
    analyze: 'Анализ',
    research: 'Ресёрч',
    chat: 'Чат',
    resume: 'Продолжение',
  }

  onMount(() => {
    connect()
  })

  function resetSession() {
    sendInput('reset')
    clearMessages()
    showOnboarding = true
  }
</script>

<div class="app">
  <header>
    <span class="logo">Ergodeon</span>
    <span class="sub">autonomous code orchestration</span>

    {#if $activeWorkflow}
      <span class="mode-badge mode-{$activeWorkflow}">
        {workflowLabels[$activeWorkflow] || $activeWorkflow}
      </span>
    {/if}
    {#if $activeProject}
      <span class="path-badge" title={$activeProject}>
        {$activeProject.split('/').slice(-2).join('/')}
      </span>
    {/if}

    <div class="header-actions">
      <button class="new-btn" on:click={() => showOnboarding = true} title="Новый сеанс">
        + Новый
      </button>
      <button class="clear-btn" on:click={clearMessages} title="Очистить чат">✕</button>
    </div>
  </header>

  <StatusBar />
  <Chat />
  <LogStream />
  <Input />
  <ConfirmDialog />

  <OnboardingModal bind:show={showOnboarding} />
</div>

<style>
  :global(*, *::before, *::after) { box-sizing: border-box; margin: 0; padding: 0; }
  :global(body) {
    background: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    height: 100vh;
    overflow: hidden;
  }
  :global(html, body, #app) { height: 100%; }

  .app { display: flex; flex-direction: column; height: 100vh; }

  header {
    display: flex; align-items: center; gap: .6rem;
    padding: .5rem 1rem;
    background: #181825;
    border-bottom: 1px solid #313244;
    flex-shrink: 0;
  }
  .logo { font-weight: 700; font-size: 1rem; color: #cba6f7; letter-spacing: .04em; }
  .sub { font-size: .72rem; color: #45475a; }

  .mode-badge {
    font-size: .7rem; font-weight: 600; padding: 2px 8px;
    border-radius: 10px; text-transform: uppercase; letter-spacing: .06em;
  }
  .mode-chat     { background: #1e3a5f; color: #89b4fa; }
  .mode-build    { background: #1e3a2f; color: #a6e3a1; }
  .mode-modify   { background: #1e3a2f; color: #a6e3a1; }
  .mode-fix      { background: #3a1e1e; color: #f38ba8; }
  .mode-analyze  { background: #3a2f1e; color: #fab387; }
  .mode-research { background: #3a2f1e; color: #fab387; }
  .mode-resume   { background: #2f1e3a; color: #cba6f7; }

  .path-badge {
    font-size: .72rem; color: #6c7086;
    max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }

  .header-actions { margin-left: auto; display: flex; gap: .4rem; align-items: center; }

  .new-btn {
    background: #313244; border: none; color: #cdd6f4;
    font-size: .8rem; padding: .25rem .7rem;
    border-radius: 5px; cursor: pointer;
  }
  .new-btn:hover { background: #45475a; }

  .clear-btn {
    background: none; border: none; color: #45475a;
    font-size: .9rem; cursor: pointer;
    padding: .2rem .4rem; border-radius: 4px;
  }
  .clear-btn:hover { color: #f38ba8; background: #2d1b20; }
</style>
