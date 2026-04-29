<template>
  <div class="editor-container">
    <!-- Editor Header -->
    <header class="editor-header">
      <div class="editor-title-area">
        <h1 class="editor-title" v-if="!editingTitle" @dblclick="startTitleEdit">
          {{ note.title }}
        </h1>
        <input
          v-else
          type="text"
          class="title-edit-input"
          v-model="titleDraft"
          @keydown.enter="saveTitle"
          @keydown.escape="cancelTitleEdit"
          @blur="saveTitle"
          ref="titleInput"
        />
        <div class="editor-meta">
          <div class="meta-labels" v-if="note.labels.length > 0">
            <span class="badge" v-for="l in note.labels" :key="l">{{ l }}</span>
          </div>
        </div>
      </div>
      <div class="editor-actions">
        <button 
          class="btn-icon tooltip" 
          data-tooltip="Add to Hierarchy" 
          @click="showLabelPicker = !showLabelPicker" 
          :class="{ active: showLabelPicker }"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20.59 13.41L13.42 20.58C13.04 20.96 12.53 21.17 12 21.17C11.47 21.17 10.96 20.96 10.59 20.58L2 12V2H12L20.59 10.59C21.37 11.37 21.37 12.63 20.59 13.41Z"/>
            <line x1="7" y1="7" x2="7.01" y2="7"/>
          </svg>
        </button>
        <div class="view-toggle">
          <button class="toggle-btn" :class="{ active: viewMode === 'edit' }" @click="viewMode = 'edit'">Edit</button>
          <button class="toggle-btn" :class="{ active: viewMode === 'split' }" @click="viewMode = 'split'">Split</button>
          <button class="toggle-btn" :class="{ active: viewMode === 'preview' }" @click="viewMode = 'preview'">Preview</button>
        </div>
        <button class="btn btn-danger" @click="confirmDelete">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6V20C19 21.1 18.1 22 17 22H7C5.9 22 5 21.1 5 20V6M8 6V4C8 2.9 8.9 2 10 2H14C15.1 2 16 2.9 16 4V6"/>
          </svg>
        </button>
      </div>
    </header>

    <!-- Hierarchy Picker -->
    <div class="label-picker" v-if="showLabelPicker">
      <div class="picker-header">Add to Location</div>
      <div class="picker-scroll-area">
        <div class="label-picker-item" v-for="label in allLabels" :key="label.id">
          <label class="label-checkbox">
            <input type="checkbox" :checked="note.labels.includes(label.id.split(':')[1])" @change="toggleLabel(label.id)" />
            <span>{{ label.id.split(':')[1] }}</span>
          </label>
        </div>
      </div>
    </div>

    <!-- Editor Body -->
    <div class="editor-body" :class="viewMode">
      <div class="edit-pane" v-if="viewMode !== 'preview'">
        <div class="edit-area-wrapper" @dragover.prevent @drop.prevent="handleDrop">
          <textarea
            class="edit-textarea"
            v-model="content"
            @input="handleInput($event)"
            @keydown="handleKeydown"
            @scroll="handleScroll"
            ref="textarea"
            placeholder="Start writing... Use [[ to link/embed drawings"
            spellcheck="false"
          ></textarea>
          <!-- Autocomplete -->
          <div class="autocomplete-dropdown" v-if="showAutocomplete && autocompleteResults.length > 0" :style="autocompletePosition">
            <button
              v-for="(result, idx) in autocompleteResults"
              :key="result.id"
              class="autocomplete-item"
              :class="{ active: autocompleteIndex === idx }"
              @click="insertAutocomplete(result)"
            >
              <svg v-if="result.type === 'excalidraw'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/><path d="M2 2l5 2"/><path d="M2 2l2 5"/>
              </svg>
              <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6C4.89 2 4 2.9 4 4V20C4 21.1 4.89 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z"/><path d="M14 2V8H20"/>
              </svg>
              <span class="ac-title">{{ result.title }}</span>
              <span v-if="result.type === 'excalidraw'" class="ac-tag">excalidraw</span>
            </button>
            <div class="autocomplete-footer" v-if="autocompleteQuery">
               Press Enter to link to "{{ autocompleteQuery }}"
            </div>
          </div>
        </div>
      </div>

      <div class="preview-pane" v-if="viewMode !== 'edit'" ref="previewPane" @scroll="handleScroll">
        <div class="preview-content markdown-body" @click="handlePreviewClick">
          <template v-for="(block, idx) in contentBlocks" :key="idx">
             <div v-if="block.type === 'drawing'" class="drawing-preview-block">
                <div class="drawing-header-mini">
                  <span class="drawing-name-pill">{{ block.name }}</span>
                  <button class="btn-edit-drawing" @click="notesStore.fetchNote(block.name)">Edit Excalidraw</button>
                </div>
                <ExcalidrawPreview :content="block.content" :name="block.name" @edit="openDrawingViewer(block.name, 'excalidraw')" />
             </div>
             <div v-else-if="block.type === 'lorien'" class="drawing-preview-block lorien-block">
                <div class="drawing-header-mini">
                  <span class="drawing-name-pill">{{ block.name }}</span>
                  <button class="btn-edit-drawing" @click="notesStore.fetchNote(block.name)">Edit Lorien</button>
                </div>
                <LorienPreview :content="block.content" :name="block.name" @edit="openDrawingViewer(block.name, 'lorien')" />
             </div>
             <div v-else-if="block.type === 'xopp'" class="drawing-preview-block xjournal-block">
                <div class="drawing-header-mini">
                  <div class="drawing-info">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: #6366f1">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                    <span class="drawing-name-pill">{{ block.name }}</span>
                  </div>
                  <div class="drawing-actions">
                    <button class="btn-refresh-drawing tooltip" @click="refreshXopp(block.name)" data-tooltip="Refresh Preview">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
                      </svg>
                    </button>
                    <button class="btn-edit-drawing" @click="notesStore.openXjournal(block.name)">Edit Xournal++</button>
                  </div>
                </div>
                <XjournalPreview :note-id="block.name" :ref="(el) => setXoppRef(el, block.name)" @edit="notesStore.openXjournal(block.name)" />
             </div>
               <div v-else-if="block.type === 'pdf'" class="pdf-block">
                 <PdfViewer :filename="block.filename" />
               </div>
               <div v-else v-html="block.html"></div>
          </template>
        </div>
      </div>
    </div>

    <!-- Status Bar -->
    <footer class="editor-status">
      <span class="status-item" v-if="notesStore.saving"><span class="saving-indicator"></span> Saving...</span>
      <span class="status-item" v-else><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Saved</span>
      <span class="status-item">{{ wordCount }} words</span>
    </footer>

    <!-- New Drawing Modal -->
    <Teleport to="body">
       <div class="modal-overlay" v-if="showNewDrawingModal" @click.self="showNewDrawingModal = false">
         <div class="modal fade-in">
           <h3 class="modal-title">New {{ creationType === 'lorien' ? 'Lorien' : (creationType === 'xopp' ? 'Xournal++' : 'Excalidraw') }}</h3>
           <input type="text" class="input" :placeholder="creationType === 'lorien' ? 'Lorien name...' : (creationType === 'xopp' ? 'Xournal++ name...' : 'Excalidraw name...')" v-model="newDrawingTitle" @keydown.enter="createAndEmbedDrawing" autofocus />
           <div class="modal-actions">
             <button class="btn btn-ghost" @click="showNewDrawingModal = false">Cancel</button>
             <button class="btn btn-primary" @click="createAndEmbedDrawing" :disabled="!newDrawingTitle.trim()">Create & Embed</button>
           </div>
         </div>
       </div>
    <!-- Hidden file input for /upload command -->
    <input ref="fileInput" type="file" style="display:none" @change="handleFileSelected" :accept="acceptedTypes" />

    <!-- Drawing Viewer Modal -->
    <div class="modal-overlay drawing-viewer-overlay" v-if="viewingDrawing" @click.self="closeDrawingViewer">
      <div class="drawing-viewer-modal fade-in">
        <header class="viewer-header">
          <div class="viewer-title">
            <svg v-if="viewingDrawing.type === 'excalidraw'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/><path d="M2 2l5 2"/><path d="M2 2l2 5"/>
            </svg>
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/>
            </svg>
            <h3>{{ viewingDrawing.name }}</h3>
          </div>
          <div class="viewer-actions">
            <button class="zoom-btn" @click="viewerZoom = Math.max(0.25, viewerZoom - 0.25)">-</button>
            <span class="zoom-level">{{ Math.round(viewerZoom * 100) }}%</span>
            <button class="zoom-btn" @click="viewerZoom = Math.min(3, viewerZoom + 0.25)">+</button>
            <button class="btn btn-primary btn-sm" @click="notesStore.fetchNote(viewingDrawing.name); closeDrawingViewer()">Edit</button>
            <button class="btn-icon" @click="closeDrawingViewer">
               <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </div>
        </header>
        <div 
          class="viewer-body" 
          @wheel.prevent="handleViewerWheel" 
          @mousedown="startViewerPan" 
          @mousemove="handleViewerPan" 
          @mouseup="endViewerPan" 
          @mouseleave="endViewerPan"
          ref="viewerBodyRef"
          :class="{ 'is-panning': isViewerPanning }"
        >
          <div class="viewer-canvas" :style="{ transform: `scale(${viewerZoom})`, transformOrigin: 'top center' }">
             <ExcalidrawPreview v-if="viewingDrawing.type === 'excalidraw'" :name="viewingDrawing.name" content="{}" />
             <LorienPreview v-if="viewingDrawing.type === 'lorien'" :name="viewingDrawing.name" content="{}" />
          </div>
        </div>
      </div>
    </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { marked } from 'marked'
