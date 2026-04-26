/**
 * Graph Store — Pinia store for graph visualization data.
 */
import { defineStore } from 'pinia'
import { graphApi } from '../api/client'

export const useGraphStore = defineStore('graph', {
  state: () => ({
    nodes: [],
    edges: [],
    loading: false,
    error: null,
  }),

  actions: {
    async fetchGraph() {
      this.loading = true
      try {
        const { data } = await graphApi.data()
        this.nodes = data.nodes
        this.edges = data.edges
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
  },
})
