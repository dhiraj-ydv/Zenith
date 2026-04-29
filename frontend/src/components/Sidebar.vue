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
      <button class="btn-icon graph-toggle tooltip" data-tooltip="Knowledge Graph" @click="handleToggleGraph">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 2L12 22M2 12L22 12M12 2L22 12L12 22L2 12L12 2"/>
        </svg>
      </button>
    </div>

    <!-- Top Actions -->
    <div class="sidebar-top-actions">
      <button class="btn btn-ghost switch-vault-btn" @click="$emit('switch-vault')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
          <polyline points="9 22 9 12 15 12 15 22"></polyline>
        </svg>
        Switch Vault
      </button>
    </div>

    <!-- Main Content Area -->
    <div class="sidebar-actions-container">
      <div class="contextual-header">
         <template v-if="!labelsStore.activeFeedId">
            <div class="sidebar-header-bar library-header"
              :class="{ 'drag-over': dragOverTarget === 'root' }"
              @dragover.prevent="dragOverTarget = 'root'"
              @dragleave="dragOverTarget = null"
              @drop.stop="onDropOnRoot($event)"
            >
               <h2 class="sidebar-title">Library</h2>
               <div class="header-pill-group">
                  <button :class="{ active: rootFilter === 'all' }" @click="rootFilter = 'all'">All</button>
                  <button :class="{ active: rootFilter === 'feeds' }" @click="rootFilter = 'feeds'">Feeds</button>
                  <button :class="{ active: rootFilter === 'notes' }" @click="rootFilter = 'notes'">Notes</button>
               </div>
            </div>
            <div class="sidebar-actions grid">
              <button class="btn btn-primary action-btn-sm" @click="handleNewFeedRootAction" title="New Feed">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5V19M5 12H19"/></svg>
                Feed
              </button>
              <button class="btn btn-primary action-btn-sm" @click="handleNewNoteAction" title="New Note">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5V19M5 12H19"/></svg>
                Note
              </button>
            </div>
         </template>
         <template v-else>
            <div class="sidebar-header nav-header">
              <button class="btn-icon back-btn" :class="{ 'drag-over': dragOverTarget === 'back' }" @click="labelsStore.setFeed(null)" @dragover.prevent="handleBackDragOver" @dragleave="handleBackDragLeave" @drop.stop="onDropOnRoot($event)">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 18l-6-6 6-6" /></svg>
              </button>
              <h2 class="sidebar-title active-title">{{ labelsStore.activeFeedDisplayName }}</h2>
            </div>
            <div class="sidebar-actions grid">
              <button class="btn btn-primary action-btn-sm" @click="handleNewLabelAction" title="New Label">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5V19M5 12H19"/></svg>
                Label
              </button>
              <button class="btn btn-primary action-btn-sm" @click="handleNewNoteAction" title="New Note">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5V19M5 12H19"/></svg>
                Note
              </button>
            </div>
         </template>
      </div>
    </div>

    <!-- Search -->
    <div class="sidebar-search">
      <div class="search-input-wrapper">
        <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <path d="M21 21L16.65 16.65"/>
        </svg>
        <input
          type="text"
          class="search-input"
          :placeholder="labelsStore.activeFeedId ? 'Search feed...' : 'Search library...'"
          v-model="activeSearchQuery"
        />
      </div>
    </div>

    <!-- Navigation Area -->
    <div class="sidebar-section tree-section">
      
      <!-- Root View -->
      <div v-if="!labelsStore.activeFeedId" class="feed-root-view">
         <!-- feeds List -->
         <div v-if="rootFilter !== 'notes'" class="nav-list">
            <button 
              v-for="feed in filteredRootFeeds" 
              :key="feed.id" 
              class="nav-card"
              :class="{ 'drag-over': dragOverTarget === feed.id }"
              @click="labelsStore.setFeed(feed.id)"
              @dragover.prevent="handleFeedDragOver($event, feed.id)"
              @dragleave="handleFeedDragLeave"
              @drop.stop="onDropOnFeed($event, feed.id)"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                <polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>
              </svg>
              <span class="nav-name">{{ feed.id.split(':')[1] }}</span>
              <svg class="arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M9 18l6-6-6-6" />
              </svg>
            </button>
         </div>

         <hr class="sidebar-divider" v-if="rootFilter === 'all' && filteredRootFeeds.length > 0 && filteredRootNotes.length > 0" />

         <!-- root notes List -->
         <div v-if="rootFilter !== 'feeds'" class="nav-list">
            <button
              v-for="note in filteredRootNotes"
              :key="note.id"
              class="note-item root-level-note"
              :class="{ active: notesStore.activeNote?.id === note.id }"
              @click="$emit('select-note', note.id)"
              draggable="true"
              @dragstart="onDragStartLibraryNote($event, note.id)"
            >
              <svg v-if="note.type === 'excalidraw'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/><path d="M2 2l5 2"/><path d="M2 2l2 5"/>
              </svg>
              <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6C4.89 2 4 2.9 4 4V20C4 21.1 4.89 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z"/><path d="M14 2V8H20"/>
              </svg>
              <span class="note-title">{{ note.title }}</span>
            </button>
         </div>
         
         <div v-if="filteredRootFeeds.length === 0 && filteredRootNotes.length === 0" class="empty-state">
            Empty Library
         </div>
      </div>

      <!-- Focused Feed View -->
      <div v-else class="focused-view">
          <div class="hierarchy-list">
             <HierarchyItem 
             v-for="(node, index) in filteredFocusedTree" 
              :key="node.id" 
              :node="node"
              :parent-id="labelsStore.activeFeedId"
              :sibling-index="index"
              :sibling-count="filteredFocusedTree.length"
              @select-note="(id) => $emit('select-note', id)"
              @request-create="handleHierarchyCreate"
              @request-move-root="moveNodeToFeedRoot"
              @request-move-library-root="moveNodeToLibraryRoot"
              @request-move-other-feed="openMoveFeedModal"
            />
            <div v-if="filteredFocusedTree.length === 0" class="empty-state">
              {{ focusedSearchQuery ? 'No matches found' : 'Empty Feed' }}
            </div>
          </div>
      </div>

    </div>

    <!-- Modals -->
    <Teleport to="body">
      <div class="modal-overlay" v-if="showNewNoteModal" @click.self="showNewNoteModal = false">
        <div class="modal fade-in">
          <h3 class="modal-title">{{ modalTitle }}</h3>
          <input type="text" class="input" placeholder="Title..." v-model="newNoteTitle" @keydown.enter="createNote" ref="newNoteTitleInput" autofocus />
          <div class="modal-actions">
            <button class="btn btn-ghost" @click="showNewNoteModal = false">Cancel</button>
            <button class="btn btn-primary" @click="createNote" :disabled="!newNoteTitle.trim()">Create</button>
          </div>
        </div>
      </div>
      
      <div class="modal-overlay" v-if="showNewLabelModal" @click.self="showNewLabelModal = false">
        <div class="modal fade-in">
          <h3 class="modal-title">{{ modalTitle }}</h3>
          <input type="text" class="input" placeholder="Name..." v-model="newLabelName" @keydown.enter="createGenericLabel" autofocus />
          <div class="modal-actions">
            <button class="btn btn-ghost" @click="showNewLabelModal = false">Cancel</button>
            <button class="btn btn-primary" @click="createGenericLabel" :disabled="!newLabelName.trim()">Create</button>
          </div>
        </div>
      </div>

      <div class="modal-overlay" v-if="showMoveFeedModal" @click.self="closeMoveFeedModal">
        <div class="modal fade-in move-feed-modal">
          <div class="move-feed-header">
            <button v-if="moveFeedStep === 'placement'" class="btn-icon back-btn move-feed-back" @click="moveFeedStep = 'feeds'; moveFeedQuery = ''">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 18l-6-6 6-6" /></svg>
            </button>
            <h3 class="modal-title">{{ moveFeedStep === 'feeds' ? 'Move To Other Feed' : `Place In ${movePlacementFeedId?.split(':')[1] || ''}` }}</h3>
          </div>
          <input
            ref="moveFeedInput"
            type="text"
            class="input"
            :placeholder="moveFeedStep === 'feeds' ? 'Search feeds...' : 'Search inside feed...'"
            v-model="moveFeedQuery"
          />
          <div class="move-feed-list">
            <template v-if="moveFeedStep === 'feeds'">
              <button
                class="move-feed-item"
                :class="{ active: selectedMoveFeedTarget === '__root__' }"
                @click="selectedMoveFeedTarget = '__root__'"
              >
                <div class="move-feed-main">
                  <span class="move-feed-name">Library Root</span>
                  <span class="move-feed-path">Move out of feeds</span>
                </div>
                <button
                  class="move-feed-icon minus icon-action-btn"
                  title="Move to library root"
                  @click.stop="moveNodeDirectlyToTarget('__root__')"
                >
                  -
                </button>
              </button>

              <button
                v-for="feed in fuzzyFilteredFeeds"
                :key="feed.id"
                class="move-feed-item"
                :class="{ active: selectedMoveFeedTarget === feed.id }"
                @click="openPlacementStep(feed.id)"
              >
                <div class="move-feed-main">
                  <span class="move-feed-name">{{ feed.id.split(':')[1] }}</span>
                  <span class="move-feed-path">{{ feed.id }}</span>
                </div>
                <button
                  class="move-feed-icon plus icon-action-btn"
                  title="Open feed placement"
                  @click.stop="openPlacementStep(feed.id)"
                >
                  +
                </button>
              </button>

              <div v-if="fuzzyFilteredFeeds.length === 0" class="move-feed-empty">
                No feeds match your search
              </div>
            </template>

            <template v-else>
              <button class="move-feed-item root-option" @click="moveNodeToFeedRootOf(movePlacementFeedId)">
                <div class="move-feed-main">
                  <span class="move-feed-name">Feed Root</span>
                  <span class="move-feed-path">Place directly under {{ movePlacementFeedId?.split(':')[1] }}</span>
                </div>
                <span class="move-feed-icon plus">+</span>
              </button>

              <MovePlacementItem
                v-for="(node, index) in movePlacementTree"
                :key="node.id"
                :node="node"
                :parent-id="movePlacementFeedId"
                :sibling-index="index"
                @place-child="placeMovedNodeInside"
                @place-parent="placeMovedNodeAsParent"
                @place-sibling="placeMovedNodeAsSibling"
              />

              <div v-if="movePlacementTree.length === 0" class="move-feed-empty">
                No matching targets in this feed
              </div>
            </template>
          </div>
          <div class="modal-actions">
            <button class="btn btn-ghost" @click="closeMoveFeedModal">Cancel</button>
            <button v-if="moveFeedStep === 'feeds'" class="btn btn-primary" :disabled="!selectedMoveFeedTarget" @click="confirmMoveToFeed">Select</button>
            <button v-else class="btn btn-primary" @click="moveNodeToFeedRootOf(movePlacementFeedId)">Place At Feed Root</button>
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
import { useGraphStore } from '../stores/graph'
import HierarchyItem from './HierarchyItem.vue'
import MovePlacementItem from './MovePlacementItem.vue'