import { useNotesStore } from '../stores/notes'
import { useLabelsStore } from '../stores/labels'
import { attachmentsApi } from '../api/client'
import ExcalidrawPreview from './ExcalidrawPreview.vue'
import LorienPreview from './LorienPreview.vue'
import XjournalPreview from './XjournalPreview.vue'
import PdfViewer from './PdfViewer.vue'

const notesStore = useNotesStore()
const labelsStore = useLabelsStore()

const content = ref('')
const viewMode = ref('split')
const editingTitle = ref(false)
const titleDraft = ref('')
const titleInput = ref(null)
const textarea = ref(null)
const previewPane = ref(null)
const fileInput = ref(null)
const acceptedTypes = 'image/*,video/*,audio/*,application/pdf'
const userInteracted = ref(false)
const showLabelPicker = ref(false)
const showNewDrawingModal = ref(false)
const newDrawingTitle = ref('')
const creationType = ref('excalidraw')

const xoppRefs = ref({})
function setXoppRef(el, name) {
  if (el) xoppRefs.value[name] = el
}
function refreshXopp(name) {
  if (xoppRefs.value[name]) xoppRefs.value[name].refresh()
}

const showAutocomplete = ref(false)
const autocompleteResults = ref([])
const autocompleteIndex = ref(0)
const autocompletePosition = ref({ top: '0px', left: '0px' })
const autocompleteQuery = ref('')

