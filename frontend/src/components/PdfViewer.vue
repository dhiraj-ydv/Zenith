<template>
  <div class="pdf-viewer">
    <canvas v-if="canvasVisible" ref="canvas" style="width:100%;height:auto;border:0;" />
    <iframe v-else-if="blobUrl" :src="blobUrl" style="width:100%;height:600px;border:0;" loading="lazy"></iframe>
    <div v-else class="pdf-loading">Loading PDF…</div>
    <p style="margin-top:8px;">
      If the PDF does not display, <a :href="directUrl" target="_blank" rel="noopener noreferrer">open or download it</a>.
    </p>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { attachmentsApi } from '../api/client'

const props = defineProps({ filename: { type: String, required: true } })

const blobUrl = ref(null)
const canvas = ref(null)
const canvasVisible = ref(false)

const directUrl = computed(() => {
  let url = attachmentsApi.getUrl(props.filename)
  try {
    if (typeof window !== 'undefined' && window.location && window.location.port && window.location.port !== '8000') {
      const rawHost = window.location.hostname || '127.0.0.1'
      const host = (rawHost === 'localhost' || rawHost === '::1') ? '127.0.0.1' : rawHost
      url = `${window.location.protocol}//${host}:8000/api/attachments/${encodeURIComponent(props.filename)}`
    }
  } catch (e) {
    // ignore
  }
  return url
})

async function renderWithPdfJsData(data) {
  try {
    const pdfjsLib = window.pdfjsLib
    if (!pdfjsLib) return false
    if (pdfjsLib.GlobalWorkerOptions && !pdfjsLib.GlobalWorkerOptions.workerSrc) {
      pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://unpkg.com/pdfjs-dist@3.10.111/build/pdf.worker.min.js'
    }
    const loadingTask = pdfjsLib.getDocument({ data })
    const pdf = await loadingTask.promise
    const page = await pdf.getPage(1)
    const viewport = page.getViewport({ scale: 1.5 })
    const cnv = canvas.value
    if (!cnv) return false
    cnv.width = viewport.width
    cnv.height = viewport.height
    const ctx = cnv.getContext('2d')
    const renderContext = { canvasContext: ctx, viewport }
    await page.render(renderContext).promise
    canvasVisible.value = true
    return true
  } catch (e) {
    console.error('pdfjs render failed', e)
    return false
  }
}

async function initPdf() {
  blobUrl.value = null
  canvasVisible.value = false
  try {
    // Fetch the PDF bytes first (avoids range requests in iframe/proxy issues)
    const resp = await fetch(directUrl.value, { method: 'GET' })
    if (!resp.ok) {
      blobUrl.value = directUrl.value
      return
    }
    const arrayBuffer = await resp.arrayBuffer()
    const usedPdfJs = await renderWithPdfJsData(new Uint8Array(arrayBuffer))
    if (!usedPdfJs) {
      // fallback to using direct backend URL in iframe
      blobUrl.value = directUrl.value
    }
  } catch (e) {
    console.error('PDF fetch/render failed', e)
    blobUrl.value = directUrl.value
  }
}

onMounted(initPdf)
watch(() => props.filename, initPdf)
</script>

<style scoped>
.pdf-loading { color: var(--text-tertiary); }
canvas { max-width: 100%; height: auto; }
</style>