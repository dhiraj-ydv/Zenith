<template>
  <div class="lorien-preview" ref="container" @click="$emit('edit')">
    <div v-if="loading" class="preview-loading">Rendering Lorien canvas...</div>
    <div v-else-if="error" class="preview-error">Failed to load canvas</div>
    <div v-else class="preview-content">
      <canvas ref="canvas" class="preview-canvas"></canvas>
      <div v-if="isEmpty" class="preview-empty">Empty Canvas</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { notesApi } from '../api/client'

const props = defineProps({
  name: String,
  content: String
})

const emit = defineEmits(['edit'])

const canvas = ref(null)
const loading = ref(true)
const error = ref(false)
const isEmpty = ref(false)

async function renderPreview() {
  try {
    loading.value = true
    error.value = false
    isEmpty.value = false

    let drawingContent = props.content
    if (!drawingContent || drawingContent === '{}') {
      try {
        const { data } = await notesApi.get(props.name)
        drawingContent = data.content
      } catch (err) {
        console.warn(`Could not fetch Lorien drawing ${props.name} for preview`, err)
      }
    }

    if (!drawingContent || drawingContent === '{}') {
      isEmpty.value = true
      loading.value = false
      return
    }

    const parsed = JSON.parse(drawingContent)
    if (!parsed.strokes || parsed.strokes.length === 0) {
      isEmpty.value = true
      loading.value = false
      return
    }

    loading.value = false
    await nextTick()

    if (canvas.value) {
      drawStrokes(canvas.value, parsed.strokes)
    }
  } catch (e) {
    console.error('Failed to render Lorien preview:', e)
    error.value = true
    loading.value = false
  }
}

function drawStrokes(cnv, strokes) {
  const ctx = cnv.getContext('2d')
  
  // Find bounds to scale
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
  strokes.forEach(stroke => {
    const points = stroke.points || stroke // support both old and new format
    points.forEach(p => {
      if (p.x < minX) minX = p.x
      if (p.y < minY) minY = p.y
      if (p.x > maxX) maxX = p.x
      if (p.y > maxY) maxY = p.y
    })
  })

  const padding = 20
  const width = (maxX - minX) + padding * 2
  const height = (maxY - minY) + padding * 2

  // Set canvas size based on content aspect ratio
  cnv.width = 800
  cnv.height = (height / width) * 800
  
  const scale = 800 / width

  ctx.clearRect(0, 0, cnv.width, cnv.height)
  
  ctx.translate(padding * scale, padding * scale)
  ctx.scale(scale, scale)
  ctx.translate(-minX, -minY)

  strokes.forEach(stroke => {
    const points = stroke.points || stroke
    if (points.length < 1) return
    
    ctx.lineWidth = (stroke.size || 2)
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.strokeStyle = stroke.color || '#61afef'

    ctx.beginPath()
    ctx.moveTo(points[0].x, points[0].y)
    points.forEach(p => {
      ctx.lineTo(p.x, p.y)
    })
    ctx.stroke()
  })
}

onMounted(renderPreview)
watch(() => [props.content, props.name], renderPreview)
</script>

<style scoped>
.lorien-preview {
  width: 100%;
  cursor: pointer;
}
.preview-content {
  background: #1e1e1e;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100px;
}
.preview-canvas {
  max-width: 100%;
  height: auto;
  display: block;
}
.preview-loading, .preview-error, .preview-empty {
  padding: 40px;
  text-align: center;
  font-size: 0.8rem;
  color: var(--text-tertiary);
  background: var(--bg-secondary);
  border-radius: 8px;
}
</style>
