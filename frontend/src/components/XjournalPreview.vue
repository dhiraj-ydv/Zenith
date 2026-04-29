<template>
  <div class="xjournal-preview" :class="{ loading, error: !!errorMsg, empty: isEmpty, 'multi-page': pages.length > 1 }">
    <!-- Loading State -->
    <div v-if="loading" class="preview-status">
      <div class="loader"></div>
      <span>Loading document...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="errorMsg" class="preview-status error-state">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <span>{{ errorMsg }}</span>
      <button class="btn-retry" @click="fetchAndRender()" title="Retry">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
        </svg>
        Retry
      </button>
    </div>

    <!-- Rendered Pages -->
    <div v-else class="pages-container" @click="$emit('edit')">
      <div
        v-for="(page, idx) in pages"
        :key="idx"
        class="page-wrapper"
        :style="{ aspectRatio: page.width / page.height }"
      >
        <!-- Page number badge for multi-page docs -->
        <div v-if="pages.length > 1" class="page-badge">{{ idx + 1 }}</div>
        <svg
          :viewBox="`0 0 ${page.width} ${page.height}`"
          :width="'100%'"
          preserveAspectRatio="xMidYMid meet"
          class="xopp-svg"
          xmlns="http://www.w3.org/2000/svg"
        >
          <!-- Page background -->
          <rect
            x="0" y="0"
            :width="page.width"
            :height="page.height"
            :fill="page.bgColor"
          />
          <!-- Ruling lines (if applicable) -->
          <template v-if="page.bgStyle === 'lined'">
            <line
              v-for="ly in getLinedRuling(page)"
              :key="'rule-' + ly"
              :x1="0" :y1="ly" :x2="page.width" :y2="ly"
              stroke="#c0c0e0" stroke-width="0.5" opacity="0.5"
            />
          </template>
          <template v-if="page.bgStyle === 'graph'">
            <line
              v-for="gx in getGraphRulingX(page)"
              :key="'gx-' + gx"
              :x1="gx" :y1="0" :x2="gx" :y2="page.height"
              stroke="#c0c0e0" stroke-width="0.3" opacity="0.4"
            />
            <line
              v-for="gy in getGraphRulingY(page)"
              :key="'gy-' + gy"
              :x1="0" :y1="gy" :x2="page.width" :y2="gy"
              stroke="#c0c0e0" stroke-width="0.3" opacity="0.4"
            />
          </template>

          <!-- Strokes -->
          <template v-for="(layer, li) in page.layers" :key="'layer-' + li">
            <path
              v-for="(stroke, si) in layer.strokes"
              :key="'stroke-' + li + '-' + si"
              :d="stroke.pathData"
              :stroke="stroke.color"
              :stroke-width="stroke.width"
              :stroke-linecap="stroke.capStyle || 'round'"
              :stroke-linejoin="stroke.capStyle || 'round'"
              fill="none"
              :opacity="stroke.opacity"
            />
            <!-- Text elements -->
            <text
              v-for="(txt, ti) in layer.texts"
              :key="'text-' + li + '-' + ti"
              :x="txt.x"
              :y="txt.y"
              :font-size="txt.size"
              :fill="txt.color"
              :font-family="txt.font || 'sans-serif'"
            >{{ txt.content }}</text>
          </template>
        </svg>
      </div>

      <!-- Empty document overlay -->
      <div v-if="isEmpty" class="empty-overlay">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" opacity="0.5">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>
        <span>Empty document</span>
        <span class="empty-sub">Open in Xournal++ to start drawing</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  noteId: String
})

defineEmits(['edit'])

const loading = ref(true)
const errorMsg = ref('')
const pages = ref([])
const isEmpty = ref(false)

let pollTimer = null
let lastModified = null

// ── Xopp XML parsing ──

