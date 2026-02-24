import { io } from 'socket.io-client'
import { writable } from 'svelte/store'

export const EVT = {
  LOG:            'agent:log',
  TOOL_CALL:      'agent:tool_call',
  TOOL_RESULT:    'agent:tool_result',
  MESSAGE:        'agent:message',
  STATUS:         'agent:status',
  CONFIRM:        'agent:confirm',
  DONE:           'agent:done',
  ERROR:          'agent:error',
  INPUT:          'agent:input',
  CONFIRM_RESP:   'agent:confirm_response',
  COMMAND:        'agent:command',
}

export const PROJECT_TYPES = [
  { value: 'web-frontend',  label: 'Веб-фронтенд' },
  { value: 'backend-api',   label: 'Бэкенд API' },
  { value: 'fullstack',     label: 'Full-stack' },
  { value: 'mobile',        label: 'Мобайл' },
  { value: 'ml-data',       label: 'ML / Data' },
  { value: 'library',       label: 'Библиотека / SDK' },
  { value: 'other',         label: 'Другое' },
]

// Stores
export const connected      = writable(false)
export const messages       = writable([])
export const logs           = writable([])
export const status         = writable(null)
export const pendingConfirm = writable(null)
export const pipelineDone   = writable(null)
export const activeWorkflow = writable(null)
export const activeProject  = writable('')

let _socket = null
let _msgId = 0
const nextId = () => ++_msgId

function addMessage(type, text, payload) {
  messages.update(list => [...list, { id: nextId(), type, text, ts: Date.now(), payload }])
}

export function connect() {
  if (_socket) return _socket

  _socket = io({ path: '/socket.io', transports: ['websocket'] })

  _socket.on('connect', () => {
    connected.set(true)
    addMessage('system', 'Соединение установлено')
  })

  _socket.on('disconnect', () => {
    connected.set(false)
    activeWorkflow.set(null)
    addMessage('system', 'Соединение разорвано')
  })

  _socket.on(EVT.MESSAGE, (data) => {
    const text = data.text || ''
    const type = data.type || 'assistant'
    const payload = data.payload || null

    if (payload && payload.workflow) {
      activeWorkflow.set(payload.workflow)
      if (payload.workflow !== 'chat') {
        activeProject.set(payload.project || '')
      }
    }
    if (payload && payload.status === 'completed' && payload.workflow !== 'chat') {
      pipelineDone.set({ status: payload.status })
    }

    addMessage(type, text, payload)
  })

  _socket.on(EVT.LOG, (data) => {
    const msg = data.message || data.msg || ''
    const level = data.level || 'INFO'
    logs.update(list => {
      const next = [...list, { level, msg, ts: Date.now() }]
      return next.length > 500 ? next.slice(-500) : next
    })
  })

  _socket.on(EVT.TOOL_CALL, ({ tool, args }) => {
    logs.update(list => [...list, {
      level: 'TOOL',
      msg: `→ ${tool}  ${typeof args === 'string' ? args : JSON.stringify(args).slice(0, 120)}`,
      ts: Date.now(),
    }])
  })

  _socket.on(EVT.TOOL_RESULT, ({ tool, result }) => {
    logs.update(list => [...list, {
      level: 'TOOL',
      msg: `← ${tool}  ${String(result).slice(0, 120)}`,
      ts: Date.now(),
    }])
  })

  _socket.on(EVT.STATUS, data => {
    status.set({
      phase: data.phase || null,
      step: data.step || 0,
      total: data.total || 0,
      description: data.description || '',
      status: data.status || null,
    })
  })

  _socket.on(EVT.CONFIRM, data => pendingConfirm.set(data))

  _socket.on(EVT.DONE, data => {
    pipelineDone.set(data)
    status.set(null)
  })

  _socket.on(EVT.ERROR, (data) => {
    const msg = data.error || data.msg || 'неизвестная ошибка'
    addMessage('error', `Ошибка: ${msg}`)
  })

  return _socket
}

export function sendInput(text) {
  if (!_socket) return
  addMessage('user', text)
  _socket.emit(EVT.INPUT, { text })
}

export function sendConfirm(data, confirmed) {
  if (!_socket) return
  _socket.emit(EVT.CONFIRM_RESP, { response: confirmed ? 'yes' : 'no' })
  pendingConfirm.set(null)
}

export function sendCommand(command, data) {
  if (!_socket) return
  _socket.emit(EVT.COMMAND, { command, ...data })
}

export function clearMessages() {
  messages.set([])
  pipelineDone.set(null)
}

export function clearLogs() {
  logs.set([])
}
