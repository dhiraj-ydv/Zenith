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
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
      </svg>
      <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M14 2H6C4.89 2 4 2.9 4 4V20C4 21.1 4.89 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z"/><path d="M14 2V8H20"/>
      </svg>

      <span class="node-title">{{ displayName }}</span>
    </div>

    <div v-if="node.resolvedChildren.length > 0 && !collapsed" class="hierarchy-children">
      <HierarchyItem 
        v-for="child in node.resolvedChildren" 
        :key="child.id" 
        :node="child" 
        :depth="depth + 1"
        @select-note="(id) => $emit('select-note', id)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useLabelsStore } from '../stores/labels'
import { useNotesStore } from '../stores/notes'

const props = defineProps({
  node: Object,
  depth: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['select-note'])

const labelsStore = useLabelsStore()
const notesStore = useNotesStore()
const collapsed = ref(false)
const isDragOver = ref(false)

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
