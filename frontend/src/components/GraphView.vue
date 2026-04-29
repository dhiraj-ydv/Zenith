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
        <div class="graph-search">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="search-icon">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
          </svg>
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="Search notes..." 
            @input="handleSearch"
            @keydown.enter="focusFoundNode"
          />
          <button v-if="searchQuery" class="clear-search" @click="clearSearch">×</button>
        </div>
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
      <div v-if="searchQuery" class="legend-item">
        <span class="legend-dot" style="background: #ff9f43;"></span>
        <span>Search Match</span>
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

// Search state
const searchQuery = ref('')
const highlightedNodes = ref(new Set())

let instance = null

function handleSearch() {
  if (!instance) return
  
  const query = searchQuery.value.toLowerCase().trim()
  highlightedNodes.value.clear()
  
  if (query) {
    const nodes = instance.graphData().nodes
    nodes.forEach(node => {
      if (node.name.toLowerCase().includes(query)) {
        highlightedNodes.value.add(node.id)
      }
    })
  }
  
  // Update node appearance - Only highlight match, don't dim others
  instance
    .nodeColor(node => {
      if (query && highlightedNodes.value.has(node.id)) return '#ff9f43' // Orange for matches
      return '#6366f1' // Standard purple for everything else
    })
    .nodeOpacity(0.9)
    .linkColor(() => 'rgba(255,255,255,0.2)')
    
  // Force redraw of 3D objects to update labels
  instance.nodeThreeObject(instance.nodeThreeObject())
}

function clearSearch() {
  searchQuery.value = ''
  handleSearch()
}

function focusFoundNode() {
  if (!instance || highlightedNodes.value.size === 0) return
  
  // Find the first matching node
  const firstId = Array.from(highlightedNodes.value)[0]
  const nodes = instance.graphData().nodes
  const node = nodes.find(n => n.id === firstId)
  
  if (node) {
    // Aim camera at node
    const distance = 40
    const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z)
    instance.cameraPosition(
      { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }, // new pos
      node, // lookAt
      1000  // ms transition
    )
  }
}

function isWebGLAvailable() {
  try {
    const canvas = document.createElement('canvas')
    return !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')))
  } catch (e) {
    return false
  }
}

const THREE_CDN = 'https://unpkg.com/three@0.160.0/build/three.min.js'

async function loadLibrary() {
  if (window.ForceGraph3D && window.THREE) return window.ForceGraph3D
  
  // Load Three.js first
  if (!window.THREE) {
    await new Promise((resolve, reject) => {
      const script = document.createElement('script')
      script.src = THREE_CDN
      script.onload = resolve
      script.onerror = reject
      document.head.appendChild(script)
    })
  }

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
      .nodeColor(node => {
        if (searchQuery.value && highlightedNodes.value.has(node.id)) return '#ff9f43'
        return '#6366f1'
      })
      .nodeLabel(node => {
        const name = node.name
        const query = searchQuery.value.toLowerCase().trim()
        if (!query) return name
        
        // Highlight matching characters in the tooltip as well
        const regex = new RegExp(`(${query})`, 'gi')
        return name.replace(regex, '<span style="color: #ff9f43; font-weight: bold;">$1</span>')
      })
      .nodeOpacity(0.9)
      .nodeRelSize(4)
      .linkColor(() => 'rgba(255,255,255,0.2)')
      .linkWidth(2)
      .linkDirectionalParticles(3)
      .linkDirectionalParticleSpeed(0.008)
      .onNodeClick(node => {
        emit('select-node', node.id)
      })
      .showNavInfo(false)
      
    // Add permanent labels
    instance.nodeThreeObject(node => {
      // Create a group to hold both sphere and text
      const group = new THREE.Group()
      
      // The "dot" (sphere)
      const isMatch = searchQuery.value && highlightedNodes.value.has(node.id)
      const color = isMatch ? '#ff9f43' : '#6366f1'
      const sphere = new THREE.Mesh(
        new THREE.SphereGeometry(5),
        new THREE.MeshLambertMaterial({ color, transparent: true, opacity: 0.9 })
      )
      group.add(sphere)

      // The label (sprite)
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      const text = node.name
      const query = searchQuery.value.toLowerCase().trim()
      
      // Larger, thicker font
      const fontSize = 32
      ctx.font = `bold ${fontSize}px Inter, system-ui, sans-serif`
      const textWidth = ctx.measureText(text).width
      canvas.width = textWidth + 40
      canvas.height = fontSize * 1.5
      
      ctx.font = `bold ${fontSize}px Inter, system-ui, sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      
      const xCenter = canvas.width / 2
      const yCenter = canvas.height / 2
      
      // Draw text with partial highlighting
      if (query && text.toLowerCase().includes(query)) {
        const parts = text.split(new RegExp(`(${query})`, 'gi'))
        let currentX = xCenter - textWidth / 2
        
        parts.forEach(part => {
          const isPartMatch = part.toLowerCase() === query
          ctx.fillStyle = isPartMatch ? '#ff9f43' : '#ffffff'
          ctx.font = `bold ${fontSize}px Inter, system-ui, sans-serif`
          
          ctx.fillText(part, currentX + ctx.measureText(part).width / 2, yCenter)
          currentX += ctx.measureText(part).width
        })
      } else {
        ctx.fillStyle = '#ffffff'
        ctx.globalAlpha = 0.8
        ctx.fillText(text, xCenter, yCenter)
      }

      const texture = new THREE.CanvasTexture(canvas)
      const spriteMaterial = new THREE.SpriteMaterial({ map: texture, transparent: true })
      const sprite = new THREE.Sprite(spriteMaterial)
      
      // Position label below the dot
      sprite.scale.set(canvas.width / 8, canvas.height / 8, 1)
      sprite.position.set(0, -15, 0)
      
      group.add(sprite)
      return group
    })

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

.graph-controls {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.graph-search {
  display: flex;
  align-items: center;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 0 var(--space-sm);
  height: 32px;
  width: 220px;
  transition: width 0.2s, border-color 0.2s;
}
.graph-search:focus-within {
  width: 300px;
  border-color: var(--accent-primary);
  background: var(--bg-secondary);
}
.search-icon {
  color: var(--text-tertiary);
  margin-right: var(--space-xs);
  flex-shrink: 0;
}
.graph-search input {
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 0.8125rem;
  width: 100%;
  outline: none;
}
.clear-search {
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  line-height: 1;
}
.clear-search:hover {
  color: var(--text-primary);
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