const emit = defineEmits(['select-note', 'new-note', 'toggle-graph', 'switch-vault'])

const notesStore = useNotesStore()
const labelsStore = useLabelsStore()
const graphStore = useGraphStore()

const rootFilter = ref('all') 
const showNewNoteModal = ref(false)
const showNewLabelModal = ref(false)
const showMoveFeedModal = ref(false)
const newNoteTitle = ref('')
const newLabelName = ref('')
const newNoteTitleInput = ref(null)
const moveFeedInput = ref(null)
const dragOverTarget = ref(null)
const creationPlan = ref(null)
const moveFeedNodeId = ref(null)
const moveFeedQuery = ref('')
const selectedMoveFeedTarget = ref('')
const moveFeedStep = ref('feeds')
const movePlacementFeedId = ref(null)
let backHoverTimer = null
let feedHoverTimer = null

const creationType = ref('feed') 

const modalTitle = computed(() => {
  if (creationType.value === 'feed') return 'Create New Feed'
  if (creationType.value === 'drawing') return 'Create New Excalidraw'
  if (creationType.value === 'lorien') return 'Create New Lorien'
  if (creationType.value === 'xopp') return 'Create New Xournal++'
  if (creationType.value === 'note') return 'Create New Note'
  return 'Create New Label'
})

