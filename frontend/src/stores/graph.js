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
    async fetchGraph(id) {
      this.loading = true
      this.error = null
      try {
        const { data } = await graphApi.data(id)
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
