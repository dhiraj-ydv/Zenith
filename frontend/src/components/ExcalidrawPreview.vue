<template>
  <div class="excalidraw-preview" ref="container">
    <div v-if="loading" class="preview-loading">Rendering drawing...</div>
    <div v-else-if="error" class="preview-error">Failed to load preview</div>
    <div v-else class="preview-canvas" ref="canvasContainer" @click="$emit('edit')"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
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

async function renderPreview() {
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
      loading.value = false
      return
    }

    const parsed = JSON.parse(drawingContent)
    if (!parsed.elements || parsed.elements.length === 0) {
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

    if (canvasContainer.value) {
      canvasContainer.value.innerHTML = ''
      svg.style.width = '100%'
      svg.style.height = 'auto'
      svg.style.maxWidth = '100%'
      canvasContainer.value.appendChild(svg)
    }
    loading.value = false
  } catch (e) {
    console.error('Failed to render Excalidraw preview:', e)
    error.value = true
    loading.value = false
  }
}

onMounted(renderPreview)
watch(() => props.content, renderPreview)
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
.preview-loading, .preview-error {
  padding: 20px;
  text-align: center;
  font-size: 0.8rem;
  color: var(--text-tertiary);
  background: var(--bg-secondary);
  border-radius: 8px;
}
</style>