function parseXoppXml(xmlString) {
  const parser = new DOMParser()
  const doc = parser.parseFromString(xmlString, 'application/xml')

  const parseError = doc.querySelector('parsererror')
  if (parseError) throw new Error('Invalid .xopp XML')

  const pageNodes = doc.querySelectorAll('page')
  const parsedPages = []
  let hasContent = false

  pageNodes.forEach(pageNode => {
    const width = parseFloat(pageNode.getAttribute('width') || '595.27559')
    const height = parseFloat(pageNode.getAttribute('height') || '841.88976')

    // Parse background
    const bg = pageNode.querySelector('background')
    let bgColor = '#ffffff'
    let bgStyle = 'plain'
    if (bg) {
      const rawColor = bg.getAttribute('color') || '#ffffffff'
      bgColor = xoppColorToCSS(rawColor)
      bgStyle = bg.getAttribute('style') || 'plain'
    }

    // Parse layers
    const layers = []
    pageNode.querySelectorAll('layer').forEach(layerNode => {
      const strokes = []
      const texts = []

      // Parse strokes
      layerNode.querySelectorAll('stroke').forEach(strokeNode => {
        const tool = strokeNode.getAttribute('tool') || 'pen'
        if (tool === 'eraser') return // don't render eraser strokes visually

        const rawColor = strokeNode.getAttribute('color') || '#000000ff'
        const colorInfo = xoppColorToCSS(rawColor, true)
        const widthAttr = strokeNode.getAttribute('width') || '1.4'
        // width can be a list for variable-width strokes; take the first
        const strokeWidth = parseFloat(widthAttr.split(' ')[0])
        const capStyle = strokeNode.getAttribute('capStyle') || 'round'

        const coords = strokeNode.textContent.trim().split(/\s+/).map(Number)
        if (coords.length < 4) return

        const pathData = coordsToPath(coords)
        if (pathData) {
          hasContent = true
          strokes.push({
            pathData,
            color: colorInfo.color,
            opacity: colorInfo.opacity,
            width: strokeWidth,
            capStyle,
            tool
          })
        }
      })

      // Parse text elements
      layerNode.querySelectorAll('text').forEach(textNode => {
        const x = parseFloat(textNode.getAttribute('x') || '0')
        const y = parseFloat(textNode.getAttribute('y') || '0')
        const size = parseFloat(textNode.getAttribute('size') || '12')
        const rawColor = textNode.getAttribute('color') || '#000000ff'
        const font = textNode.getAttribute('font') || 'sans-serif'
        const content = textNode.textContent || ''
        if (content.trim()) {
          hasContent = true
          texts.push({
            x, y: y + size, // Xournal uses top-left; SVG text needs baseline
            size,
            color: xoppColorToCSS(rawColor),
            font,
            content
          })
        }
      })

      layers.push({ strokes, texts })
    })

    parsedPages.push({ width, height, bgColor, bgStyle, layers })
  })

  return { pages: parsedPages, hasContent }
}

function coordsToPath(coords) {
  // coords is [x1, y1, x2, y2, ...] or [x1, y1, p1, x2, y2, p2, ...] (with pressure)
  // We'll handle pairs (no pressure) and detect if there's pressure data
  if (coords.length < 2) return null

  let points = []

  // Standard format: x y x y x y ...
  for (let i = 0; i < coords.length - 1; i += 2) {
    points.push({ x: coords[i], y: coords[i + 1] })
  }

  if (points.length === 0) return null
  if (points.length === 1) {
    // Single point — draw a tiny circle-like dot
    const p = points[0]
    return `M ${p.x} ${p.y} L ${p.x + 0.01} ${p.y + 0.01}`
  }

  // Build smooth path using Catmull-Rom-like smoothing for natural pen strokes
  let d = `M ${points[0].x} ${points[0].y}`

  if (points.length === 2) {
    d += ` L ${points[1].x} ${points[1].y}`
    return d
  }

  // Use quadratic bezier smoothing for smoother curves
  for (let i = 1; i < points.length - 1; i++) {
    const midX = (points[i].x + points[i + 1].x) / 2
    const midY = (points[i].y + points[i + 1].y) / 2
    d += ` Q ${points[i].x} ${points[i].y} ${midX} ${midY}`
  }
  // Final segment to last point
  const last = points[points.length - 1]
  const secondLast = points[points.length - 2]
  d += ` Q ${secondLast.x} ${secondLast.y} ${last.x} ${last.y}`

  return d
}

