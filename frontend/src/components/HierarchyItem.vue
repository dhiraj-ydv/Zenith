<template>
  <div class="hierarchy-node">
    <div 
      class="hierarchy-item" 
      :class="{ 
        active: isActive,
        'drag-over': isDragOver,
        'is-label': isLabel,
        'is-note': isNote
      }"
      :style="{ paddingLeft: depth * 12 + 16 + 'px' }"
      @click="handleClick"
      draggable="true"
      @dragstart="onDragStart($event)"
      @dragover.prevent="onDragOver"
      @dragleave="onDragLeave"
      @drop.stop="onDrop"
    >
      <button 
        v-if="node.resolvedChildren.length > 0" 
        class="collapse-btn" 
        @click.stop="collapsed = !collapsed"
        :class="{ collapsed }"
      >
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
      <div v-else class="collapse-spacer"></div>

      <!-- Icon -->
      <svg v-if="isLabel" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M20.59 13.41L13.42 20.58C13.04 20.96 12.53 21.17 12 21.17C11.47 21.17 10.96 20.96 10.59 20.58L2 12V2H12L20.59 10.59C21.37 11.37 21.37 12.63 20.59 13.41Z"/>
        <line x1="7" y1="7" x2="7.01" y2="7"/>
      </svg>
      <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M14 2H6C4.89 2 4 2.9 4 4V20C4 21.1 4.89 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z"/><path d="M14 2V8H20"/>
      </svg>

      <span class="node-title">{{ displayName }}</span>
      <div class="row-actions" @click.stop>
        <div class="action-menu-wrap">
          <button class="plus-btn" title="Add around this item" @click.stop="toggleMenu">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
              <path d="M12 5v14M5 12h14" />
            </svg>
          </button>
          <div v-if="showMenu" ref="menuRef" class="action-menu">
            <button class="action-menu-item" @click.stop="requestCreate('note', 'sibling', siblingIndex)">New note above</button>
            <button class="action-menu-item" @click.stop="requestCreate('note', 'sibling', siblingIndex + 1)">New note below</button>
            <button class="action-menu-item" @click.stop="requestCreate('label', 'sibling', siblingIndex)">New label above</button>
            <button class="action-menu-item" @click.stop="requestCreate('label', 'sibling', siblingIndex + 1)">New label below</button>
            <button class="action-menu-item" @click.stop="requestCreate('note', 'wrap', siblingIndex)">Parent note</button>
            <button class="action-menu-item" @click.stop="requestCreate('label', 'wrap', siblingIndex)">Parent label</button>
            <button class="action-menu-item" @click.stop="requestCreate('note', 'child')">Child note</button>
            <button class="action-menu-item" @click.stop="requestCreate('label', 'child')">Child label</button>
            <button class="action-menu-item" @click.stop="moveToOtherFeed">Move to other feed</button>
            <button class="action-menu-item" :disabled="!canMoveToFeedRoot" @click.stop="moveToFeedRoot">Move to root of feed</button>
            <button v-if="isNote" class="action-menu-item" @click.stop="moveToLibraryRoot">Move to library root</button>
          </div>
        </div>
        <button class="move-btn" title="Move up" :disabled="siblingIndex <= 0" @click.stop="moveBy(-1)">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
            <path d="M18 15l-6-6-6 6" />
          </svg>
        </button>
        <button class="move-btn" title="Move down" :disabled="siblingIndex >= siblingCount - 1" @click.stop="moveBy(1)">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
            <path d="M6 9l6 6 6-6" />
          </svg>
        </button>
      </div>
    </div>

    <div v-if="node.resolvedChildren.length > 0 && !collapsed" class="hierarchy-children">
      <HierarchyItem 
        v-for="(child, childIndex) in node.resolvedChildren" 
        :key="child.id" 
        :node="child" 
        :depth="depth + 1"
        :parent-id="node.id"
        :sibling-index="childIndex"
        :sibling-count="node.resolvedChildren.length"
        @select-note="(id) => $emit('select-note', id)"
        @request-create="(payload) => $emit('request-create', payload)"
        @request-move-root="(nodeId) => $emit('request-move-root', nodeId)"
        @request-move-library-root="(nodeId) => $emit('request-move-library-root', nodeId)"
        @request-move-other-feed="(nodeId) => $emit('request-move-other-feed', nodeId)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useLabelsStore } from '../stores/labels'
import { useNotesStore } from '../stores/notes'

const props = defineProps({
  node: Object,
  depth: {
    type: Number,
    default: 0
  },
  parentId: {
    type: String,
    default: null
  },
  siblingIndex: {
    type: Number,
    default: 0
  },
  siblingCount: {
    type: Number,
    default: 1
  }
})

const emit = defineEmits(['select-note', 'request-create', 'request-move-root', 'request-move-library-root', 'request-move-other-feed'])

