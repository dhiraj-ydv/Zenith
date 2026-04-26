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
          id="edit-title-input"
        />
        <div class="editor-meta">
          <div class="meta-labels" v-if="note.labels.length > 0">
            <span class="badge" v-for="l in note.labels" :key="l">{{ l }}</span>
          </div>
          <span class="meta-links" v-if="note.links.length > 0">
            {{ note.links.length }} link{{ note.links.length !== 1 ? 's' : '' }}
          </span>
        </div>
      </div>
      <div class="editor-actions">
        <button 
          class="btn-icon tooltip" 
          data-tooltip="Add to Hierarchy" 
          @click="showLabelPicker = !showLabelPicker" 
          id="label-picker-toggle"
          :class="{ active: showLabelPicker }"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20.59 13.41L13.42 20.58C13.04 20.96 12.53 21.17 12 21.17C11.47 21.17 10.96 20.96 10.59 20.58L2 12V2H12L20.59 10.59C21.37 11.37 21.37 12.63 20.59 13.41Z"/>
            <line x1="7" y1="7" x2="7.01" y2="7"/>
          </svg>
        </button>
        <div class="view-toggle">
          <button
            class="toggle-btn"
            :class="{ active: viewMode === 'edit' }"
            @click="viewMode = 'edit'"
          >Edit</button>
          <button
            class="toggle-btn"
            :class="{ active: viewMode === 'split' }"
            @click="viewMode = 'split'"
          >Split</button>
          <button
            class="toggle-btn"
            :class="{ active: viewMode === 'preview' }"
            @click="viewMode = 'preview'"
          >Preview</button>
        </div>
        <button class="btn btn-danger" @click="confirmDelete" id="delete-note-button">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6V20C19 21.1 18.1 22 17 22H7C5.9 22 5 21.1 5 20V6M8 6V4C8 2.9 8.9 2 10 2H14C15.1 2 16 2.9 16 4V6"/>
          </svg>
        </button>
      </div>
    </header>

    <!-- Hierarchy Picker Dropdown (Mental Model: 'Add to Feed/Field') -->
    <div class="label-picker" v-if="showLabelPicker">
      <div class="picker-header">Add to Location</div>
      <div class="picker-scroll-area">
        <div class="label-picker-item" v-for="label in allLabels" :key="label.id">
          <label class="label-checkbox">
            <input
              type="checkbox"
              :checked="note.labels.includes(label.id.replace('label:', ''))"
              @change="toggleLabel(label.id)"
            />
            <span>{{ label.id.replace('label:', '') }}</span>
          </label>
        </div>
      </div>
      <div class="label-picker-empty" v-if="allLabels.length === 0">
        No feeds or labels yet.
      </div>
    </div>

    <!-- Editor Body -->
    <div class="editor-body" :class="viewMode">
      <!-- Edit Pane -->
      <div class="edit-pane" v-if="viewMode !== 'preview'">
        <div class="edit-area-wrapper" @dragover.prevent @drop.prevent="handleDrop">
          <textarea
            class="edit-textarea"
            v-model="content"
            @input="handleInput"
            @keydown="handleKeydown"
            ref="textarea"
            placeholder="Start writing... Use [[Note Title]] to link notes, ![[filename]] for attachments"
            spellcheck="false"
            id="note-editor-textarea"
          ></textarea>
          <!-- Link Autocomplete Dropdown -->
          <div
            class="autocomplete-dropdown"
            v-if="showAutocomplete && autocompleteResults.length > 0"
            :style="autocompletePosition"
          >
            <button
              v-for="(result, idx) in autocompleteResults"
              :key="result.id"
              class="autocomplete-item"
              :class="{ active: autocompleteIndex === idx }"
              @click="insertAutocomplete(result)"
            >
              {{ result.title }}
            </button>
          </div>
        </div>
      </div>

      <!-- Preview Pane -->
      <div class="preview-pane" v-if="viewMode !== 'edit'">
        <div class="preview-content markdown-body" v-html="renderedContent"></div>
      </div>
    </div>

    <!-- Status Bar -->
    <footer class="editor-status">
      <span class="status-item" v-if="notesStore.saving">
        <span class="saving-indicator"></span> Saving...
      </span>
      <span class="status-item" v-else>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        Saved
      </span>
      <span class="status-item">{{ wordCount }} words</span>
      <span class="status-item">{{ charCount }} chars</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { marked } from 'marked'