function xoppColorToCSS(raw, withOpacity = false) {
  // Xournal colors can be: named ("black"), hex8 ("#RRGGBBAA"), hex6 ("#RRGGBB")
  const namedColors = {
    black: '#000000', blue: '#3333cc', red: '#ff0000', green: '#008000',
    gray: '#808080', lightblue: '#00c0ff', lightgreen: '#00ff00',
    magenta: '#ff00ff', orange: '#ff8000', yellow: '#ffff00', white: '#ffffff'
  }

  if (namedColors[raw]) {
    if (withOpacity) return { color: namedColors[raw], opacity: 1 }
    return namedColors[raw]
  }

  // Handle hex with alpha: #RRGGBBAA
  if (raw.startsWith('#') && raw.length === 9) {
    const rgb = raw.substring(0, 7)
    const alpha = parseInt(raw.substring(7, 9), 16) / 255
    if (withOpacity) return { color: rgb, opacity: alpha }
    return rgb
  }

  if (withOpacity) return { color: raw, opacity: 1 }
  return raw
}

// ── Ruling helpers ──
function getLinedRuling(page) {
  const lines = []
  const spacing = 24 // standard ruled spacing in pts
  for (let y = 80; y < page.height; y += spacing) {
    lines.push(y)
  }
  return lines
}

function getGraphRulingX(page) {
  const lines = []
  const spacing = 14.17 // 5mm grid in pts
  for (let x = spacing; x < page.width; x += spacing) {
    lines.push(x)
  }
  return lines
}

function getGraphRulingY(page) {
  const lines = []
  const spacing = 14.17
  for (let y = spacing; y < page.height; y += spacing) {
    lines.push(y)
  }
  return lines
}

// ── Data fetching ──

async function fetchAndRender() {
  if (!props.noteId) return
  loading.value = true
  errorMsg.value = ''

  try {
    const res = await fetch(`/api/xjournal/${props.noteId}/xml`)
    if (!res.ok) {
      if (res.status === 404) throw new Error('Document not found')
      throw new Error(`Server error (${res.status})`)
    }

    const xmlText = await res.text()
    const result = parseXoppXml(xmlText)
    pages.value = result.pages
    isEmpty.value = !result.hasContent
  } catch (err) {
    console.warn('Xjournal preview failed:', err)
    errorMsg.value = err.message || 'Failed to load document'
    pages.value = []
  } finally {
    loading.value = false
  }
}

async function checkForUpdates() {
  if (!props.noteId) return
  try {
    const res = await fetch(`/api/xjournal/${props.noteId}/file-info`)
    if (!res.ok) return
    const info = await res.json()
    if (lastModified !== null && info.modified !== lastModified) {
      // File changed on disk — re-render
      await fetchAndRender()
    }
    lastModified = info.modified
  } catch {
    // silent — polling failure is non-critical
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(checkForUpdates, 3000) // Check every 3 seconds
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onMounted(async () => {
  await fetchAndRender()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})

watch(() => props.noteId, async () => {
  lastModified = null
  await fetchAndRender()
})

defineExpose({
  refresh: () => fetchAndRender()
})
</script>

<style scoped>
.xjournal-preview {
  width: 100%;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
  background: var(--bg-secondary, #1e1e1e);
}

.pages-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 8px;
  cursor: pointer;
}

.page-wrapper {
  width: 100%;
  max-width: 100%;
  position: relative;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
  background: white;
  transition: box-shadow 0.2s ease;
}

.page-wrapper:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
}

.page-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  color: #fff;
  font-size: 0.6rem;
  font-weight: 700;
  border-radius: 50%;
  z-index: 2;
}

.xopp-svg {
  display: block;
  width: 100%;
  height: auto;
}

/* States */
.preview-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: #888;
  font-size: 0.8rem;
  padding: 32px 16px;
}

.error-state {
  color: #f87171;
}

.error-state svg {
  opacity: 0.6;
}

.btn-retry {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  padding: 5px 14px;
  background: rgba(248, 113, 113, 0.12);
  color: #f87171;
  border: 1px solid rgba(248, 113, 113, 0.2);
  border-radius: 6px;
  font-size: 0.72rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-retry:hover {
  background: rgba(248, 113, 113, 0.2);
  border-color: rgba(248, 113, 113, 0.35);
}

.empty-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.85);
  pointer-events: none;
  z-index: 1;
}

.empty-overlay span {
  font-size: 0.78rem;
  color: #999;
  font-weight: 500;
}

.empty-overlay .empty-sub {
  font-size: 0.65rem;
  color: #bbb;
  font-weight: 400;
}

.loader {
  width: 22px;
  height: 22px;
  border: 2.5px solid rgba(255, 255, 255, 0.08);
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