const labelsStore = useLabelsStore()
const notesStore = useNotesStore()
const collapsed = ref(false)
const isDragOver = ref(false)
const showMenu = ref(false)
const menuRef = ref(null)

const isLabel = computed(() => props.node.id.startsWith('label:') || props.node.id.startsWith('feed:'))
const isNote = computed(() => props.node.id.startsWith('note:'))

const displayName = computed(() => {
  if (isLabel.value) return props.node.id.split(':')[1]
  const noteId = props.node.id.replace('note:', '', 1)
  const note = notesStore.noteById(noteId)
  return note ? note.title : noteId
})

const isActive = computed(() => {
  if (isLabel.value) return labelsStore.activeLabel === props.node.id
  const noteId = props.node.id.replace('note:', '', 1)
  return notesStore.activeNote?.id === noteId
})

const canMoveToFeedRoot = computed(() => {
  return !!labelsStore.activeFeedId && props.parentId && props.parentId !== labelsStore.activeFeedId
})

function handleClick() {
  if (isLabel.value) {
    labelsStore.setActiveLabel(props.node.id)
  } else {
    const noteId = props.node.id.replace('note:', '', 1)
    emit('select-note', noteId)
  }
}

// Drag & Drop
function onDragStart(event) {
  event.dataTransfer.setData('nodeId', props.node.id)
  event.dataTransfer.effectAllowed = 'move'
}

function onDragOver(event) {
  isDragOver.value = true
  event.dataTransfer.dropEffect = 'move'
}

function onDragLeave() {
  isDragOver.value = false
}

async function onDrop(event) {
  isDragOver.value = false
  const draggedNodeId = event.dataTransfer.getData('nodeId')
  const targetNodeId = props.node.id
  
  if (draggedNodeId === targetNodeId) return
  await labelsStore.moveLabel(draggedNodeId, targetNodeId)
}

async function moveBy(delta) {
  const nextIndex = props.siblingIndex + delta
  if (nextIndex < 0 || nextIndex >= props.siblingCount) return
  await labelsStore.reorderNode(props.node.id, props.parentId, nextIndex)
}

function toggleMenu() {
  showMenu.value = !showMenu.value
}

function requestCreate(kind, mode, insertIndex = null) {
  showMenu.value = false
  emit('request-create', {
    kind,
    mode,
    nodeId: props.node.id,
    parentId: props.parentId,
    insertIndex,
  })
}

function moveToFeedRoot() {
  if (!canMoveToFeedRoot.value) return
  showMenu.value = false
  emit('request-move-root', props.node.id)
}

function moveToLibraryRoot() {
  showMenu.value = false
  emit('request-move-library-root', props.node.id)
}

function moveToOtherFeed() {
  showMenu.value = false
  emit('request-move-other-feed', props.node.id)
}

function handleDocumentClick(event) {
  if (!showMenu.value) return
  if (menuRef.value?.contains(event.target)) return
  showMenu.value = false
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleDocumentClick)
})
</script>

<style scoped>
.hierarchy-node {
  display: flex;
  flex-direction: column;
}

.hierarchy-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  border: none;
  background: none;
  color: var(--text-secondary);
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all var(--transition-fast);
  text-align: left;
  width: 100%;
  user-select: none;
  border-top: 2px solid transparent;
  border-bottom: 2px solid transparent;
}

.hierarchy-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.hierarchy-item.active {
  background: var(--accent-glow);
  color: var(--accent-secondary);
}

.hierarchy-item.is-note.active {
  border-left: 2px solid var(--accent-primary);
}

.hierarchy-item.drag-over {
  background: var(--accent-glow);
  border-top-color: var(--accent-primary);
  border-bottom-color: var(--accent-primary);
}

.node-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.row-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.hierarchy-item:hover .row-actions,
.hierarchy-item.active .row-actions {
  opacity: 1;
}

.action-menu-wrap {
  position: relative;
}

.plus-btn,
.move-btn {
  width: 18px;
  height: 18px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.plus-btn:hover,
.move-btn:hover:not(:disabled) {
  color: var(--text-primary);
  background: var(--bg-primary);
}

.action-menu {
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  min-width: 168px;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  z-index: 30;
}

.action-menu-item {
  border: none;
  background: none;
  color: var(--text-secondary);
  text-align: left;
  padding: 7px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.75rem;
  transition: all var(--transition-fast);
}

.action-menu-item:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.action-menu-item:disabled {
  opacity: 0.4;
  cursor: default;
}

.move-btn:disabled {
  opacity: 0.35;
  cursor: default;
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border: none;
  background: none;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 0;
  transition: transform var(--transition-fast);
}

.collapse-btn.collapsed {
  transform: rotate(-90deg);
}

.collapse-spacer {
  width: 16px;
}

.hierarchy-item svg {
  flex-shrink: 0;
}
</style>