import { useNotesStore } from '../stores/notes'
import { useLabelsStore } from '../stores/labels'
import { attachmentsApi } from '../api/client'

const notesStore = useNotesStore()
const labelsStore = useLabelsStore()

const content = ref('')
const viewMode = ref('split')
const editingTitle = ref(false)
const titleDraft = ref('')
const titleInput = ref(null)
const textarea = ref(null)
const showLabelPicker = ref(false)

// Autocomplete state
const showAutocomplete = ref(false)
const autocompleteResults = ref([])
const autocompleteIndex = ref(0)
const autocompletePosition = ref({ top: '0px', left: '0px' })
const autocompleteQuery = ref('')

let saveTimer = null

const note = computed(() => notesStore.activeNote || { id: '', title: '', content: '', labels: [], links: [], attachments: [] })

// Filter all labels from hierarchy (exclude notes themselves from picker)
const allLabels = computed(() => labelsStore.hierarchy.filter(h => h.id.startsWith('label:')))

const renderedContent = computed(() => {
  if (!content.value) return '<p style="color: var(--text-tertiary);">Nothing to preview</p>'
  let processed = content.value.replace(
    /\[\[([^\]]+)\]\]/g,
    '<a class="wikilink" href="#" data-link="$1">$1</a>'
  )
  processed = processed.replace(
    /!\[\[([^\]]+)\]\]/g,
    (match, filename) => `<img src="${attachmentsApi.getUrl(filename)}" alt="${filename}" style="max-width:100%;border-radius:8px;margin:8px 0;" />`
  )
  return marked(processed)
})

const wordCount = computed(() => {
  if (!content.value) return 0
  return content.value.trim().split(/\s+/).filter(Boolean).length
})

const charCount = computed(() => content.value.length)

onMounted(() => {
  if (notesStore.activeNote) {
    content.value = notesStore.activeNote.content || ''
  }
})

watch(() => notesStore.activeNote?.id, () => {
  if (notesStore.activeNote) {
    content.value = notesStore.activeNote.content || ''
  }
})

function handleInput() {
  checkAutocomplete()
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    notesStore.updateNote(note.value.id, content.value)
  }, 800)
}

function startTitleEdit() {
  titleDraft.value = note.value.title
  editingTitle.value = true
  nextTick(() => titleInput.value?.select())
}

async function saveTitle() {
  if (!titleDraft.value.trim() || titleDraft.value.trim() === note.value.title) {
    editingTitle.value = false
    return
  }
  const result = await notesStore.renameNote(note.value.id, titleDraft.value.trim())
  editingTitle.value = false
  if (result) {
    await labelsStore.fetchLabels()
  }
}

function cancelTitleEdit() {
  editingTitle.value = false
}

// Label toggle (adds/removes 'mentions' in hierarchy)
async function toggleLabel(nodeId) {
  const labelName = nodeId.replace('label:', '')
  const current = [...note.value.labels]
  const idx = current.indexOf(labelName)
  
  if (idx >= 0) {
    current.splice(idx, 1)
  } else {
    current.push(labelName)
  }
  
  await notesStore.updateNoteLabels(note.value.id, current)
  await labelsStore.fetchLabels()
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
  } else {
    showAutocomplete.value = false
  }
}

function insertAutocomplete(result) {
  const el = textarea.value
  const cursorPos = el.selectionStart
  const textBefore = content.value.substring(0, cursorPos)
  const textAfter = content.value.substring(cursorPos)
  const match = textBefore.match(/\[\[([^\]]*?)$/)
  if (match) {
    const start = cursorPos - match[1].length
    content.value = textBefore.substring(0, start) + result.title + ']]' + textAfter
    showAutocomplete.value = false
    nextTick(() => {
      const newPos = start + result.title.length + 2
      el.selectionStart = newPos; el.selectionEnd = newPos; el.focus()
    })
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
  if (confirm(`Delete "${note.value.title}"? This cannot be undone.`)) {
    notesStore.deleteNote(note.value.id).then(() => {
      labelsStore.fetchLabels()
    })
  }
}
</script>

<style scoped>
.editor-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-root);
}

