<template>
  <div class="vault-switcher-overlay">
    <div class="vault-switcher-card">
      <div class="vault-header">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
          <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="var(--accent-primary)"/>
          <path d="M2 17L12 22L22 17" stroke="var(--accent-primary)" stroke-width="2" stroke-linecap="round"/>
          <path d="M2 12L12 17L22 12" stroke="var(--accent-primary)" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <h2>Welcome to Zenith</h2>
        <p>Open an existing vault or create a new one.</p>
      </div>

      <div class="vault-list" v-if="vaultStore.vaults.length > 0">
        <h3>Recent Vaults</h3>
        <button 
          v-for="vault in vaultStore.vaults" 
          :key="vault.path"
          class="vault-item"
          :class="{ active: vault.is_active }"
          @click="openVault(vault.path)"
        >
          <div class="vault-info">
            <span class="vault-name">{{ vault.name }}</span>
            <span class="vault-path">{{ vault.path }}</span>
          </div>
          <svg v-if="vault.is_active" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 6L9 17L4 12"/>
          </svg>
        </button>
      </div>

      <div class="vault-create">
        <h3>Open or Create Vault</h3>
        <form @submit.prevent="createNewVault">
          <div class="input-group">
            <input 
              v-model="newVaultPath" 
              type="text" 
              placeholder="Enter full path (e.g., C:\Users\Documents\MyVault)"
              required
            />
            <button type="submit" class="btn btn-primary" :disabled="!newVaultPath.trim()">Open</button>
          </div>
        </form>
      </div>

      <button v-if="vaultStore.activeVault" class="btn btn-ghost close-btn" @click="$emit('close')">Cancel</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useVaultStore } from '../stores/vaults'

const emit = defineEmits(['close'])
const vaultStore = useVaultStore()
const newVaultPath = ref('')

async function openVault(path) {
  const success = await vaultStore.createOrOpenVault(path)
  if (success) {
    emit('close')
    // Reload the app completely to reset state for the new vault
    window.location.reload()
  }
}

async function createNewVault() {
  if (newVaultPath.value.trim()) {
    await openVault(newVaultPath.value.trim())
  }
}
</script>

<style scoped>
.vault-switcher-overlay {
  position: fixed;
  inset: 0;
  background: rgba(10, 10, 15, 0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.vault-switcher-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-2xl);
  width: 100%;
  max-width: 500px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
}

.vault-header {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
}
.vault-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
}
.vault-header p {
  color: var(--text-tertiary);
  font-size: 0.9rem;
}

.vault-list h3, .vault-create h3 {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-tertiary);
  margin-bottom: var(--space-md);
}

.vault-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.vault-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  background: var(--bg-tertiary);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}
.vault-item:hover {
  background: var(--bg-hover);
}
.vault-item.active {
  background: rgba(99, 102, 241, 0.1);
  border-color: var(--accent-primary);
}

.vault-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.vault-name {
  font-weight: 500;
}
.vault-path {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  font-family: var(--font-mono);
}

.input-group {
  display: flex;
  gap: var(--space-sm);
}
.input-group input {
  flex: 1;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-tertiary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 0.9rem;
}
.input-group input:focus {
  outline: none;
  border-color: var(--accent-primary);
}

.close-btn {
  align-self: center;
}
</style>