// Independent Search Queries
const libraryRootSearchQuery = ref('')
const focusedSearchQuery = ref('')

const activeSearchQuery = computed({
  get: () => {
    return labelsStore.activeFeedId ? focusedSearchQuery.value : libraryRootSearchQuery.value
  },
  set: (val) => {
    if (labelsStore.activeFeedId) focusedSearchQuery.value = val
    else libraryRootSearchQuery.value = val
  }
})

// Filtered Lists
const filteredRootNotes = computed(() => {
  const all = labelsStore.rootNotes
  if (!libraryRootSearchQuery.value) return all
  const q = libraryRootSearchQuery.value.toLowerCase()
  return all.filter(n => n.title.toLowerCase().includes(q))
})

const filteredRootFeeds = computed(() => {
  const all = labelsStore.rootFeeds
  if (!libraryRootSearchQuery.value) return all
  const q = libraryRootSearchQuery.value.toLowerCase()
  return all.filter(f => f.id.split(':')[1].toLowerCase().includes(q))
})

const filteredFocusedTree = computed(() => {
  const tree = labelsStore.selectedFeedTree
  if (!focusedSearchQuery.value) return tree
  const q = focusedSearchQuery.value.toLowerCase()
  const getDisplayName = (id) => {
    if (id.includes(':')) {
       if (id.startsWith('note:')) {
          const note = notesStore.noteById(id.replace('note:', ''))
          return note ? note.title : id.split(':')[1]
       }
       return id.split(':')[1]
    }
    return id
  }
  
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

const fuzzyFilteredFeeds = computed(() => {
  const feeds = labelsStore.rootFeeds.filter(feed => feed.id !== labelsStore.activeFeedId)
  const query = moveFeedQuery.value.trim().toLowerCase()
  if (!query) return feeds

  return feeds
    .map(feed => ({
      feed,
      score: fuzzyScore(feed.id.split(':')[1].toLowerCase(), query),
    }))
    .filter(entry => entry.score > Number.NEGATIVE_INFINITY)
    .sort((a, b) => b.score - a.score || a.feed.id.localeCompare(b.feed.id))
    .map(entry => entry.feed)
})

const movePlacementTree = computed(() => {
  if (!movePlacementFeedId.value) return []
  const tree = resolveTreeForFeed(movePlacementFeedId.value)
  const query = moveFeedQuery.value.trim().toLowerCase()
  if (!query) return tree

  const getDisplayName = (id) => {
    if (id.startsWith('note:')) {
      const note = notesStore.noteById(id.replace('note:', ''))
      return note ? note.title : id.split(':')[1]
    }
    return id.split(':')[1]
  }

  function filterNodes(nodes) {
    return nodes
      .map(node => {
        const filteredChildren = filterNodes(node.resolvedChildren || [])
        if (getDisplayName(node.id).toLowerCase().includes(query) || filteredChildren.length > 0) {
          return { ...node, resolvedChildren: filteredChildren }
        }
        return null
      })
      .filter(Boolean)
  }

  return filterNodes(tree)
})

function resolveTreeForFeed(rootId) {
  const nodes = {}

  labelsStore.hierarchy.forEach(h => {
    nodes[h.id] = { ...h, resolvedChildren: [] }
  })

  labelsStore.hierarchy.forEach(h => {
    h.children.forEach(cid => {
      if (!nodes[cid]) {
        nodes[cid] = { id: cid, children: [], resolvedChildren: [] }
      }
    })
  })

  const resolve = (node, path = new Set()) => {
    if (path.has(node.id)) return
    const nextPath = new Set(path)
    nextPath.add(node.id)

    node.children.forEach(cid => {
      if (!nodes[cid]) return
      const childNode = { ...nodes[cid], resolvedChildren: [] }
      node.resolvedChildren.push(childNode)
      resolve(childNode, nextPath)
    })
  }

  const root = nodes[rootId]
  if (!root) return []
  const focusedNode = { ...root, resolvedChildren: [] }
  resolve(focusedNode)
  return focusedNode.resolvedChildren
}

const vClickOutside = {
  mounted(el, binding) {
    el.clickOutsideEvent = (event) => {
      if (!(el === event.target || el.contains(event.target))) binding.value()
    }
    document.addEventListener('click', el.clickOutsideEvent)
  },
  unmounted(el) {
    document.removeEventListener('click', el.clickOutsideEvent)
  }
}

// Handlers
function handleNewNoteAction() {
  creationType.value = 'note'
  creationPlan.value = null
  showNewNoteModal.value = true
}

function handleNewDrawingAction() {
  creationType.value = 'drawing'
  showNewNoteModal.value = true
}

function handleNewLorienAction() {
  creationType.value = 'lorien'
  showNewNoteModal.value = true
}

function handleNewXjournalAction() {
  creationType.value = 'xopp'
  showNewNoteModal.value = true
}

function handleNewFeedRootAction() {
  creationType.value = 'feed'
  creationPlan.value = null
  showNewLabelModal.value = true
}

function handleNewLabelAction() {
  creationType.value = 'label'
  creationPlan.value = null
  showNewLabelModal.value = true
}

function handleToggleGraph() {
  graphStore.fetchGraph()
  emit('toggle-graph')
}

async function createNote() {
  if (!newNoteTitle.value.trim()) return
  let labels = []
  const targetId = creationPlan.value?.targetParentId || labelsStore.activeLabel || labelsStore.activeFeedId
  if (targetId) labels = [targetId]

  let type = 'markdown'
  if (creationType.value === 'drawing') type = 'excalidraw'
  if (creationType.value === 'lorien') type = 'lorien'
  if (creationType.value === 'xopp') type = 'xopp'
  
  const content = (type === 'markdown') ? '' : '{}'

  // The backend NoteService will now handle the type correctly.
  // We just need to make sure we're sending the right type.
  const setActive = type !== 'xopp'
  const note = await notesStore.createNote(newNoteTitle.value.trim(), content, labels, type, setActive)
  if (note) {
    await finalizeCreatedNode(`note:${note.id}`)
    showNewNoteModal.value = false
    emit('select-note', note.id)
    emit('new-note')
    await labelsStore.fetchLabels()
    creationPlan.value = null
  } else {
    alert(notesStore.error || 'Failed to create file. A file with this name might already exist.')
  }
}

async function createGenericLabel() {
  if (!newLabelName.value.trim()) return
  const name = newLabelName.value.trim()
  const targetParent = creationPlan.value?.targetParentId || labelsStore.activeLabel || labelsStore.activeFeedId
  
  if (creationType.value === 'feed') {
    await labelsStore.createLabel(`feed:${name}`)
  } else {
    const result = await labelsStore.createLabel(`label:${name}`, targetParent)
    if (result) {
      await finalizeCreatedNode(result.id)
    }
  }
  
  showNewLabelModal.value = false
  newLabelName.value = ''
  creationPlan.value = null
}

async function finalizeCreatedNode(createdNodeId) {
  if (!creationPlan.value) return

  if (creationPlan.value.reorderParentId !== undefined && creationPlan.value.reorderIndex !== null) {
    await labelsStore.reorderNode(createdNodeId, creationPlan.value.reorderParentId, creationPlan.value.reorderIndex)
  }

  if (creationPlan.value.wrapCurrentNodeId) {
    await labelsStore.moveLabel(creationPlan.value.wrapCurrentNodeId, createdNodeId)
  }
}

function handleHierarchyCreate(request) {
  if (!labelsStore.activeFeedId) return

  if (request.kind === 'note') {
    creationType.value = 'note'
    showNewNoteModal.value = true
  } else {
    creationType.value = 'label'
    showNewLabelModal.value = true
  }

  if (request.mode === 'child') {
    creationPlan.value = {
      targetParentId: request.nodeId,
      reorderParentId: null,
      reorderIndex: null,
      wrapCurrentNodeId: null,
    }
    return
  }

  if (request.mode === 'sibling') {
    creationPlan.value = {
      targetParentId: request.parentId,
      reorderParentId: request.parentId,
      reorderIndex: request.insertIndex,
      wrapCurrentNodeId: null,
    }
    return
  }

  if (request.mode === 'wrap') {
    creationPlan.value = {
      targetParentId: request.parentId,
      reorderParentId: request.parentId,
      reorderIndex: request.insertIndex,
      wrapCurrentNodeId: request.nodeId,
    }
  }
}

async function moveNodeToFeedRoot(nodeId) {
  if (!labelsStore.activeFeedId) return
  await labelsStore.moveLabel(nodeId, labelsStore.activeFeedId)
}

async function moveNodeToLibraryRoot(nodeId) {
  await labelsStore.moveLabel(nodeId, null)
}

function openMoveFeedModal(nodeId) {
  moveFeedNodeId.value = nodeId
  moveFeedQuery.value = ''
  selectedMoveFeedTarget.value = ''
  moveFeedStep.value = 'feeds'
  movePlacementFeedId.value = null
  showMoveFeedModal.value = true
  nextTick(() => moveFeedInput.value?.focus())
}

function closeMoveFeedModal() {
  showMoveFeedModal.value = false
  moveFeedNodeId.value = null
  moveFeedQuery.value = ''
  selectedMoveFeedTarget.value = ''
  moveFeedStep.value = 'feeds'
  movePlacementFeedId.value = null
}

async function confirmMoveToFeed() {
  if (!moveFeedNodeId.value || !selectedMoveFeedTarget.value) return
  const target = selectedMoveFeedTarget.value === '__root__' ? null : selectedMoveFeedTarget.value
  await labelsStore.moveLabel(moveFeedNodeId.value, target)
  closeMoveFeedModal()
}

async function moveNodeDirectlyToTarget(targetId) {
  if (!moveFeedNodeId.value) return
  const target = targetId === '__root__' ? null : targetId
  await labelsStore.moveLabel(moveFeedNodeId.value, target)
  closeMoveFeedModal()
}

function openPlacementStep(feedId) {
  movePlacementFeedId.value = feedId
  moveFeedStep.value = 'placement'
  moveFeedQuery.value = ''
  selectedMoveFeedTarget.value = feedId
  nextTick(() => moveFeedInput.value?.focus())
}

async function moveNodeToFeedRootOf(feedId) {
  if (!moveFeedNodeId.value || !feedId) return
  await labelsStore.moveLabel(moveFeedNodeId.value, feedId)
  closeMoveFeedModal()
}

async function placeMovedNodeInside(targetId) {
  if (!moveFeedNodeId.value) return
  await labelsStore.moveLabel(moveFeedNodeId.value, targetId)
  closeMoveFeedModal()
}

async function placeMovedNodeAsSibling({ parentId, index }) {
  if (!moveFeedNodeId.value) return
  await labelsStore.moveLabel(moveFeedNodeId.value, parentId)
  await labelsStore.reorderNode(moveFeedNodeId.value, parentId, index)
  closeMoveFeedModal()
}

async function placeMovedNodeAsParent({ targetId, parentId, index }) {
  if (!moveFeedNodeId.value || !targetId) return
  await labelsStore.moveLabel(moveFeedNodeId.value, parentId)
  await labelsStore.reorderNode(moveFeedNodeId.value, parentId, index)
  await labelsStore.moveLabel(targetId, moveFeedNodeId.value)
  closeMoveFeedModal()
}

function fuzzyScore(text, query) {
  if (!query) return 0
  if (text.includes(query)) return 1000 - (text.length - query.length)

  let score = 0
  let qIndex = 0
  let streak = 0

  for (let i = 0; i < text.length && qIndex < query.length; i += 1) {
    if (text[i] === query[qIndex]) {
      score += 10 + streak * 4
      streak += 1
      qIndex += 1
    } else {
      streak = 0
    }
  }

  if (qIndex !== query.length) return Number.NEGATIVE_INFINITY
  return score - (text.length - query.length)
}

function onDragStartLibraryNote(event, noteId) {
  event.dataTransfer.setData('nodeId', `note:${noteId}`)
  event.dataTransfer.effectAllowed = 'move'
}

async function onDropOnFeed(event, feedId) {
  dragOverTarget.value = null
  if (feedHoverTimer) clearTimeout(feedHoverTimer)
  
  const nodeId = event.dataTransfer.getData('nodeId')
  if (nodeId) {
    await labelsStore.moveLabel(nodeId, feedId)
  }
}

async function onDropOnRoot(event) {
  dragOverTarget.value = null
  if (backHoverTimer) clearTimeout(backHoverTimer)
  if (feedHoverTimer) clearTimeout(feedHoverTimer)
  
  const nodeId = event.dataTransfer.getData('nodeId')
  if (nodeId) {
    await labelsStore.moveLabel(nodeId, null)
    labelsStore.setFeed(null)
  }
}

function handleFeedDragOver(event, feedId) {
  dragOverTarget.value = feedId
  if (!feedHoverTimer) {
    feedHoverTimer = setTimeout(() => {
      labelsStore.setFeed(feedId)
      dragOverTarget.value = null
      feedHoverTimer = null
    }, 600)
  }
}

function handleFeedDragLeave() {
  dragOverTarget.value = null
  if (feedHoverTimer) {
    clearTimeout(feedHoverTimer)
    feedHoverTimer = null
  }
}

function handleBackDragOver(event) {
  dragOverTarget.value = 'back'
  if (!backHoverTimer) {
    backHoverTimer = setTimeout(() => {
      labelsStore.setFeed(null)
      dragOverTarget.value = 'root'
      backHoverTimer = null
    }, 600)
  }
}

function handleBackDragLeave() {
  dragOverTarget.value = null
  if (backHoverTimer) {
    clearTimeout(backHoverTimer)
    backHoverTimer = null
  }
}

watch(showNewNoteModal, (val) => {
  if (val) {
    newNoteTitle.value = ''
    nextTick(() => newNoteTitleInput.value?.focus())
  } else {
    newNoteTitle.value = ''
  }
})

watch(showNewLabelModal, (val) => {
  if (!val) {
    newLabelName.value = ''
  }
})

defineExpose({
  showNewNoteModal
})
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width); height: 100vh; display: flex; flex-direction: column;
  background: var(--bg-primary); border-right: 1px solid var(--border-subtle); overflow: hidden;
}