.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-xl);
  border-bottom: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  min-height: 56px;
  flex-shrink: 0;
}

.editor-title-area {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  min-width: 0;
  flex: 1;
}
.editor-title {
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color var(--transition-fast);
}
.editor-title:hover {
  color: var(--accent-secondary);
}

.title-edit-input {
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  background: var(--bg-secondary);
  border: 1px solid var(--accent-primary);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  padding: 2px 8px;
  outline: none;
  box-shadow: 0 0 0 3px var(--accent-glow);
}

.editor-meta {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}
.meta-labels {
  display: flex;
  gap: var(--space-xs);
}
.meta-links {
  font-size: 0.6875rem;
  color: var(--text-tertiary);
}

.editor-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.btn-icon.active {
  color: var(--accent-primary);
  background: var(--accent-glow);
}

/* View Toggle */
.view-toggle {
  display: flex;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
}
.toggle-btn {
  padding: 4px 12px;
  border: none;
  background: none;
  color: var(--text-tertiary);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.toggle-btn.active {
  background: var(--accent-primary);
  color: white;
}
.toggle-btn:hover:not(.active) {
  color: var(--text-primary);
  background: var(--bg-hover);
}

/* Label Picker */
.label-picker {
  position: absolute;
  top: 60px;
  right: var(--space-xl);
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  box-shadow: var(--shadow-lg);
  z-index: 100;
  min-width: 220px;
  max-height: 400px;
  display: flex;
  flex-direction: column;
  animation: fadeIn var(--transition-fast) ease-out;
}
.picker-header {
  font-size: 0.625rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-tertiary);
  margin-bottom: var(--space-sm);
  letter-spacing: 0.05em;
}
.picker-scroll-area {
  overflow-y: auto;
  flex: 1;
}
.label-picker-item {
  padding: var(--space-xs) 0;
}
.label-checkbox {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  cursor: pointer;
  font-size: 0.8125rem;
  color: var(--text-secondary);
  transition: color var(--transition-fast);
}
.label-checkbox:hover {
  color: var(--text-primary);
}
.label-checkbox input[type="checkbox"] {
  accent-color: var(--accent-primary);
}
.label-picker-empty {
  padding: var(--space-sm);
  color: var(--text-tertiary);
  font-size: 0.8125rem;
  text-align: center;
}

.editor-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}
.editor-body.split .edit-pane,
.editor-body.split .preview-pane {
  width: 50%;
}
.editor-body.edit .edit-pane {
  width: 100%;
}
.editor-body.preview .preview-pane {
  width: 100%;
}

.edit-pane {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: 1px solid var(--border-subtle);
}
.edit-area-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
}
.edit-textarea {
  width: 100%;
  height: 100%;
  padding: var(--space-xl);
  background: var(--bg-root);
  border: none;
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 0.875rem;
  line-height: 1.7;
  resize: none;
  outline: none;
  tab-size: 2;
  overflow-y: auto;
}

.preview-pane {
  overflow-y: auto;
}
.preview-content {
  padding: var(--space-xl);
  max-width: 720px;
}

.preview-content :deep(a.wikilink) {
  color: var(--accent-secondary);
  background: var(--accent-glow);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  border: 1px solid rgba(99, 102, 241, 0.2);
  text-decoration: none;
  font-weight: 500;
}

.editor-status {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  padding: var(--space-xs) var(--space-xl);
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  flex-shrink: 0;
}
.status-item {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.6875rem;
  color: var(--text-tertiary);
}
.saving-indicator {
  width: 6px; height: 6px; border-radius: 50%; background: var(--color-warning);
  animation: pulseGlow 1s infinite;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
</style>