// Viewer Modal State
const viewingDrawing = ref(null)
const viewerZoom = ref(1)

// Panning State
const viewerBodyRef = ref(null)
const isViewerPanning = ref(false)
let viewerPanStartX = 0
let viewerPanStartY = 0
let viewerPanScrollLeft = 0
let viewerPanScrollTop = 0

function openDrawingViewer(name, type) {
  viewingDrawing.value = { name, type }
  viewerZoom.value = 1
}

function closeDrawingViewer() {
  viewingDrawing.value = null
  viewerZoom.value = 1
  isViewerPanning.value = false
}

function startViewerPan(e) {
  if (e.button !== 0) return // Only left click
  if (!viewerBodyRef.value) return
  isViewerPanning.value = true
  viewerPanStartX = e.pageX - viewerBodyRef.value.offsetLeft
  viewerPanStartY = e.pageY - viewerBodyRef.value.offsetTop
  viewerPanScrollLeft = viewerBodyRef.value.scrollLeft
  viewerPanScrollTop = viewerBodyRef.value.scrollTop
}

function handleViewerPan(e) {
  if (!isViewerPanning.value || !viewerBodyRef.value) return
  e.preventDefault()
  const x = e.pageX - viewerBodyRef.value.offsetLeft
  const y = e.pageY - viewerBodyRef.value.offsetTop
  const walkX = (x - viewerPanStartX) * 1.5 // Pan speed multiplier
  const walkY = (y - viewerPanStartY) * 1.5
  viewerBodyRef.value.scrollLeft = viewerPanScrollLeft - walkX
  viewerBodyRef.value.scrollTop = viewerPanScrollTop - walkY
}

function endViewerPan() {
  isViewerPanning.value = false
}

function handleViewerWheel(e) {
  // Zoom on any mouse wheel scroll
  if (e.deltaY < 0) viewerZoom.value = Math.min(3, viewerZoom.value + 0.1)
  else viewerZoom.value = Math.max(0.25, viewerZoom.value - 0.1)
}

let saveTimer = null

const note = computed(() => notesStore.activeNote || { id: '', title: '', content: '', labels: [], links: [], attachments: [] })
const allLabels = computed(() => labelsStore.hierarchy.filter(h => h.id.startsWith('label:') || h.id.startsWith('feed:')))