.sidebar-brand { display: flex; align-items: center; gap: var(--space-md); padding: var(--space-lg) var(--space-lg) var(--space-sm); }
.brand-icon { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; background: var(--accent-glow); border-radius: var(--radius-md); }
.brand-text { font-size: 1.125rem; font-weight: 700; background: linear-gradient(135deg, var(--accent-secondary), var(--accent-primary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; flex: 1; }

.sidebar-top-actions { padding: 0 var(--space-lg) var(--space-md); }
.switch-vault-btn { width: 100%; justify-content: flex-start; font-size: 0.75rem; color: var(--text-tertiary); gap: var(--space-sm); padding: 8px var(--space-md); }

.sidebar-actions-container { display: flex; flex-direction: column; }
.contextual-header { display: flex; flex-direction: column; }

.sidebar-header-bar { padding: var(--space-md) var(--space-lg); display: flex; align-items: center; justify-content: space-between; transition: all var(--transition-fast); }
.sidebar-header-bar.library-header { border-bottom: 1px solid var(--border-subtle); margin-bottom: var(--space-xs); }
.sidebar-header-bar.drag-over { background: var(--accent-glow); outline: 2px solid var(--accent-primary); }

.header-pill-group { 
  display: flex; 
  align-items: center; 
  background: var(--bg-tertiary); 
  padding: 2px; 
  border-radius: var(--radius-md); 
  gap: 2px;
}
.header-pill-group button { 
  padding: 3px 12px; border: none; background: none; color: var(--text-tertiary); 
  font-size: 0.625rem; font-weight: 700; cursor: pointer; border-radius: var(--radius-sm); transition: all var(--transition-fast); 
}
.header-pill-group button.active { background: var(--bg-primary); color: var(--accent-primary); box-shadow: var(--shadow-sm); }

.sidebar-header { padding: var(--space-md) var(--space-lg); display: flex; align-items: center; justify-content: space-between; }
.sidebar-title { font-size: 0.875rem; font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em; white-space: nowrap; }

.sidebar-actions { padding: 0 var(--space-lg) var(--space-sm); display: flex; gap: var(--space-xs); flex-wrap: wrap; }
.sidebar-actions.grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; }
.action-btn-sm { padding: 6px 4px; font-size: 0.65rem; border-radius: var(--radius-md); gap: 4px; display: flex; align-items: center; justify-content: center; }

.sidebar-search { padding: var(--space-sm) var(--space-lg) var(--space-md); }
.search-input-wrapper { position: relative; }
.search-icon { position: absolute; left: var(--space-md); top: 50%; transform: translateY(-50%); color: var(--text-tertiary); pointer-events: none; }
.search-input { width: 100%; padding: var(--space-sm) var(--space-md) var(--space-sm) 36px; background: var(--bg-secondary); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); color: var(--text-primary); font-size: 0.8125rem; outline: none; }
.search-input:focus { border-color: var(--accent-primary); box-shadow: 0 0 0 3px var(--accent-glow); }

