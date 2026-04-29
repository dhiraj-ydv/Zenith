<template>
  <div class="excalidraw-preview" ref="container">
    <div v-if="loading" class="preview-loading">Rendering drawing...</div>
    <div v-else-if="error" class="preview-error">Failed to load preview</div>
    <div v-else-if="isEmpty" class="preview-empty" @click="$emit('edit')">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" opacity="0.4"><path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/><path d="M2 2l5 2"/><path d="M2 2l2 5"/></svg>
      <span>Empty Drawing. Click to edit.</span>
    </div>
    <div v-else class="preview-canvas" ref="canvasContainer" @click="$emit('edit')"></div>
  </div>
</template>

<script setup>
import { nextTick, ref, onMounted, watch } from 'vue'
import { exportToSvg } from '@excalidraw/excalidraw'
import { notesApi } from '../api/client'

const props = defineProps({
  content: String,
  name: String
})

const emit = defineEmits(['edit'])

const container = ref(null)
const canvasContainer = ref(null)
const loading = ref(true)
const error = ref(false)
const isEmpty = ref(false)
let renderSeq = 0

async function renderPreview() {
  const currentRender = ++renderSeq
  try {
    loading.value = true
    error.value = false
    
    let drawingContent = props.content
    
    // If content is missing or just the default empty object, try to fetch it
    if (!drawingContent || drawingContent === '{}') {
       try {
         const { data } = await notesApi.get(props.name)
         drawingContent = data.content
       } catch (err) {
         console.warn(`Could not fetch drawing ${props.name} for preview`, err)
       }
    }

    if (!drawingContent || drawingContent === '{}') {
      isEmpty.value = true
      loading.value = false
      return
    }

    const parsed = JSON.parse(drawingContent)
    if (!parsed.elements || parsed.elements.length === 0) {
      isEmpty.value = true
      loading.value = false
      return
    }

    const svg = await exportToSvg({
      elements: parsed.elements,
      appState: {
        ...parsed.appState,
        exportWithStyle: true,
        exportBackground: true,
      },
      files: parsed.files,
    })

    if (currentRender !== renderSeq) return

    loading.value = false
    await nextTick()

    if (currentRender !== renderSeq) return

    if (canvasContainer.value) {
      canvasContainer.value.innerHTML = ''
      svg.style.width = '100%'
      svg.style.height = 'auto'
      svg.style.maxWidth = '100%'
      canvasContainer.value.appendChild(svg)
    }
  } catch (e) {
    console.error('Failed to render Excalidraw preview:', e)
    error.value = true
    loading.value = false
  }
}

onMounted(renderPreview)
watch(() => [props.content, props.name], renderPreview)
</script>

<style scoped>
.excalidraw-preview {
  width: 100%;
  min-height: 50px;
}
.preview-canvas {
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
  background: white; /* Excalidraw usually looks best on white or its own bg */
}
.preview-loading, .preview-error, .preview-empty {
  padding: 40px 20px;
  text-align: center;
  font-size: 0.85rem;
  color: var(--text-tertiary);
  background: var(--bg-secondary);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}
.preview-empty:hover {
  background: var(--bg-tertiary);
}
</style>
