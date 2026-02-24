<script>
  import { createEventDispatcher } from 'svelte'
  import { sendInput, PROJECT_TYPES } from '../lib/socket.js'

  export let show = false

  const dispatch = createEventDispatcher()

  let step = 'mode'
  let selectedMode = ''
  let selectedType = 'other'
  let pathInput = ''
  let taskInput = ''

  const modeLabels = {
    chat:     { label: 'Чат / Правки',       desc: 'Работа с кодом, вопросы, рефакторинг' },
    analyze:  { label: 'Анализ проекта',      desc: 'Изучить архитектуру, бизнес-логику, API' },
    research: { label: 'Ресёрч',              desc: 'Исследование технологий, документации' },
    build:    { label: 'Создание проекта',    desc: 'Создать новый проект с нуля по описанию' },
  }

  function selectMode(m) {
    selectedMode = m
    step = 'config'
    pathInput = selectedMode === 'build' ? 'projects/' : ''
    taskInput = ''
  }

  function back() {
    if (step === 'config') { step = 'mode'; selectedMode = ''; return }
  }

  function submit() {
    if (!pathInput.trim()) return

    // Set active project via text command
    sendInput(`project ${pathInput.trim()}`)

    // If there's a task description, send it as the main request
    if (taskInput.trim()) {
      setTimeout(() => sendInput(taskInput.trim()), 300)
    } else if (selectedMode === 'analyze') {
      setTimeout(() => sendInput('проанализируй проект'), 300)
    } else if (selectedMode === 'research') {
      setTimeout(() => sendInput('исследуй проект'), 300)
    }

    close()
  }

  function close() {
    show = false
    step = 'mode'
    selectedMode = ''
    dispatch('close')
  }

  function onKeydown(e) {
    if (e.key === 'Escape') close()
  }
</script>

<svelte:window on:keydown={onKeydown} />

{#if show}
  <div class="overlay" on:click|self={close} role="dialog" aria-modal="true">
    <div class="modal">

      <div class="modal-header">
        <span class="modal-title">
          {#if step === 'mode'}Новый сеанс{/if}
          {#if step === 'config'}{modeLabels[selectedMode]?.label}{/if}
        </span>
        <button class="close-btn" on:click={close}>✕</button>
      </div>

      {#if step === 'mode'}
        <div class="step-mode">
          <p class="hint">Выберите режим работы</p>
          <div class="mode-cards">
            {#each Object.entries(modeLabels) as [key, info]}
              <button class="mode-card" on:click={() => selectMode(key)}>
                <span class="mode-label">{info.label}</span>
                <span class="mode-desc">{info.desc}</span>
              </button>
            {/each}
          </div>
        </div>

      {:else if step === 'config'}
        <div class="step-config">
          {#if selectedMode === 'build'}
            <label class="field-label" for="type-select">Тип проекта</label>
            <select id="type-select" class="select" bind:value={selectedType}>
              {#each PROJECT_TYPES as pt}
                <option value={pt.value}>{pt.label}</option>
              {/each}
            </select>
          {/if}

          <label class="field-label" for="path-input">
            {selectedMode === 'build' ? 'Базовая директория' : 'Путь к проекту'}
          </label>
          <input
            id="path-input"
            class="input"
            bind:value={pathInput}
            placeholder={selectedMode === 'build' ? 'projects/' : '/path/to/project'}
            spellcheck="false"
          />

          <label class="field-label" for="task-input">
            {selectedMode === 'build' ? 'Описание задачи' : 'Запрос (необязательно)'}
          </label>
          <textarea
            id="task-input"
            class="textarea"
            bind:value={taskInput}
            rows="3"
            placeholder={selectedMode === 'build'
              ? 'Опишите что нужно создать...'
              : 'Что сделать с проектом...'}
          />

          <div class="actions">
            <button class="btn-secondary" on:click={back}>Назад</button>
            <button
              class="btn-primary"
              on:click={submit}
              disabled={!pathInput.trim() || (selectedMode === 'build' && !taskInput.trim())}
            >
              {selectedMode === 'build' ? 'Создать' : 'Открыть'}
            </button>
          </div>
        </div>
      {/if}

    </div>
  </div>
{/if}

<style>
  .overlay {
    position: fixed; inset: 0;
    background: rgba(0,0,0,.6);
    display: flex; align-items: center; justify-content: center;
    z-index: 200;
  }
  .modal {
    background: #1e1e2e;
    border: 1px solid #45475a;
    border-radius: 12px;
    width: 480px; max-width: 95vw;
    padding: 24px;
    display: flex; flex-direction: column; gap: 16px;
  }
  .modal-header {
    display: flex; justify-content: space-between; align-items: center;
  }
  .modal-title { font-size: 1.1rem; font-weight: 600; color: #cdd6f4; }
  .close-btn {
    background: none; border: none; color: #6c7086;
    cursor: pointer; font-size: 1rem; padding: 2px 6px;
  }
  .close-btn:hover { color: #cdd6f4; }

  .hint { color: #6c7086; font-size: .875rem; margin: 0; }

  .mode-cards { display: flex; flex-direction: column; gap: 10px; }
  .mode-card {
    background: #181825; border: 1px solid #313244;
    border-radius: 8px; padding: 14px 16px;
    text-align: left; cursor: pointer;
    display: flex; flex-direction: column; gap: 4px;
    transition: border-color .15s;
  }
  .mode-card:hover { border-color: #89b4fa; }
  .mode-label { color: #cdd6f4; font-weight: 500; font-size: .95rem; }
  .mode-desc  { color: #6c7086; font-size: .8rem; }

  .step-config { display: flex; flex-direction: column; gap: 10px; }

  .field-label { color: #a6adc8; font-size: .8rem; margin-bottom: 2px; }
  .select, .input {
    background: #181825; border: 1px solid #313244; border-radius: 6px;
    color: #cdd6f4; padding: 8px 10px; font-size: .9rem; width: 100%;
    box-sizing: border-box; outline: none;
  }
  .select:focus, .input:focus { border-color: #89b4fa; }
  .textarea {
    background: #181825; border: 1px solid #313244; border-radius: 6px;
    color: #cdd6f4; padding: 8px 10px; font-size: .9rem; width: 100%;
    box-sizing: border-box; outline: none; resize: vertical; font-family: inherit;
  }
  .textarea:focus { border-color: #89b4fa; }

  .actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 4px; }
  .btn-primary {
    background: #89b4fa; color: #1e1e2e; border: none;
    border-radius: 6px; padding: 8px 18px; font-size: .9rem;
    cursor: pointer; font-weight: 500;
  }
  .btn-primary:hover:not(:disabled) { background: #b4d0fb; }
  .btn-primary:disabled { opacity: .4; cursor: not-allowed; }
  .btn-secondary {
    background: transparent; color: #6c7086; border: 1px solid #313244;
    border-radius: 6px; padding: 8px 14px; font-size: .9rem; cursor: pointer;
  }
  .btn-secondary:hover { color: #cdd6f4; border-color: #45475a; }
</style>
