<template>
  <div class="app-shell" :class="{ 'graph-open': showGraph }">
    <!-- Vault Switcher Overlay -->
    <VaultSwitcher 
      v-if="!vaultStore.isInitializing && (!vaultStore.activeVault || showVaultSwitcher)"
      @close="showVaultSwitcher = false"
    />

    <!-- Sidebar -->
    <Sidebar
      ref="sidebarRef"
      v-if="vaultStore.activeVault"
      @select-note="handleSelectNote"
      @new-note="handleNewNote"
      @toggle-graph="showGraph = !showGraph"
      @switch-vault="showVaultSwitcher = true"
      :show-graph="showGraph"
    />

    <!-- Main Content -->
    <main class="main-content" v-if="vaultStore.activeVault">
      <Editor
        v-if="notesStore.activeNote && !showGraph"
        :key="notesStore.activeNote.id"
      />
      <GraphView
        v-else-if="showGraph"
        @select-node="handleGraphNodeSelect"
      />
      <EmptyState v-else @new-note="handleNewNote" />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useNotesStore } from './stores/notes'
import { useLabelsStore } from './stores/labels'
import { useVaultStore } from './stores/vaults'
import Sidebar from './components/Sidebar.vue'
import Editor from './components/Editor.vue'
import GraphView from './components/GraphView.vue'
import EmptyState from './components/EmptyState.vue'
import VaultSwitcher from './components/VaultSwitcher.vue'

const notesStore = useNotesStore()
const labelsStore = useLabelsStore()
const vaultStore = useVaultStore()

const showGraph = ref(false)
const showVaultSwitcher = ref(false)
const sidebarRef = ref(null)

onMounted(async () => {
  await vaultStore.init()
  if (vaultStore.activeVault) {
    await loadVaultData()
  }
})

async function loadVaultData() {
  await labelsStore.fetchLabels()
  await notesStore.fetchNotes()
}

function handleSelectNote(id) {
  showGraph.value = false
  notesStore.fetchNote(id)
}

function handleNewNote() {
  showGraph.value = false
  if (sidebarRef.value) {
    sidebarRef.value.showNewNoteModal = true
  }
}

function handleGraphNodeSelect(id) {
  showGraph.value = false
  notesStore.fetchNote(id)
}
</script>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--bg-root);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}
</style>