.tree-section { flex: 1; overflow-y: auto; display: flex; flex-direction: column; }
.feed-root-view { display: flex; flex-direction: column; height: 100%; }
.nav-list, .hierarchy-list { display: flex; flex-direction: column; gap: 1px; }

.sidebar-divider { border: none; border-top: 1px solid var(--border-subtle); margin: var(--space-sm) var(--space-lg); opacity: 0.5; }

.nav-card { display: flex; align-items: center; gap: var(--space-md); padding: 10px var(--space-lg); background: none; border: none; color: var(--text-secondary); font-size: 0.875rem; cursor: pointer; transition: all var(--transition-fast); text-align: left; border-radius: var(--radius-md); margin: 0 8px; border: 2px solid transparent; }
.nav-card:hover { background: var(--bg-secondary); color: var(--text-primary); transform: translateX(4px); }
.nav-card.drag-over { background: var(--accent-glow); border-color: var(--accent-primary); color: var(--text-primary); }
.nav-card svg { color: var(--accent-secondary); }
.move-btn { width: 18px; height: 18px; border: none; border-radius: var(--radius-sm); background: var(--bg-secondary); color: var(--text-tertiary); display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all var(--transition-fast); }
.move-btn:hover:not(:disabled) { color: var(--text-primary); background: var(--bg-primary); }
.move-btn:disabled { opacity: 0.35; cursor: default; }
.nav-card .arrow { margin-left: auto; opacity: 0; transition: opacity var(--transition-fast); }
.nav-card:hover .arrow { opacity: 0.5; }

