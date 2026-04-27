<template>
  <div class="drawing-editor-container">
    <div class="excalidraw-wrapper" v-if="initialData">
       <ExcalidrawComponent
         :initialData="initialData"
         @onChange="handleChange"
         theme="dark"
         :UIOptions="uiOptions"
       />
    </div>

    <!-- Discrete Top-Right Close Button -->
    <button class="btn-close-drawing" @click="handleBack" title="Close and return to note">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <path d="M18 6L6 18M6 6l12 12" />
      </svg>
    </button>

    <!-- Tiny Bottom-Right Status Indicator -->
    <div class="drawing-status-floating" :class="{ saving }">
       <div class="status-dot"></div>
       <span>{{ saving ? 'Saving...' : 'Saved' }}</span>
    </div>

    <div v-if="!initialData" class="loading-drawing">
       <div class="loader"></div>
       Initializing Canvas...
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Excalidraw } from '@excalidraw/excalidraw'
import "@excalidraw/excalidraw/index.css"
import { applyReactInVue } from 'veaury'
import { useNotesStore } from '../stores/notes'

const ExcalidrawComponent = applyReactInVue(Excalidraw)

const props = defineProps({
  note: Object
})

const emit = defineEmits(['close'])

const notesStore = useNotesStore()
const saving = ref(false)
const initialData = ref(null)
let saveTimeout = null

const uiOptions = {
  canvasActions: {
    toggleTheme: true,
    export: {
      saveFileToDisk: true
    }
  }
}

onMounted(() => {
  try {
    const contentStr = props.note.content?.trim()
    const parsed = (contentStr && contentStr !== '{}') ? JSON.parse(contentStr) : { elements: [], appState: {}, files: {} }
    
    initialData.value = {
      elements: parsed.elements || [],
      appState: { 
        ...parsed.appState,
        theme: 'dark',
        viewBackgroundColor: parsed.appState?.viewBackgroundColor || '#121212'
      },
      files: parsed.files || {}
    }
  } catch (e) {
    console.error('Failed to parse drawing content:', e)
    initialData.value = { 
      elements: [],
      appState: { theme: 'dark', viewBackgroundColor: '#121212' }
    }
  }
})

let lastExport = null

function handleChange(elements, appState, files) {
  if (!initialData.value) return
  lastExport = { elements, appState, files }
  
  if (saveTimeout) clearTimeout(saveTimeout)
  
  saveTimeout = setTimeout(async () => {
    await performSave()
  }, 1500)
}

async function performSave() {
  if (!lastExport) return
  saving.value = true
  const { elements, appState, files } = lastExport
  const content = JSON.stringify({ 
    elements, 
    appState: { 
      theme: appState.theme, 
      viewBackgroundColor: appState.viewBackgroundColor 
    }, 
    files 
  })
  // We must update the note object in the store too
  props.note.content = content
  await notesStore.updateNote(props.note.id, content)
  saving.value = false
  if (saveTimeout) {
    clearTimeout(saveTimeout)
    saveTimeout = null
  }
}

async function handleBack() {
  // If there's a pending save, do it now before exiting
  if (saveTimeout) {
    await performSave()
  }
  emit('close')
}
</script>

<style scoped>
.drawing-editor-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #121212;
  position: relative;
}

.excalidraw-wrapper {
  flex: 1;
  position: relative;
  height: 100%;
}

.btn-close-drawing {
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

.btn-close-drawing:hover {
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

.loading-drawing {
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

:deep(.excalidraw) {
  height: 100% !important;
  width: 100% !important;
}
</style>
