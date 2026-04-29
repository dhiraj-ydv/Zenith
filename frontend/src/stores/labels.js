/**
 * Labels Store — Manages hierarchy and multiple feed roots.
 * Supports virtual node resolution for cleaner YAML.
 */
import { defineStore } from 'pinia'
import { labelsApi } from '../api/client'
import { useNotesStore } from './notes'

export const useLabelsStore = defineStore('labels', {
  state: () => ({
    hierarchy: [],
    activeFeedId: null, 
    activeLabel: null, // Sub-label inside a feed root
    loading: false,
    error: null,
  }),

  getters: {
    /**
     * Top-level Feed Roots.
     */
    rootFeeds: (state) => {
      const childIds = new Set()
      state.hierarchy.forEach(h => h.children.forEach(cid => childIds.add(cid)))
      return state.hierarchy
        .filter(h => (h.id.startsWith('label:') || h.id.startsWith('feed:')) && !childIds.has(h.id))
        .sort((a, b) => a.id.split(':')[1].localeCompare(b.id.split(':')[1]))
    },

    /**
     * Notes that have no parent in the hierarchy.
     */
    rootNotes: (state) => {
      const notesStore = useNotesStore()
      const childIds = new Set()
      state.hierarchy.forEach(h => h.children.forEach(cid => childIds.add(cid)))
      
      // A root note is any hierarchy entry starting with 'note:' that is NOT a child of another node
      return state.hierarchy
        .filter(h => h.id.startsWith('note:') && !childIds.has(h.id))
        .map(h => notesStore.noteById(h.id.replace('note:', '')))
        .filter(Boolean)
        .sort((a, b) => a.title.localeCompare(b.title))
    },

    /**
     * Tree view for the active feed root.
     */
    selectedFeedTree: (state) => {
      if (!state.activeFeedId) return []
      return resolveTree(state, state.activeFeedId)
    },

    activeFeedDisplayName: (state) => {
      if (!state.activeFeedId) return ''
      return state.activeFeedId.split(':')[1]
    }
  },

  actions: {
    async fetchLabels() {
      this.loading = true
      try {
        const { data } = await labelsApi.list()
        this.hierarchy = data
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },

    async createLabel(name, parent = null) {
      try {
        const { data } = await labelsApi.create(name, parent)
        await this.fetchLabels()
        return data
      } catch (err) {
        this.error = err.message
        return null
      }
    },

    async moveLabel(nodeId, newParentId) {
      try {
        await labelsApi.move(nodeId, newParentId)
        await this.fetchLabels()
        return true
      } catch (err) {
        this.error = err.message
        return false
      }
    },

    async reorderNode(nodeId, parentId, index) {
      try {
        await labelsApi.reorder(nodeId, parentId, index)
        await this.fetchLabels()
        return true
      } catch (err) {
        this.error = err.message
        return false
      }
    },

    async deleteLabel(nodeId) {
      try {
        await labelsApi.delete(nodeId)
        await this.fetchLabels()
        return true
      } catch (err) {
        this.error = err.message
        return false
      }
    },

    setActiveLabel(id) {
      this.activeLabel = this.activeLabel === id ? null : id
    },

    async setFeed(id) {
      this.activeFeedId = id
      this.activeLabel = null
    }
  },
})

/**
 * Helper to build hierarchical tree with cycle detection.
 * Resolves "virtual" nodes (nodes mentioned as children but missing from hierarchy list).
 */
function resolveTree(state, rootId) {
  const notesStore = useNotesStore()
  const nodes = {}

  // 1. Build map from explicit hierarchy entries
  state.hierarchy.forEach(h => {
    nodes[h.id] = { ...h, resolvedChildren: [] }
  })

  // 2. Discover and create virtual nodes for children not in hierarchy list
  state.hierarchy.forEach(h => {
    h.children.forEach(cid => {
      if (!nodes[cid]) {
        nodes[cid] = { id: cid, children: [], resolvedChildren: [] }
      }
    })
  })

  const getDisplayName = (id) => {
    if (id.startsWith('note:')) {
      const note = notesStore.noteById(id.replace('note:', ''))
      return note ? note.title : id.split(':')[1]
    }
    if (id.includes(':')) return id.split(':')[1]
    const note = notesStore.noteById(id.replace('note:', ''))
    return note ? note.title : id
  }

  const resolve = (node, path = new Set()) => {
    if (path.has(node.id)) return
    const newPath = new Set(path)
    newPath.add(node.id)

    node.children.forEach(cid => {
      if (nodes[cid]) {
        const childNode = { ...nodes[cid], resolvedChildren: [] }
        node.resolvedChildren.push(childNode)
        resolve(childNode, newPath)
      }
    })
  }

  const root = nodes[rootId]
  if (!root) return []
  const focusedNode = { ...root, resolvedChildren: [] }
  resolve(focusedNode)
  return focusedNode.resolvedChildren
}
