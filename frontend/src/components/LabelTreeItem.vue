<template>
  <div class="label-tree-node">
    <div 
      class="label-item" 
      :class="{ 
        active: labelsStore.activeLabel === node.fullName,
        'drag-over': isDragOver 
      }"
      :style="{ paddingLeft: depth * 12 + 16 + 'px' }"
      @click="handleLabelClick(node.fullName)"
      draggable="true"
      @dragstart="onDragStartLabel($event)"
      @dragover.prevent="onDragOver"
      @dragleave="onDragLeave"
      @drop.stop="onDrop"
    >
      <button 
        v-if="node.children.length > 0" 
        class="collapse-btn" 
        @click.stop="collapsed = !collapsed"
        :class="{ collapsed }"
      >
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
      <div v-else class="collapse-spacer"></div>

      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M20.59 13.41L13.42 20.58C13.04 20.96 12.53 21.17 12 21.17C11.47 21.17 10.96 20.96 10.59 20.58L2 12V2H12L20.59 10.59C21.37 11.37 21.37 12.63 20.59 13.41Z"/>
      </svg>
      <span class="label-name">{{ node.name }}</span>
      <span class="label-count" v-if="node.notes.length > 0">{{ node.notes.length }}</span>
    </div>

    <div v-if="!collapsed" class="label-children">
      <!-- Child Labels -->
      <LabelTreeItem 
        v-for="child in node.children" 
        :key="child.fullName" 
        :node="child" 
        :depth="depth + 1"
        @select-note="(id) => $emit('select-note', id)"
      />
      <!-- Notes -->
      <div 
        v-for="note in resolvedNotes" 
        :key="note.id"
        class="tree-note-item"
        :class="{ active: notesStore.activeNote?.id === note.id }"
        :style="{ paddingLeft: (depth + 1) * 12 + 28 + 'px' }"
        @click="$emit('select-note', note.id)"
        draggable="true"
        @dragstart="onDragStartNote($event, note.id)"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M14 2H6C4.89 2 4 2.9 4 4V20C4 21.1 4.89 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z"/><path d="M14 2V8H20"/>
        </svg>
        <span class="note-title">{{ note.title }}</span>
      </div>
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

const resolvedNotes = computed(() => {
  return props.node.notes.map(id => notesStore.noteById(id)).filter(Boolean)
})

async function handleLabelClick(fullName) {
  labelsStore.setActiveLabel(fullName)
  await notesStore.fetchNotes(labelsStore.activeLabel)
}

// Drag & Drop
function onDragStartLabel(event) {
  event.dataTransfer.setData('type', 'label')
  event.dataTransfer.setData('name', props.node.fullName)
  event.dataTransfer.effectAllowed = 'move'
}

function onDragStartNote(event, noteId) {
  event.dataTransfer.setData('type', 'note')
  event.dataTransfer.setData('id', noteId)
  event.dataTransfer.setData('oldLabel', props.node.fullName)
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
  const type = event.dataTransfer.getData('type')
  
  if (type === 'note') {
    const noteId = event.dataTransfer.getData('id')
    const oldLabel = event.dataTransfer.getData('oldLabel')
    const newLabel = props.node.fullName
    
    if (oldLabel === newLabel) return

    // Replace old label with new label in note's labels list
    const note = notesStore.noteById(noteId)
    if (note) {
      let newLabels = note.labels.filter(l => l !== oldLabel)
      if (!newLabels.includes(newLabel)) {
        newLabels.push(newLabel)
      }
      await notesStore.updateNoteLabels(noteId, newLabels)
      await labelsStore.fetchLabels() // Refresh to update counts
    }
  } else if (type === 'label') {
    const labelName = event.dataTransfer.getData('name')
    const newParent = props.node.fullName
    
    if (labelName === newParent) return
    await labelsStore.moveLabel(labelName, newParent)
  }
}
</script>

<style scoped>
.label-tree-node {
  display: flex;
  flex-direction: column;
}

.label-item {
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

.label-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.label-item.active {
  background: var(--accent-glow);
  color: var(--accent-secondary);
}

.label-item.drag-over {
  background: var(--accent-glow);
  border-top-color: var(--accent-primary);
  border-bottom-color: var(--accent-primary);
}

.label-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.label-count {
  font-size: 0.6875rem;
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
  padding: 1px 6px;
  border-radius: var(--radius-full);
}

.tree-note-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 16px;
  color: var(--text-secondary);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all var(--transition-fast);
  border-left: 2px solid transparent;
}

.tree-note-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.tree-note-item.active {
  background: var(--accent-glow);
  color: var(--accent-secondary);
  border-left-color: var(--accent-primary);
}

.note-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
</style>
