<template>
  <aside class="sidebar">
    <!-- Logo / Brand -->
    <div class="sidebar-brand">
      <div class="brand-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="url(#grad)" opacity="0.9"/>
          <path d="M2 17L12 22L22 17" stroke="url(#grad)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
          <path d="M2 12L12 17L22 12" stroke="url(#grad)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
          <defs>
            <linearGradient id="grad" x1="2" y1="2" x2="22" y2="22">
              <stop offset="0%" stop-color="#818cf8"/>
              <stop offset="100%" stop-color="#6366f1"/>
            </linearGradient>
          </defs>
        </svg>
      </div>
      <span class="brand-text">Zenith</span>
      <button class="btn-icon graph-toggle tooltip" data-tooltip="Knowledge Graph" @click="$emit('toggle-graph')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="6" cy="6" r="3"/>
          <circle cx="18" cy="6" r="3"/>
          <circle cx="12" cy="18" r="3"/>
          <path d="M8.5 7.5L10.5 16" />
          <path d="M15.5 7.5L13.5 16" />
        </svg>
      </button>
    </div>

    <!-- Top Actions (Switch Vault) -->
    <div class="sidebar-top-actions">
      <button class="btn btn-ghost switch-vault-btn" @click="$emit('switch-vault')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
          <polyline points="9 22 9 12 15 12 15 22"></polyline>
        </svg>
        Switch Vault
      </button>
    </div>

    <!-- View Toggle -->
    <div class="sidebar-view-toggle">
      <div class="toggle-group">
        <button 
          :class="{ active: viewMode === 'feeds' }" 
          @click="viewMode = 'feeds'"
        >
          Feeds
        </button>
        <button 
          :class="{ active: viewMode === 'library' }" 
          @click="viewMode = 'library'"
        >
          Library
        </button>
      </div>
    </div>

    <!-- Creation Actions (New button) -->
    <div class="sidebar-actions">
      <!-- Library View -> New Note -->
      <button v-if="viewMode === 'library'" class="btn btn-primary new-action-btn" @click="handleNewNoteAction">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 5V19M5 12H19"/>
        </svg>
        New Note
      </button>

      <!-- Feeds Root -> New Feed -->
      <button v-else-if="!labelsStore.activeFeedId" class="btn btn-primary new-action-btn" @click="handleNewLabelAction(true)">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 5V19M5 12H19"/>
        </svg>
        New Feed
      </button>

      <!-- Focused Feed -> New Label -->
      <button v-else class="btn btn-primary new-action-btn" @click="handleNewLabelAction(false)">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 5V19M5 12H19"/>
        </svg>
        New Label
      </button>
    </div>

    <!-- Search (Moved below New) -->
    <div class="sidebar-search">
      <div class="search-input-wrapper">
        <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <path d="M21 21L16.65 16.65"/>
        </svg>
        <input
          type="text"
          class="search-input"
          placeholder="Search..."
          v-model="activeSearchQuery"
        />
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="sidebar-section tree-section">
      <!-- Library Mode -->
      <div v-if="viewMode === 'library'" class="library-list">
        <button
          v-for="note in filteredLibraryNotes"
          :key="note.id"
          class="note-item"
          :class="{ active: notesStore.activeNote?.id === note.id }"
          @click="$emit('select-note', note.id)"
          draggable="true"
          @dragstart="onDragStartLibraryNote($event, note.id)"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M14 2H6C4.89 2 4 2.9 4 4V20C4 21.1 4.89 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z"/><path d="M14 2V8H20"/>
          </svg>
          <span class="note-title">{{ note.title }}</span>
        </button>
      </div>

      <!-- Feeds Mode -->
      <div v-else class="feeds-container">
        <!-- Root Feeds List -->
        <div v-if="!labelsStore.activeFeedId" class="feeds-list">
          <div class="section-header">
             <span class="section-title">Feeds</span>
          </div>
          <button 
            v-for="feed in filteredRootFeeds" 
            :key="feed.id" 
            class="feed-card"
            @click="labelsStore.setFeed(feed.id)"
          >
            <svg v-if="feed.id.startsWith('label:')" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            </svg>
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6C4.89 2 4 2.9 4 4V20C4 21.1 4.89 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z"/><path d="M14 2V8H20"/>
            </svg>
            <span class="feed-name">{{ getDisplayName(feed.id) }}</span>
            <svg class="arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M9 18l6-6-6-6" />
            </svg>
          </button>
        </div>

        <!-- Focused Hierarchy View -->
        <div v-else class="focused-feed">
          <div class="feed-header">
            <button class="btn-icon back-btn" @click="labelsStore.setFeed(null)">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M15 18l-6-6 6-6" />
              </svg>
            </button>
            <span class="active-feed-title">{{ activeFeedDisplayName }}</span>
          </div>
          <div class="hierarchy-list">
             <HierarchyItem 
              v-for="node in filteredFocusedTree" 
              :key="node.id" 
              :node="node"
              @select-note="(id) => $emit('select-note', id)"
            />
            <div v-if="filteredFocusedTree.length === 0" class="empty-feed">
              {{ focusedSearchQuery ? 'No matches found' : 'Empty Feed' }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <Teleport to="body">
      <div class="modal-overlay" v-if="showNewNoteModal" @click.self="showNewNoteModal = false">
        <div class="modal fade-in">
          <h3 class="modal-title">Create New Note</h3>
          <input
            type="text"
            class="input"
            placeholder="Note title..."
            v-model="newNoteTitle"
            @keydown.enter="createNote"
            ref="newNoteTitleInput"
            autofocus
          />
          <div class="modal-actions">
            <button class="btn btn-ghost" @click="showNewNoteModal = false">Cancel</button>
            <button class="btn btn-primary" @click="createNote" :disabled="!newNoteTitle.trim()">Create</button>
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div class="modal-overlay" v-if="showNewLabelModal" @click.self="showNewLabelModal = false">
        <div class="modal fade-in">
          <h3 class="modal-title">{{ isCreatingFeed ? 'Create New Feed' : 'Create Label' }}</h3>
          <input
            type="text"
            class="input"
            placeholder="Name..."
            v-model="newLabelName"
            @keydown.enter="createLabel"
            autofocus
          />
          <div class="modal-actions">
            <button class="btn btn-ghost" @click="showNewLabelModal = false">Cancel</button>
            <button class="btn btn-primary" @click="createLabel" :disabled="!newLabelName.trim()">Create</button>
          </div>
        </div>
      </div>
    </Teleport>
  </aside>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useNotesStore } from '../stores/notes'
import { useLabelsStore } from '../stores/labels'
import HierarchyItem from './HierarchyItem.vue'

const emit = defineEmits(['select-note', 'new-note', 'toggle-graph', 'switch-vault'])

const notesStore = useNotesStore()
const labelsStore = useLabelsStore()

const viewMode = ref('feeds')
const showNewNoteModal = ref(false)
const showNewLabelModal = ref(false)
const isCreatingFeed = ref(false)
const newNoteTitle = ref('')
const newLabelName = ref('')
const newNoteTitleInput = ref(null)

// Independent Search Queries
const feedsRootSearchQuery = ref('')
const focusedSearchQuery = ref('')
const librarySearchQuery = ref('')

const activeSearchQuery = computed({
  get: () => {
    if (viewMode.value === 'library') return librarySearchQuery.value
    if (labelsStore.activeFeedId) return focusedSearchQuery.value
    return feedsRootSearchQuery.value
  },
  set: (val) => {
    if (viewMode.value === 'library') librarySearchQuery.value = val
    else if (labelsStore.activeFeedId) focusedSearchQuery.value = val
    else feedsRootSearchQuery.value = val
  }
})

const vClickOutside = {
  mounted(el, binding) {
    el.clickOutsideEvent = (event) => {
      if (!(el === event.target || el.contains(event.target))) {
        binding.value()
      }
    }
    document.addEventListener('click', el.clickOutsideEvent)
  },
  unmounted(el) {
    document.removeEventListener('click', el.clickOutsideEvent)
  }
}

// Filtered Lists
const filteredLibraryNotes = computed(() => {
  const all = [...notesStore.notes].sort((a, b) => a.title.localeCompare(b.title))
  if (!librarySearchQuery.value) return all
  const q = librarySearchQuery.value.toLowerCase()
  return all.filter(n => n.title.toLowerCase().includes(q))
})

const filteredRootFeeds = computed(() => {
  const all = [...labelsStore.rootFeeds].sort((a, b) => getDisplayName(a.id).localeCompare(getDisplayName(b.id)))
  if (!feedsRootSearchQuery.value) return all
  const q = feedsRootSearchQuery.value.toLowerCase()
  return all.filter(f => getDisplayName(f.id).toLowerCase().includes(q))
})

const filteredFocusedTree = computed(() => {
  const tree = labelsStore.selectedFeedTree
  if (!focusedSearchQuery.value) return tree
  
  const q = focusedSearchQuery.value.toLowerCase()
  
  function filterNodes(nodes) {
    return nodes.map(node => {
      const name = getDisplayName(node.id).toLowerCase()
      const filteredChildren = filterNodes(node.resolvedChildren)
      
      if (name.includes(q) || filteredChildren.length > 0) {
        return { ...node, resolvedChildren: filteredChildren }
      }
      return null
    }).filter(Boolean)
  }
  
  return filterNodes(tree)
})

const activeFeedDisplayName = computed(() => {
  if (!labelsStore.activeFeedId) return ''
  return getDisplayName(labelsStore.activeFeedId)
})

function getDisplayName(id) {
  if (id.startsWith('label:')) return id.replace('label:', '', 1)
  const noteId = id.replace('note:', '', 1)
  const note = notesStore.noteById(noteId)
  return note ? note.title : noteId
}

watch(showNewNoteModal, (val) => {
  if (val) {
    newNoteTitle.value = ''
    nextTick(() => newNoteTitleInput.value?.focus())
  }
})

function handleNewNoteAction() {
  showNewNoteModal.value = true
}

function handleNewLabelAction(asFeed = false) {
  isCreatingFeed.value = asFeed
  showNewLabelModal.value = true
}

function onDragStartLibraryNote(event, noteId) {
  event.dataTransfer.setData('nodeId', `note:${noteId}`)
  event.dataTransfer.effectAllowed = 'copyMove'
}

async function createNote() {
  if (!newNoteTitle.value.trim()) return
  
  let labels = []
  if (viewMode.value === 'feeds') {
    if (labelsStore.activeLabel && labelsStore.activeLabel.startsWith('label:')) {
      labels = [labelsStore.activeLabel.replace('label:', '', 1)]
    } else if (labelsStore.activeFeedId && labelsStore.activeFeedId.startsWith('label:')) {
      labels = [labelsStore.activeFeedId.replace('label:', '', 1)]
    }
  }
  
  const note = await notesStore.createNote(newNoteTitle.value.trim(), '', labels)
  if (note) {
    showNewNoteModal.value = false
    emit('select-note', note.id)
    emit('new-note')
    await labelsStore.fetchLabels()
  }
}

async function createLabel() {
  if (!newLabelName.value.trim()) return
  const name = newLabelName.value.trim()
  
  const result = await labelsStore.createLabel(name)
  if (result) {
    if (!isCreatingFeed.value) {
      const targetParent = labelsStore.activeLabel || labelsStore.activeFeedId
      if (targetParent) {
         await labelsStore.moveLabel(result.id, targetParent)
      }
    }
  }
  
  showNewLabelModal.value = false
  newLabelName.value = ''
}

defineExpose({
  showNewNoteModal
})
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  border-right: 1px solid var(--border-subtle);
  overflow: hidden;
  flex-shrink: 0;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg) var(--space-lg) var(--space-sm);
}
.brand-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-glow);
  border-radius: var(--radius-md);
  border: 1px solid rgba(99, 102, 241, 0.15);
}
.brand-text {
  font-size: 1.125rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, var(--accent-secondary), var(--accent-primary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  flex: 1;
}
.graph-toggle {
  opacity: 0.6;
  transition: opacity var(--transition-fast);
}
.graph-toggle:hover {
  opacity: 1;
}

.sidebar-top-actions {
  padding: 0 var(--space-lg) var(--space-md);
}
.switch-vault-btn {
  width: 100%;
  justify-content: flex-start;
  font-size: 0.75rem;
  color: var(--text-tertiary);
  gap: var(--space-sm);
  padding: 8px var(--space-md);
}

.sidebar-view-toggle {
  padding: 0 var(--space-lg) var(--space-md);
}
.toggle-group {
  display: flex;
  background: var(--bg-secondary);
  padding: 4px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
}
.toggle-group button {
  flex: 1;
  padding: 6px;
  border: none;
  background: none;
  color: var(--text-tertiary);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}
.toggle-group button:hover {
  color: var(--text-secondary);
}
.toggle-group button.active {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}

.sidebar-actions {
  padding: 0 var(--space-lg) var(--space-sm);
}
.new-action-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  font-size: 0.8125rem;
}

