<template>
  <div class="lorien-editor-container">
    <iframe
      v-if="bundleUrl"
      ref="lorienIframe"
      :src="bundleUrl"
      class="lorien-iframe"
      allow="display-capture"
    ></iframe>

    <!-- Close Button -->
    <button class="btn-close-lorien" @click="handleBack" title="Close and return to note">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <path d="M18 6L6 18M6 6l12 12" />
      </svg>
    </button>

    <!-- Status Indicator -->
    <div class="drawing-status-floating" :class="{ saving }">
       <div class="status-dot"></div>
       <span>{{ saving ? 'Saving...' : 'Saved (Local)' }}</span>
    </div>

    <div v-if="!bundleUrl" class="loading-lorien">
       <div class="loader"></div>
       Loading Lorien...
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useNotesStore } from '../stores/notes'

const props = defineProps({
  note: Object
})

const emit = defineEmits(['close'])

const notesStore = useNotesStore()
const saving = ref(false)
const lorienIframe = ref(null)

const bundleUrl = computed(() => {
  const host = window.location.hostname || '127.0.0.1'
  const port = 8000
  return `http://${host}:${port}/lorien/index.html?v=${Date.now()}`
})

// Lorien communication logic
// Note: This depends on Lorien having a JS bridge for postMessage.
// For now, this is a placeholder for the integration strategy.
// Since Lorien HTML5 export might not have a built-in "save to parent" API,
// we might need to patch its index.html or use local storage sync if it supports it.

onMounted(() => {
  window.addEventListener('message', handleMessage)
})

watch(() => props.note.id, () => {
  // If we're already mounted and the note changes, we might need to re-init
  // but usually the :key on the component handles this. 
  // Just in case, we can try to send data if the iframe is already ready.
}, { immediate: true })

function sendInitialData() {
  const iframe = lorienIframe.value
  if (iframe && iframe.contentWindow && props.note.content) {
    try {
      const content = props.note.content.trim()
      if (!content || content === '{}') {
        // Send empty strokes to clear the canvas if new/empty
        iframe.contentWindow.postMessage({
          type: 'LORIEN_INIT',
          payload: { strokes: [] }
        }, '*')
        return
      }
      
      const parsed = JSON.parse(content)
      console.log('Zenith: Sending LORIEN_INIT to iframe', props.note.id)
      iframe.contentWindow.postMessage({
        type: 'LORIEN_INIT',
        payload: parsed
      }, '*')
    } catch (e) {
      console.warn('Could not parse Lorien content for init:', e)
    }
  }
}

onBeforeUnmount(() => {
  window.removeEventListener('message', handleMessage)
})

function handleMessage(event) {
  // Security check: only allow messages from our backend
  if (!event.origin.includes(':8000')) return

  if (event.data.type === 'LORIEN_READY') {
    sendInitialData()
  } else if (event.data.type === 'LORIEN_SAVE') {
    saveData(event.data.payload)
  }
}

async function saveData(data) {
  saving.value = true
  const content = typeof data === 'string' ? data : JSON.stringify(data)
  // Update local object immediately so if we switch away and back, we have it
  props.note.content = content
  await notesStore.updateNote(props.note.id, content)
  saving.value = false
}

async function handleBack() {
  emit('close')
}
</script>

<style scoped>
.lorien-editor-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #21252b;
  position: relative;
}

.lorien-iframe {
  flex: 1;
  width: 100%;
  height: 100%;
  border: none;
}

.btn-close-lorien {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(40, 40, 40, 0.6);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  color: #888;
  cursor: pointer;
  transition: all 0.2s ease;
  z-index: 100;
}

.btn-close-lorien:hover {
  background: #e11d48;
  color: white;
  transform: rotate(90deg);
  border-color: #e11d48;
}

.drawing-status-floating {
  position: absolute;
  bottom: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(30, 30, 30, 0.4);
  backdrop-filter: blur(4px);
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.65rem;
  color: #666;
  pointer-events: none;
  z-index: 100;
  border: 1px solid rgba(255,255,255,0.05);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #22c55e;
}

.drawing-status-floating.saving {
  color: #6366f1;
}

.drawing-status-floating.saving .status-dot {
  background: #6366f1;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.4; }
  100% { opacity: 1; }
}

.loading-lorien {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #666;
}

.loader {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(255,255,255,0.05);
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