.focused-view { display: flex; flex-direction: column; height: 100%; }
.active-title { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.nav-header { display: flex; align-items: center; gap: var(--space-sm); padding: 0 var(--space-lg) var(--space-sm); }
.back-btn { width: 24px; height: 24px; border-radius: var(--radius-sm); border: 2px solid transparent; transition: all var(--transition-fast); }
.back-btn.drag-over { background: var(--accent-glow); border-color: var(--accent-primary); color: var(--accent-primary); transform: scale(1.1); }

.note-item { display: flex; align-items: center; gap: var(--space-sm); padding: 6px var(--space-lg); border: none; background: none; color: var(--text-secondary); font-size: 0.8125rem; cursor: pointer; transition: all var(--transition-fast); text-align: left; width: 100%; user-select: none; }
.root-level-note { padding-left: 20px; }
.note-item:hover { background: var(--bg-hover); color: var(--text-primary); }
.note-item.active { background: var(--accent-glow); color: var(--accent-secondary); border-left: 2px solid var(--accent-primary); }
.note-title { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.empty-state { padding: var(--space-xl); text-align: center; color: var(--text-tertiary); font-size: 0.75rem; font-style: italic; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { width: 400px; max-width: 90vw; background: var(--bg-secondary); border: 1px solid var(--border-default); border-radius: var(--radius-lg); padding: var(--space-xl); box-shadow: var(--shadow-lg); }
.modal-title { font-size: 1rem; font-weight: 600; margin-bottom: var(--space-lg); }
.modal-actions { display: flex; justify-content: flex-end; gap: var(--space-sm); margin-top: var(--space-lg); }
.move-feed-modal { width: 520px; max-width: 92vw; }
.move-feed-header { display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-md); }
.move-feed-back { flex-shrink: 0; }
.move-feed-list { max-height: min(42vh, 360px); overflow-y: auto; display: flex; flex-direction: column; gap: 6px; margin-top: var(--space-md); padding-right: 4px; }
.move-feed-item { display: flex; align-items: center; justify-content: space-between; gap: var(--space-md); width: 100%; padding: 10px 12px; border: 1px solid var(--border-subtle); border-radius: var(--radius-md); background: var(--bg-secondary); color: var(--text-primary); cursor: pointer; text-align: left; transition: all var(--transition-fast); }
.move-feed-item:hover { background: var(--bg-hover); }
.move-feed-item.active { border-color: var(--accent-primary); background: var(--accent-glow); }
.move-feed-main { display: flex; flex-direction: column; min-width: 0; }
.move-feed-name { font-weight: 600; }
.move-feed-path { font-size: 0.75rem; color: var(--text-tertiary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.move-feed-icon { width: 24px; height: 24px; border-radius: 999px; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }
.move-feed-icon.plus { background: var(--accent-glow); color: var(--accent-primary); }
.move-feed-icon.minus { background: rgba(239, 68, 68, 0.12); color: #ef4444; }
.icon-action-btn { border: none; cursor: pointer; transition: transform var(--transition-fast), background var(--transition-fast), color var(--transition-fast); }
.icon-action-btn:hover { transform: scale(1.05); }
.move-feed-empty { padding: 18px 8px; text-align: center; color: var(--text-tertiary); font-size: 0.8125rem; }
</style>