.sidebar-search {
  padding: 0 var(--space-lg) var(--space-md);
}
.search-input-wrapper {
  position: relative;
}
.search-icon {
  position: absolute;
  left: var(--space-md);
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-tertiary);
  pointer-events: none;
}
.search-input {
  width: 100%;
  padding: var(--space-sm) var(--space-md) var(--space-sm) 36px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 0.8125rem;
  outline: none;
  transition: all var(--transition-fast);
}
.search-input:focus {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

.tree-section {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.library-list, .feeds-list, .hierarchy-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.section-header {
  padding: 0 var(--space-lg) var(--space-sm);
}
.section-title {
  font-size: 0.625rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-tertiary);
  letter-spacing: 0.05em;
  opacity: 0.6;
}

.feed-card {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: 10px var(--space-lg);
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
  text-align: left;
  border-radius: var(--radius-md);
  margin: 0 8px;
}
.feed-card:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
  transform: translateX(4px);
}
.feed-card svg {
  color: var(--accent-secondary);
}
.feed-card .arrow {
  margin-left: auto;
  opacity: 0;
  transition: opacity var(--transition-fast);
}
.feed-card:hover .arrow {
  opacity: 0.5;
}

.focused-feed {
  display: flex;
  flex-direction: column;
}
.feed-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm) var(--space-lg);
  margin-bottom: var(--space-sm);
  border-bottom: 1px solid var(--border-subtle);
}
.active-feed-title {
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.back-btn {
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
}

.note-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 6px var(--space-lg);
  border: none;
  background: none;
  color: var(--text-secondary);
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all var(--transition-fast);
  text-align: left;
  width: 100%;
  user-select: none;
}
.library-list .note-item {
  padding-left: 24px;
}
.note-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.note-item.active {
  background: var(--accent-glow);
  color: var(--accent-secondary);
  border-left: 2px solid var(--accent-primary);
}
.note-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.empty-feed {
  padding: var(--space-xl);
  text-align: center;
  color: var(--text-tertiary);
  font-size: 0.75rem;
  font-style: italic;
}

/* Modals */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  width: 400px;
  max-width: 90vw;
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  box-shadow: var(--shadow-lg);
}
.modal-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: var(--space-lg);
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  margin-top: var(--space-lg);
}
</style>
