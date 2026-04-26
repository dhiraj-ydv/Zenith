import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { vaultsApi } from '../api/client'

export const useVaultStore = defineStore('vaults', () => {
  const vaults = ref([])
  const activeVault = ref(null)
  const isInitializing = ref(true)

  async function init() {
    try {
      await fetchVaults()
      isInitializing.value = false
    } catch (e) {
      console.error('Failed to initialize vaults', e)
      isInitializing.value = false
    }
  }

  async function fetchVaults() {
    try {
      const res = await vaultsApi.list()
      vaults.value = res.data
      activeVault.value = res.data.find(v => v.is_active) || null
    } catch (e) {
      console.error('Failed to fetch vaults:', e)
    }
  }

  async function createOrOpenVault(path) {
    try {
      const res = await vaultsApi.create(path)
      activeVault.value = res.data
      await fetchVaults()
      return true
    } catch (e) {
      console.error('Failed to open vault:', e)
      return false
    }
  }

  return { vaults, activeVault, isInitializing, init, fetchVaults, createOrOpenVault }
})
