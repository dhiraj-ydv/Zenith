<template>
  <div class="placement-node">
    <div class="placement-row" :style="{ paddingLeft: depth * 14 + 'px' }">
      <div class="placement-title">
        <svg v-if="isLabel" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M20.59 13.41L13.42 20.58C13.04 20.96 12.53 21.17 12 21.17C11.47 21.17 10.96 20.96 10.59 20.58L2 12V2H12L20.59 10.59C21.37 11.37 21.37 12.63 20.59 13.41Z"/>
          <line x1="7" y1="7" x2="7.01" y2="7"/>
        </svg>
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M14 2H6C4.89 2 4 2.9 4 4V20C4 21.1 4.89 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z"/><path d="M14 2V8H20"/>
        </svg>
        <span>{{ displayName }}</span>
      </div>
      <div class="placement-actions">
        <button class="placement-btn" @click="$emit('place-child', node.id)">Inside</button>
        <button class="placement-btn" @click="$emit('place-parent', { targetId: node.id, parentId: parentId, index: siblingIndex })">Parent</button>
        <button class="placement-btn" @click="$emit('place-sibling', { parentId: parentId, index: siblingIndex })">Above</button>
        <button class="placement-btn" @click="$emit('place-sibling', { parentId: parentId, index: siblingIndex + 1 })">Below</button>
      </div>
    </div>

    <div v-if="node.resolvedChildren?.length" class="placement-children">
      <MovePlacementItem
        v-for="(child, childIndex) in node.resolvedChildren"
        :key="child.id"
        :node="child"
        :depth="depth + 1"
        :parent-id="node.id"
        :sibling-index="childIndex"
        @place-child="(targetId) => $emit('place-child', targetId)"
        @place-parent="(payload) => $emit('place-parent', payload)"
        @place-sibling="(payload) => $emit('place-sibling', payload)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useNotesStore } from '../stores/notes'

const props = defineProps({
  node: Object,
  depth: {
    type: Number,
    default: 0,
  },
  parentId: {
    type: String,
    default: null,
  },
  siblingIndex: {
    type: Number,
    default: 0,
  },
})

defineEmits(['place-child', 'place-parent', 'place-sibling'])

const notesStore = useNotesStore()

const isLabel = computed(() => props.node.id.startsWith('label:') || props.node.id.startsWith('feed:'))

const displayName = computed(() => {
  if (isLabel.value) return props.node.id.split(':')[1]
  const noteId = props.node.id.replace('note:', '')
  const note = notesStore.noteById(noteId)
  return note ? note.title : noteId
})
</script>

<style scoped>
.placement-node {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.placement-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 10px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
}

.placement-title {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  color: var(--text-primary);
  font-size: 0.8125rem;
}

.placement-title span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.placement-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.placement-btn {
  border: none;
  border-radius: var(--radius-sm);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  padding: 5px 8px;
  font-size: 0.72rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.placement-btn:hover {
  background: var(--accent-glow);
  color: var(--accent-primary);
}

.placement-children {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
</style>
