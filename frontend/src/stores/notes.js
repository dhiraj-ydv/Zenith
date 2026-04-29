/**
 * Notes Store — Pinia store for note and drawing management.
 */
import { defineStore } from 'pinia'
import { notesApi } from '../api/client'

export const useNotesStore = defineStore('notes', {
  state: () => ({
    notes: [],
    activeNote: null,
    loading: false,
    saving: false,
    error: null,
    searchResults: [],
  }),

  getters: {
    noteById: (state) => (id) => state.notes.find((n) => n.id === id),
    noteCount: (state) => state.notes.length,
  },

  actions: {
    async fetchNotes(label = null) {
      this.loading = true
      this.error = null
      try {
        const { data } = await notesApi.list(label)
        this.notes = data
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },

    async fetchNote(id) {
      this.loading = true
      this.error = null
      try {
        const { data } = await notesApi.get(id)
        this.activeNote = data
        return data
      } catch (err) {
        this.error = err.message
        return null
      } finally {
        this.loading = false
      }
    },

    async createNote(title, content = '', labels = [], type = 'markdown', setActive = true) {
      this.error = null
      try {
        const { data } = await notesApi.create({ title, content, labels, type })
        this.notes.push({ id: data.id, title: data.title, labels: data.labels, type: data.type })
        if (setActive) {
          this.activeNote = data
        }
        return data
      } catch (err) {
        this.error = err.response?.data?.detail || err.message
        return null
      }
    },

    async updateNote(id, content, labels) {
      this.saving = true
      this.error = null
      try {
        const payload = {}
        if (content !== undefined) payload.content = content
        if (labels !== undefined) payload.labels = labels
        const { data } = await notesApi.update(id, payload)
        this.activeNote = data
        const idx = this.notes.findIndex((n) => n.id === id)
        if (idx >= 0) {
          this.notes[idx] = { ...data, content: data.content || content }
        }
        return data
      } catch (err) {
        this.error = err.message
        return null
      } finally {
        this.saving = false
      }
    },

    async updateNoteLabels(id, labels) {
      this.error = null
      try {
        const { data } = await notesApi.update(id, { labels })
        const idx = this.notes.findIndex((n) => n.id === id)
        if (idx >= 0) {
          this.notes[idx].labels = data.labels
        }
        if (this.activeNote?.id === id) {
          this.activeNote.labels = data.labels
        }
        return data
      } catch (err) {
        this.error = err.message
        return null
      }
    },

    async deleteNote(id) {
      this.error = null
      try {
        await notesApi.delete(id)
        this.notes = this.notes.filter((n) => n.id !== id)
        if (this.activeNote?.id === id) {
          this.activeNote = null
        }
        return true
      } catch (err) {
        this.error = err.message
        return false
      }
    },

    async renameNote(id, newTitle) {
      this.error = null
      try {
        const { data } = await notesApi.rename(id, newTitle)
        this.notes = this.notes.filter((n) => n.id !== id)
        this.notes.push({ id: data.id, title: data.title, labels: data.labels, type: data.type })
        this.activeNote = data
        return data
      } catch (err) {
        this.error = err.response?.data?.detail || err.message
        return null
      }
    },

    async searchNotes(query) {
      if (!query || query.length < 1) {
        this.searchResults = []
        return
      }
      try {
        const { data } = await notesApi.search(query)
        this.searchResults = data
      } catch {
        this.searchResults = []
      }
    },

    async openXjournal(id) {
      try {
        await fetch(`/api/xjournal/${id}/open`, { method: 'POST' })
        return true
      } catch (err) {
        console.error('Failed to open Xjournal++:', err)
        return false
      }
    },

    saveScrollPosition(id, pos) {
      if (!id) return
      try {
        const positions = JSON.parse(localStorage.getItem('zenith_scroll_positions') || '{}')
        positions[id] = pos
        localStorage.setItem('zenith_scroll_positions', JSON.stringify(positions))
      } catch (e) {
        console.error('Failed to save scroll position', e)
      }
    },

    getScrollPosition(id) {
      if (!id) return { textarea: 0, preview: 0 }
      try {
        const positions = JSON.parse(localStorage.getItem('zenith_scroll_positions') || '{}')
        return positions[id] || { textarea: 0, preview: 0 }
      } catch (e) {
        return { textarea: 0, preview: 0 }
      }
    },
  },
})