const contentBlocks = computed(() => {
  if (!content.value) return [{ type: 'html', html: '<p style="color: var(--text-tertiary);">Nothing to preview</p>' }]

  const blocks = []
  const attachRegex = /!\[\[([^\]]+)\]\]/g
  let lastIndex = 0
  let match

  while ((match = attachRegex.exec(content.value)) !== null) {
    if (match.index > lastIndex) {
      const text = content.value.substring(lastIndex, match.index)
      blocks.push({ type: 'html', html: renderMarkdown(text) })
    }

    const filename = match[1]
    if (filename.endsWith('.excalidraw')) {
      const drawingName = filename.replace('.excalidraw', '')
      blocks.push({ type: 'drawing', name: drawingName, content: '' })
    } else if (filename.endsWith('.lorien')) {
      const drawingName = filename.replace('.lorien', '')
      blocks.push({ type: 'lorien', name: drawingName })
    } else if (filename.endsWith('.xopp')) {
      const drawingName = filename.replace('.xopp', '')
      blocks.push({ type: 'xopp', name: drawingName })
    } else if (filename.toLowerCase().endsWith('.pdf')) {
      blocks.push({ type: 'pdf', filename })
    } else {
      // treat as inline image/embed; renderMarkdown will convert it
      blocks.push({ type: 'html', html: renderMarkdown(match[0]) })
    }

    lastIndex = attachRegex.lastIndex
  }

  if (lastIndex < content.value.length) {
    const text = content.value.substring(lastIndex)
    blocks.push({ type: 'html', html: renderMarkdown(text) })
  }

  return blocks
})

