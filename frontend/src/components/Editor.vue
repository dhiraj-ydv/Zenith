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
            @input="handleInput"
            @keydown="handleKeydown"
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
              <span v-if="result.type === 'excalidraw'" class="ac-tag">drawing</span>
            </button>
            <div class="autocomplete-footer" v-if="autocompleteQuery">
               Press Enter to link to "{{ autocompleteQuery }}"
            </div>
          </div>
        </div>
      </div>

      <div class="preview-pane" v-if="viewMode !== 'edit'">
        <div class="preview-content markdown-body" @click="handlePreviewClick">
          <template v-for="(block, idx) in contentBlocks" :key="idx">
             <div v-if="block.type === 'drawing'" class="drawing-preview-block">
                <div class="drawing-header-mini">
                  <span class="drawing-name-pill">{{ block.name }}</span>
                  <button class="btn-edit-drawing" @click="notesStore.fetchNote(block.name)">Edit Drawing</button>
                </div>
                <ExcalidrawPreview :content="block.content" :name="block.name" @edit="notesStore.fetchNote(block.name)" />
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
           <h3 class="modal-title">New Drawing</h3>
           <input type="text" class="input" placeholder="Drawing name..." v-model="newDrawingTitle" @keydown.enter="createAndEmbedDrawing" autofocus />
           <div class="modal-actions">
             <button class="btn btn-ghost" @click="showNewDrawingModal = false">Cancel</button>
             <button class="btn btn-primary" @click="createAndEmbedDrawing" :disabled="!newDrawingTitle.trim()">Create & Embed</button>
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

const notesStore = useNotesStore()
const labelsStore = useLabelsStore()

const content = ref('')
const viewMode = ref('split')
const editingTitle = ref(false)
const titleDraft = ref('')
const titleInput = ref(null)
const textarea = ref(null)
const showLabelPicker = ref(false)
const showNewDrawingModal = ref(false)
const newDrawingTitle = ref('')

const showAutocomplete = ref(false)
const autocompleteResults = ref([])
const autocompleteIndex = ref(0)
const autocompletePosition = ref({ top: '0px', left: '0px' })
const autocompleteQuery = ref('')

let saveTimer = null

const note = computed(() => notesStore.activeNote || { id: '', title: '', content: '', labels: [], links: [], attachments: [] })
const allLabels = computed(() => labelsStore.hierarchy.filter(h => h.id.startsWith('label:') || h.id.startsWith('feed:')))

const contentBlocks = computed(() => {
  if (!content.value) return [{ type: 'html', html: '<p style="color: var(--text-tertiary);">Nothing to preview</p>' }]
  
  const blocks = []
  // Match ![[...]] tags that end in .excalidraw
  const drawingRegex = /!\[\[([^\]]+?\.excalidraw)\]\]/g
  let lastIndex = 0
  let match

  while ((match = drawingRegex.exec(content.value)) !== null) {
    // Text before the drawing
    if (match.index > lastIndex) {
      const text = content.value.substring(lastIndex, match.index)
      blocks.push({ type: 'html', html: renderMarkdown(text) })
    }

    const drawingName = match[1].replace('.excalidraw', '')
    
    blocks.push({ 
      type: 'drawing', 
      name: drawingName, 
      content: '' // Let the preview component fetch its own content
    })

    lastIndex = drawingRegex.lastIndex
  }

  // Remaining text after last drawing
  if (lastIndex < content.value.length) {
    const text = content.value.substring(lastIndex)
    blocks.push({ type: 'html', html: renderMarkdown(text) })
  }

  return blocks
})

function renderMarkdown(text) {
  let processed = text.replace(
    /\[\[([^\]]+)\]\]/g,
    '<a class="wikilink" href="#" data-link="$1">$1</a>'
  )
  processed = processed.replace(
    /!\[\[([^\]]+)\]\]/g,
    (match, filename) => {
       if (filename.endsWith('.excalidraw')) return match // Should be handled by blocks logic
       return `<img src="${attachmentsApi.getUrl(filename)}" alt="${filename}" style="max-width:100%;border-radius:8px;margin:8px 0;" />`
    }
  )
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

onMounted(() => { if (notesStore.activeNote && notesStore.activeNote.type === 'markdown') content.value = notesStore.activeNote.content || '' })
watch(() => notesStore.activeNote?.id, () => { 
  if (notesStore.activeNote && notesStore.activeNote.type === 'markdown') {
    content.value = notesStore.activeNote.content || '' 
  }
})

async function handleInput() {
  const el = textarea.value
  const cursorPos = el.selectionStart
  const textBefore = content.value.substring(0, cursorPos)
  
  // Check for /excali command
  if (textBefore.endsWith('/excali')) {
    // 1. Remove /excali text
    const newContent = content.value.substring(0, cursorPos - 7) + content.value.substring(cursorPos)
    content.value = newContent
    
    // 2. Save immediately so state is clean
    if (saveTimer) clearTimeout(saveTimer)
    await notesStore.updateNote(note.value.id, newContent)

    // 3. Show drawing modal
    handleNewDrawing()
    return
  }

  checkAutocomplete()
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => notesStore.updateNote(note.value.id, content.value), 800)
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
  showNewDrawingModal.value = true
}

async function createAndEmbedDrawing() {
  if (!newDrawingTitle.value.trim()) return
  const title = newDrawingTitle.value.trim()
  
  // Capture parent state before switching to drawing mode
  const parentId = note.value.id
  const parentContent = content.value
  const pos = lastCursorPos.value
  
  const drawing = await notesStore.createNote(title, '{}', [], 'excalidraw')
  if (drawing) {
    const embedText = `\n![[${drawing.id}.excalidraw]]\n`
    const updatedParentContent = parentContent.substring(0, pos) + embedText + parentContent.substring(pos)
    
    // Explicitly update the PARENT note, not the active note (which is now the drawing)
    await notesStore.updateNote(parentId, updatedParentContent)
    
    showNewDrawingModal.value = false
    
    // Open the drawing immediately
    notesStore.fetchNote(drawing.id)
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
    const insertText = (isDrawing ? '!' : '') + '[[' + result.id + (isDrawing ? '.excalidraw' : '') + ']]'
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
  if (link) { e.preventDefault(); notesStore.fetchNote(link.getAttribute('data-link').replace('.excalidraw', '')) }
  const drawing = e.target.closest('.drawing-preview-block')
  if (drawing) { 
     // Find the drawing name from the pill or data
     const name = drawing.querySelector('.drawing-name-pill')?.textContent
     if (name) notesStore.fetchNote(name)
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

.drawing-name-pill {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
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
</style>
