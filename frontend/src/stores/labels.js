/**
 * Labels Store — Pinia store for virtual folder management.
 */
import { defineStore } from 'pinia'
import { labelsApi } from '../api/client'
import { useNotesStore } from './notes'

export const useLabelsStore = defineStore('labels', {
  state: () => ({
    hierarchy: [], // Array of {id, children}
    activeFeedId: null, // The root node being viewed
    activeLabel: null,
    loading: false,
    error: null,
  }),

  getters: {
    /**
     * Top-level roots for the "Feeds" list.
     */
    rootFeeds: (state) => {
      const childIds = new Set()
      state.hierarchy.forEach(h => {
        h.children.forEach(cid => childIds.add(cid))
      })
      // Roots are nodes that are not children of any other node
      return state.hierarchy.filter(h => !childIds.has(h.id))
    },

    /**
     * Focused tree starting from activeFeedId.
     */
    selectedFeedTree: (state) => {
      if (!state.activeFeedId) return []
      
      const notesStore = useNotesStore()
      const nodes = {}
      state.hierarchy.forEach(h => {
        nodes[h.id] = { ...h, resolvedChildren: [] }
      })

      const getDisplayName = (id) => {
        if (id.startsWith('label:')) return id.replace('label:', '', 1)
        const noteId = id.replace('note:', '', 1)
        const note = notesStore.noteById(noteId)
        return note ? note.title : noteId
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
        node.resolvedChildren.sort((a, b) => getDisplayName(a.id).localeCompare(getDisplayName(b.id)))
      }

      const root = nodes[state.activeFeedId]
      if (!root) return []
      
      const focusedNode = { ...root, resolvedChildren: [] }
      resolve(focusedNode)
      return focusedNode.resolvedChildren
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

    async createLabel(name) {
      try {
        const { data } = await labelsApi.create(name)
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

    setFeed(id) {
      this.activeFeedId = id
      this.activeLabel = null // Reset selected label when switching feeds
    },
  },
})