function renderMarkdown(text) {
  // Replace image-style wiki embeds first: ![[file.ext]] -> <img ...>
  let processed = text.replace(
    /!\[\[([^\]]+)\]\]/g,
    (match, filename) => {
       if (filename.endsWith('.excalidraw') || filename.endsWith('.lorien')) return match // handled elsewhere
       return `<img src="${attachmentsApi.getUrl(filename)}" alt="${filename}" style="max-width:100%;border-radius:8px;margin:8px 0;" />`
    }
  )

  // Then replace normal wiki links [[file]] -> <a ...>
  processed = processed.replace(
    /\[\[([^\]]+)\]\]/g,
    '<a class="wikilink" href="#" data-link="$1">$1</a>'
  )
  // If running in the browser dev server, rewrite /api/attachments/... to direct backend host:8000 to avoid proxy range aborts
    try {
    if (typeof window !== 'undefined' && window.location && window.location.port && window.location.port !== '8000') {
      const rawHost = window.location.hostname || '127.0.0.1'
      const host = (rawHost === 'localhost' || rawHost === '::1') ? '127.0.0.1' : rawHost
      const backendPrefix = `${window.location.protocol}//${host}:8000/api/attachments/`
      processed = processed.replace(/(src=\")\/api\/attachments\//g, `$1${backendPrefix}`)
      processed = processed.replace(/(href=\")\/api\/attachments\//g, `$1${backendPrefix}`)
    }
  } catch (e) {
    // ignore
  }

  return marked(processed)
}

const renderedContent = computed(() => {
  // Kept for backward compatibility if needed, though we use contentBlocks now
  return marked(content.value) 
})

// Trigger fetch for drawings used in content
watch(contentBlocks, (newBlocks) => {
  newBlocks.forEach(block => {
    if (block.type === 'drawing' && block.content === '{}') {
       // We don't have the content, but notesStore.notes only has summaries.
       // We should fetch the full note if it's not already in a local cache.
       // For now, let's assume notesStore.fetchNote handles getting full content.
    }
  })
}, { immediate: true })

const wordCount = computed(() => content.value ? content.value.trim().split(/\s+/).filter(Boolean).length : 0)

let isRestoringScroll = false

function restoreScroll() {
  if (!note.value.id) return
  const targetId = note.value.id
  isRestoringScroll = true
  
  const pos = notesStore.getScrollPosition(targetId)
  
  const applyScroll = () => {
    if (note.value.id !== targetId) return
    if (pos) {
      if (textarea.value && pos.textarea !== undefined) {
        textarea.value.scrollTop = pos.textarea
      }
      if (previewPane.value && pos.preview !== undefined) {
        previewPane.value.scrollTop = pos.preview
      }
    }
  }

  // Try immediately
  nextTick(applyScroll)
  // Try after short delay for markdown render
  setTimeout(applyScroll, 50)
  // Try after longer delay for embedded drawings/iframes
  setTimeout(() => {
    applyScroll()
    // Re-enable saving scroll position
    isRestoringScroll = false
  }, 500)
}

function handleScroll(e) {
  if (!note.value.id || isRestoringScroll) return
  if (e.target === textarea.value) {
    notesStore.saveScrollPosition(note.value.id, { ...notesStore.getScrollPosition(note.value.id), textarea: e.target.scrollTop })
  } else if (e.target === previewPane.value) {
    notesStore.saveScrollPosition(note.value.id, { ...notesStore.getScrollPosition(note.value.id), preview: e.target.scrollTop })
  }
}

onMounted(() => { 
  if (notesStore.activeNote && notesStore.activeNote.type === 'markdown') {
    content.value = notesStore.activeNote.content || ''
    restoreScroll()
  } 
})
watch(() => notesStore.activeNote?.id, () => { 
  if (notesStore.activeNote && notesStore.activeNote.type === 'markdown') {
    content.value = notesStore.activeNote.content || '' 
    restoreScroll()
  }
})

async function handleInput(evt) {
  const el = textarea.value
  if (!el) return
  const cursorPos = el.selectionStart
  const textBefore = content.value.substring(0, cursorPos)

  // Only respond to user-generated input events to avoid triggering commands
  // when content is set programmatically (e.g., loading a note).
  if (!evt || !evt.isTrusted) {
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(() => notesStore.updateNote(note.value.id, content.value), 800)
    return
  }

  // Mark that the user has interacted via a trusted input event
  userInteracted.value = true

  // Check for /excali command - only if the last character was 'i' or pasted
  if (textBefore.endsWith('/excali')) {
    const newContent = content.value.substring(0, cursorPos - 7) + content.value.substring(cursorPos)
    content.value = newContent
    if (saveTimer) clearTimeout(saveTimer)
    await notesStore.updateNote(note.value.id, newContent)
    handleNewDrawing()
    return
  }

  // Check for /lorien command
  if (textBefore.endsWith('/lorien')) {
    const newContent = content.value.substring(0, cursorPos - 7) + content.value.substring(cursorPos)
    content.value = newContent
    if (saveTimer) clearTimeout(saveTimer)
    await notesStore.updateNote(note.value.id, newContent)
    handleNewLorien()
    return
  }

  // Check for /xopp command
  if (textBefore.endsWith('/xopp')) {
    const newContent = content.value.substring(0, cursorPos - 5) + content.value.substring(cursorPos)
    content.value = newContent
    if (saveTimer) clearTimeout(saveTimer)
    await notesStore.updateNote(note.value.id, newContent)
    handleNewXjournal()
    return
  }

  // Check for /upload command - only if the last character was 'd' or pasted
  if (textBefore.endsWith('/upload')) {
    // remove the command text and save the content, then open file picker
    const newContent = content.value.substring(0, cursorPos - 7) + content.value.substring(cursorPos)
    content.value = newContent
    if (saveTimer) clearTimeout(saveTimer)
    await notesStore.updateNote(note.value.id, newContent)

    // remember cursor position where files should be embedded
    lastCursorPos.value = cursorPos - 7
    
    // open file picker
    fileInput.value?.click()
    return
  }

  checkAutocomplete()
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => notesStore.updateNote(note.value.id, content.value), 800)
}

function getEmbedText(filename, mime) {
  if (!mime) return `![[${filename}]]`
  if (mime.startsWith('image/')) return `![[${filename}]]`
  if (mime.startsWith('video/')) return `\n<video controls src="${attachmentsApi.getUrl(filename)}" style="max-width:100%;">Your browser does not support the video tag.</video>\n`
  if (mime.startsWith('audio/')) return `\n<audio controls src="${attachmentsApi.getUrl(filename)}">Your browser does not support the audio element.</audio>\n`
  if (mime === 'application/pdf') {
    // Embed as a wiki attachment so the preview layer can render it with PdfViewer
    return `![[${filename}]]`
  }
  return `![[${filename}]]`
}

async function handleFileSelected(e) {
  const files = e.target?.files
  if (!files || files.length === 0) return
  const parentId = note.value.id
  let insertPos = lastCursorPos.value || textarea.value.selectionStart || 0
  let parentContent = content.value

  for (const file of files) {
    try {
      const { data } = await attachmentsApi.upload(file)
      const filename = data.filename
      const embed = getEmbedText(filename, file.type)
      parentContent = parentContent.substring(0, insertPos) + embed + parentContent.substring(insertPos)
      insertPos += embed.length
    } catch (err) {
      console.error('Upload failed:', err)
    }
  }

  // Update content and save
  content.value = parentContent
  await notesStore.updateNote(parentId, parentContent)

  // clear file input for next use
  if (fileInput.value) fileInput.value.value = null
}

function startTitleEdit() { titleDraft.value = note.value.title; editingTitle.value = true; nextTick(() => titleInput.value?.select()) }
async function saveTitle() {
  if (!titleDraft.value.trim() || titleDraft.value.trim() === note.value.title) { editingTitle.value = false; return }
  await notesStore.renameNote(note.value.id, titleDraft.value.trim())
  editingTitle.value = false; labelsStore.fetchLabels()
}
function cancelTitleEdit() { editingTitle.value = false }

async function toggleLabel(nodeId) {
  const labelName = nodeId.split(':')[1]
  const current = [...note.value.labels]
  const idx = current.indexOf(labelName)
  if (idx >= 0) current.splice(idx, 1); else current.push(labelName)
  await notesStore.updateNoteLabels(note.value.id, current); labelsStore.fetchLabels()
}

const lastCursorPos = ref(0)
function handleNewDrawing() {
  lastCursorPos.value = textarea.value.selectionStart
  newDrawingTitle.value = ''
  creationType.value = 'excalidraw'
  showNewDrawingModal.value = true
}

function handleNewLorien() {
  lastCursorPos.value = textarea.value.selectionStart
  newDrawingTitle.value = ''
  creationType.value = 'lorien'
  showNewDrawingModal.value = true
}

function handleNewXjournal() {
  lastCursorPos.value = textarea.value.selectionStart
  newDrawingTitle.value = ''
  creationType.value = 'xopp'
  showNewDrawingModal.value = true
}

async function createAndEmbedDrawing() {
  if (!newDrawingTitle.value.trim()) return
  const title = newDrawingTitle.value.trim()
  
  // Capture parent state before switching to drawing mode
  const parentId = note.value.id
  const parentContent = content.value
  const pos = lastCursorPos.value
  
  let type = 'excalidraw'
  if (creationType.value === 'lorien') type = 'lorien'
  else if (creationType.value === 'xopp') type = 'xopp'

  const setActive = type !== 'xopp'
  const drawing = await notesStore.createNote(title, '{}', [], type, setActive)
  if (drawing) {
    let ext = '.excalidraw'
    if (type === 'lorien') ext = '.lorien'
    else if (type === 'xopp') ext = '.xopp'

    const embedText = `\n![[${drawing.id}${ext}]]\n`
    const updatedParentContent = parentContent.substring(0, pos) + embedText + parentContent.substring(pos)
    
    // Explicitly update the PARENT note, not the active note (which is now the drawing)
    await notesStore.updateNote(parentId, updatedParentContent)
    
    showNewDrawingModal.value = false
    
    // Open the drawing immediately
    if (type === 'xopp') {
      notesStore.openXjournal(drawing.id)
      // Stay on current note
      notesStore.fetchNote(parentId)
    } else {
      notesStore.fetchNote(drawing.id)
    }
  } else {
    alert(notesStore.error || 'Failed to create file. A file with this name might already exist.')
  }
}

function checkAutocomplete() {
  const el = textarea.value
  if (!el) return
  const cursorPos = el.selectionStart
  const textBefore = content.value.substring(0, cursorPos)
  const match = textBefore.match(/\[\[([^\]]*?)$/)
  if (match) {
    autocompleteQuery.value = match[1]
    showAutocomplete.value = true
    autocompleteIndex.value = 0
    notesStore.searchNotes(match[1] || '').then(() => {
      autocompleteResults.value = notesStore.searchResults.filter(n => n.id !== note.value.id)
    })
    autocompletePosition.value = { top: '80px', left: '20px' }
  } else showAutocomplete.value = false
}

function insertAutocomplete(result) {
  const el = textarea.value
  const cursorPos = el.selectionStart
  const textBefore = content.value.substring(0, cursorPos)
  const textAfter = content.value.substring(cursorPos)
  const match = textBefore.match(/\[\[([^\]]*?)$/)
  if (match) {
    const start = cursorPos - match[1].length
    const isDrawing = result.type === 'excalidraw'
    const isLorien = result.type === 'lorien'
    const isXopp = result.type === 'xopp'
    const ext = isLorien ? '.lorien' : (isDrawing ? '.excalidraw' : (isXopp ? '.xopp' : ''))
    const prefix = (isDrawing || isLorien || isXopp) ? '!' : ''
    const insertText = prefix + '[[' + result.id + ext + ']]'
    content.value = textBefore.substring(0, start-2) + insertText + textAfter
    showAutocomplete.value = false
    handleInput()
  }
}

function handleKeydown(e) {
  if (showAutocomplete.value && autocompleteResults.value.length > 0) {
    if (e.key === 'ArrowDown') { e.preventDefault(); autocompleteIndex.value = (autocompleteIndex.value + 1) % autocompleteResults.value.length }
    else if (e.key === 'ArrowUp') { e.preventDefault(); autocompleteIndex.value = (autocompleteIndex.value - 1 + autocompleteResults.value.length) % autocompleteResults.value.length }
    else if (e.key === 'Enter' || e.key === 'Tab') { e.preventDefault(); insertAutocomplete(autocompleteResults.value[autocompleteIndex.value]) }
    else if (e.key === 'Escape') { showAutocomplete.value = false }
  }
}

function handlePreviewClick(e) {
  const link = e.target.closest('a.wikilink')
  if (link) {
     e.preventDefault()
     const noteId = link.getAttribute('data-link').replace('.excalidraw', '').replace('.lorien', '').replace('.xopp', '')
     notesStore.fetchNote(noteId)
     return
  }
  
  // Check if they clicked the edit button
  const editBtn = e.target.closest('.btn-edit-drawing')
  if (editBtn) return // Handled by inline @click on the button

  const drawing = e.target.closest('.drawing-preview-block')
  if (drawing) {
     // Skip if it's an xopp block, as we want to maintain context
     if (drawing.classList.contains('xjournal-block')) return

     // Find the drawing name from the pill or data
     let name = drawing.querySelector('.drawing-name-pill')?.textContent || ''
     name = name.replace(' (Lorien)', '').replace(' (Xjournal)', '').trim()
     
     if (name) {
       const type = drawing.classList.contains('lorien-block') ? 'lorien' : 'excalidraw'
       viewingDrawing.value = { name, type }
       viewerZoom.value = 1
     }
  }
}
async function handleDrop(e) {
  const files = e.dataTransfer?.files
  if (!files || files.length === 0) return
  for (const file of files) {
    try {
      const { data } = await attachmentsApi.upload(file)
      const insertText = `![[${data.filename}]]`
      const el = textarea.value
      const cursorPos = el.selectionStart
      content.value = content.value.substring(0, cursorPos) + insertText + content.value.substring(cursorPos)
      handleInput()
    } catch (err) { console.error('Upload failed:', err) }
  }
}

function confirmDelete() {
  if (confirm(`Delete "${note.value.title}"?`)) notesStore.deleteNote(note.value.id).then(() => labelsStore.fetchLabels())
}
</script>

<style scoped>
.editor-container { display: flex; flex-direction: column; height: 100%; background: var(--bg-root); position: relative; }
.editor-header { display: flex; align-items: center; justify-content: space-between; padding: var(--space-md) var(--space-xl); border-bottom: 1px solid var(--border-subtle); background: var(--bg-primary); min-height: 56px; flex-shrink: 0; }
.editor-title-area { display: flex; flex-direction: column; gap: var(--space-xs); min-width: 0; flex: 1; }
.editor-title { font-size: 1.25rem; font-weight: 600; letter-spacing: -0.02em; cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.editor-title:hover { color: var(--accent-secondary); }
.title-edit-input { font-size: 1.25rem; font-weight: 600; background: var(--bg-secondary); border: 1px solid var(--accent-primary); border-radius: var(--radius-sm); color: var(--text-primary); padding: 2px 8px; outline: none; }

.editor-actions { display: flex; align-items: center; gap: var(--space-sm); }
.btn-icon.active { color: var(--accent-primary); background: var(--accent-glow); }

.view-toggle { display: flex; background: var(--bg-secondary); border-radius: var(--radius-md); border: 1px solid var(--border-subtle); overflow: hidden; }
.toggle-btn { padding: 4px 12px; border: none; background: none; color: var(--text-tertiary); font-size: 0.75rem; font-weight: 500; cursor: pointer; }
.toggle-btn.active { background: var(--accent-primary); color: white; }

.label-picker { position: absolute; top: 60px; right: var(--space-xl); background: var(--bg-secondary); border: 1px solid var(--border-default); border-radius: var(--radius-md); padding: var(--space-md); box-shadow: var(--shadow-lg); z-index: 100; min-width: 220px; }

.editor-body { flex: 1; display: flex; overflow: hidden; }
.editor-body.split .edit-pane, .editor-body.split .preview-pane { width: 50%; }
.editor-body.edit .edit-pane { width: 100%; }
.editor-body.preview .preview-pane { width: 100%; }

.edit-pane { display: flex; flex-direction: column; overflow: hidden; border-right: 1px solid var(--border-subtle); }
.edit-area-wrapper { flex: 1; position: relative; overflow: hidden; }
.edit-textarea { width: 100%; height: 100%; padding: var(--space-xl); background: var(--bg-root); border: none; color: var(--text-primary); font-family: var(--font-mono); font-size: 0.875rem; line-height: 1.7; resize: none; outline: none; }

.preview-pane { overflow-y: auto; flex: 1; }
.preview-content { padding: var(--space-xl); max-width: 800px; margin: 0 auto; }
.preview-content :deep(a.wikilink) { color: var(--accent-secondary); background: var(--accent-glow); padding: 1px 6px; border-radius: var(--radius-sm); border: 1px solid rgba(99, 102, 241, 0.2); text-decoration: none; font-weight: 500; }

.drawing-preview-block {
  margin: 1.5rem 0;
  background: #ffffff; /* Excalidraw white background for visibility */
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-shadow: var(--shadow-sm);
}

.drawing-preview-block.xjournal-block {
  background: var(--bg-secondary);
}

.drawing-preview-block:hover {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-md);
}

.drawing-header-mini {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-subtle);
}

.drawing-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.drawing-name-pill {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.drawing-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-refresh-drawing {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-refresh-drawing:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--accent-primary);
}

.btn-edit-drawing {
  background: var(--accent-primary);
  color: white;
  border: none;
  border-radius: 4px;
  padding: 4px 10px;
  font-size: 0.7rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-edit-drawing:hover {
  opacity: 0.9;
}

.lorien-placeholder {
  height: 180px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  color: var(--text-tertiary);
  gap: 12px;
  font-size: 0.75rem;
}

.autocomplete-dropdown { position: absolute; background: var(--bg-elevated); border: 1px solid var(--border-strong); border-radius: var(--radius-md); box-shadow: var(--shadow-lg); z-index: 1000; min-width: 200px; }
.autocomplete-item { width: 100%; padding: 8px 12px; display: flex; align-items: center; gap: 8px; background: none; border: none; color: var(--text-primary); cursor: pointer; text-align: left; font-size: 0.8125rem; }
.autocomplete-item:hover, .autocomplete-item.active { background: var(--accent-primary); color: white; }
.ac-tag { font-size: 0.625rem; text-transform: uppercase; background: rgba(255, 255, 255, 0.2); padding: 1px 4px; border-radius: 4px; margin-left: auto; }
.autocomplete-footer { padding: 4px 12px; font-size: 0.65rem; color: var(--text-tertiary); background: var(--bg-secondary); border-top: 1px solid var(--border-subtle); }

.editor-status { display: flex; align-items: center; gap: var(--space-lg); padding: var(--space-xs) var(--space-xl); border-top: 1px solid var(--border-subtle); background: var(--bg-primary); flex-shrink: 0; }
.status-item { display: flex; align-items: center; gap: var(--space-xs); font-size: 0.6875rem; color: var(--text-tertiary); }

.modal-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 2000; }
.modal { width: 400px; background: var(--bg-secondary); border: 1px solid var(--border-default); border-radius: var(--radius-lg); padding: var(--space-xl); }
.modal-title { margin-bottom: var(--space-lg); }
.modal-actions { display: flex; justify-content: flex-end; gap: var(--space-sm); margin-top: var(--space-lg); }
.drawing-viewer-overlay { z-index: 3000; padding: 0; }
.drawing-viewer-modal { width: 100vw; height: 100vh; max-width: none; border-radius: 0; background: var(--bg-primary); display: flex; flex-direction: column; overflow: hidden; }
.viewer-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 20px; border-bottom: 1px solid var(--border-subtle); background: var(--bg-secondary); flex-shrink: 0; }
.viewer-title { display: flex; align-items: center; gap: 8px; font-weight: 600; color: var(--text-primary); }
.viewer-actions { display: flex; align-items: center; gap: 12px; }
.zoom-btn { background: var(--bg-tertiary); border: 1px solid var(--border-subtle); color: var(--text-primary); width: 28px; height: 28px; border-radius: 4px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-weight: bold; }
.zoom-level { font-size: 0.8rem; font-variant-numeric: tabular-nums; width: 40px; text-align: center; }
.viewer-body { flex: 1; overflow: auto; background: var(--bg-root); padding: 20px; display: flex; justify-content: center; align-items: flex-start; cursor: grab; }
.viewer-body.is-panning { cursor: grabbing; user-select: none; }
.viewer-canvas { transition: transform 0.1s ease-out; width: 100%; pointer-events: none; }
</style>
