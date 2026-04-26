<template>
  <div class="graph-container">
    <div class="graph-header">
      <div class="graph-title-area">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 2L12 22M2 12L22 12M12 2L22 12L12 22L2 12L12 2"/>
        </svg>
        <h2>3D Knowledge Graph</h2>
        <span class="graph-stats">{{ graphStore.nodes.length }} nodes · {{ graphStore.edges.length }} links</span>
      </div>
      <div class="graph-controls">
        <button class="btn btn-ghost" @click="resetView">
          Recenter
        </button>
      </div>
    </div>
    <div class="graph-canvas-wrapper" ref="wrapper">
       <div id="3d-graph" ref="graphCanvas"></div>
       <div v-if="loadingStatus" class="graph-status-overlay">
         <div class="status-content">
           <span class="status-text">{{ loadingStatus }}</span>
           <p v-if="errorDetail" class="status-detail">{{ errorDetail }}</p>
         </div>
       </div>
    </div>
    <div class="graph-legend">
      <div class="legend-item">
        <span class="legend-dot" style="background: #6366f1;"></span>
        <span>Note</span>
      </div>
      <div class="hint">Scroll to zoom · Drag to rotate · Click note to open</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useGraphStore } from '../stores/graph'

const GRAPH_CDN = 'https://unpkg.com/3d-force-graph@1.73.3/dist/3d-force-graph.min.js'

const emit = defineEmits(['select-node'])
const graphStore = useGraphStore()
const graphCanvas = ref(null)
const wrapper = ref(null)
const loadingStatus = ref('Loading 3D Engine...')
const errorDetail = ref('')

let instance = null

function isWebGLAvailable() {
  try {
    const canvas = document.createElement('canvas')
    return !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')))
  } catch (e) {
    return false
  }
}

async function loadLibrary() {
  if (window.ForceGraph3D) return window.ForceGraph3D
  
  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = GRAPH_CDN
    script.async = true
    script.onload = () => {
      if (typeof window.ForceGraph3D === 'function') {
        resolve(window.ForceGraph3D)
      } else {
        reject(new Error('Library loaded but ForceGraph3D not found on window'))
      }
    }
    script.onerror = () => reject(new Error('Failed to download 3D library from CDN'))
    document.head.appendChild(script)
  })
}

function initGraph(ForceGraph3D) {
  if (!graphCanvas.value) return

  if (!isWebGLAvailable()) {
    loadingStatus.value = 'WebGL Not Supported'
    errorDetail.value = 'Your browser or hardware does not support WebGL.'
    return
  }

  // Clear container
  graphCanvas.value.innerHTML = ''

  const gData = {
    nodes: graphStore.nodes.map(n => {
      const links = graphStore.edges.filter(e => e.source === n.id || e.target === n.id).length
      return {
        id: n.id,
        name: n.title,
        val: 2 + (links * 1.5)
      }
    }),
    links: graphStore.edges.map(e => ({
      source: e.source,
      target: e.target
    }))
  }

  try {
    instance = ForceGraph3D()(graphCanvas.value)
      .graphData(gData)
      .backgroundColor('#050508')
      .nodeColor(() => '#6366f1')
      .nodeLabel('name')
      .nodeOpacity(0.9)
      .nodeRelSize(4)
      .linkColor(() => 'rgba(255,255,255,0.2)')
      .linkWidth(1)
      .linkDirectionalParticles(2)
      .linkDirectionalParticleSpeed(0.005)
      .onNodeClick(node => {
        emit('select-node', node.id)
      })
      .showNavInfo(false)

    // Fit to container dimensions
    if (wrapper.value) {
      const rect = wrapper.value.getBoundingClientRect()
      instance.width(rect.width).height(rect.height)
    }

    loadingStatus.value = ''
    
    // Auto-resize
    const resizeObserver = new ResizeObserver(entries => {
      if (!instance) return
      for (let entry of entries) {
        const { width, height } = entry.contentRect
        if (width > 0 && height > 0) {
          instance.width(width).height(height)
        }
      }
    })
    if (wrapper.value) resizeObserver.observe(wrapper.value)

  } catch (err) {
    console.error('3D Rendering Error:', err)
    loadingStatus.value = 'Rendering Error'
    errorDetail.value = err.message
  }
}

function resetView() {
  if (instance) instance.zoomToFit(600)
}

onMounted(async () => {
  try {
    const lib = await loadLibrary()
    await graphStore.fetchGraph()
    await nextTick()
    initGraph(lib)
  } catch (err) {
    loadingStatus.value = 'Load Failed'
    errorDetail.value = err.message
  }
})

watch(() => graphStore.nodes, () => {
  if (instance) {
    const gData = {
      nodes: graphStore.nodes.map(n => ({ id: n.id, name: n.title, val: 2 })),
      links: graphStore.edges.map(e => ({ source: e.source, target: e.target }))
    }
    instance.graphData(gData)
  }
}, { deep: true })

onUnmounted(() => {
  if (instance) {
    if (graphCanvas.value) graphCanvas.value.innerHTML = ''
    instance = null
  }
})
</script>

<style scoped>
.graph-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background: #050508;
  overflow: hidden;
}

.graph-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-xl);
  border-bottom: 1px solid var(--border-subtle);
  background: #0a0a0f;
  z-index: 10;
}

.graph-title-area {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}
.graph-title-area h2 {
  font-size: 1rem;
  font-weight: 600;
}
.graph-stats {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
  padding: 2px 10px;
  border-radius: var(--radius-full);
}

.graph-canvas-wrapper {
  flex: 1;
  position: relative;
  min-height: 0;
  background: #050508;
}

#3d-graph {
  width: 100%;
  height: 100%;
}

.graph-status-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  width: 80%;
}
.status-text {
  color: var(--accent-primary);
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.status-detail {
  color: var(--text-tertiary);
  font-size: 0.75rem;
  margin-top: var(--space-sm);
}

.graph-legend {
  display: flex;
  align-items: center;
  gap: var(--space-xl);
  padding: var(--space-sm) var(--space-xl);
  border-top: 1px solid var(--border-subtle);
  background: #0a0a0f;
  z-index: 10;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.6875rem;
  color: var(--text-tertiary);
}
.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.hint {
  margin-left: auto;
  font-size: 0.625rem;
  color: var(--text-tertiary);
  opacity: 0.6;
}
</style>
