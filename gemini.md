# Zenith - System Context & Guidelines

This document provides foundational mandates and architectural instructions for AI agents working on Zenith.

## 1. Project Philosophy & Identity
Zenith is a **local-first, virtual-hierarchy note-taking application**. It rejects physical folder structures in favor of a strictly flat filesystem backed by a powerful, multi-parent virtual tree.

### Core Constraints
- **Strictly Flat File Structure**: All notes (`.md`) and drawings (`.excalidraw`) must reside in the root of the active vault's `/notes` directory. Media must be in `/attachments`. **Subdirectories are strictly forbidden.**
- **Virtual Hierarchy (P&C)**: Organization is managed via a many-to-many relationship tree in `graph_moc.yaml`. Notes and labels can be nested interchangeably.
- **YAML Source of Truth**: `graph_moc.yaml` is the absolute source of truth for the Library's structure. If a file exists in `/notes` but is missing from the YAML, the backend must automatically sync it as a root node.
- **Referential Integrity**: Attachments use a reference counting system. Orphaned attachments must be garbage-collected.

## 2. Technology Stack
### Backend
- **Framework**: Python 3.10+ with FastAPI.
- **Hierarchy Management**: Managed by `MOCService` using a recursive `HierarchyEntry` model.
- **Persistence**: File System only (Markdown + YAML). Global state in `~/.zenith/settings.json`.

### Frontend
- **Framework**: Vue 3 (Composition API).
- **React Integration**: Uses `veaury` to host Excalidraw (React) within the Vue app.
- **Visualization**: **3D-force-graph** (Three.js) for an immersive Obsidian-style experience.
- **State Management**: Pinia.
- **Navigation**: Dual-mode sidebar (Feeds vs. Library) with drill-down focused views.

## 3. Architecture & Service Patterns
### Unified Hierarchy
- All nodes in the tree have IDs prefixed with `label:` or `note:`.
- **Feeds**: Root-level labels that act as primary organizational streams.
- **Labels**: Nested organizational units within Feeds.
- **Mentions**: Notes can have multiple parents in the hierarchy.

### Drawing Workflow
- **Creation**: Triggered via `/excali` slash command in the editor.
- **Embedding**: Uses `![[id.excalidraw]]` syntax.
- **Rendering**: The `ExcalidrawPreview` component renders embedded drawings as SVGs using the Excalidraw engine.
- **Safe Persistence**: The drawing editor ensures all changes are flushed to disk before closing to prevent data loss.

### Attachment Workflow
- **Upload Trigger**: `/upload` opens the file picker from the editor after a user-initiated input event.
- **Supported Types**: Images, video, audio, and PDFs are accepted and stored in `/attachments/Uploads`.
- **Embedding**: Images use wiki-style embeds; PDFs are shown in a preview block with a fallback direct link.
- **Current Caveat**: PDF inline rendering can vary by browser; treat the direct link as the reliable fallback.

## 4. Standard Operating Procedures for AI
1. **Never create subdirectories** inside the vault.
2. **Persistence First**: Every move, rename, or creation must be immediately reflected in `graph_moc.yaml`.
3. **Handle Many-to-Many**: When resolving the tree in the frontend, always use cycle detection to prevent infinite recursion, as nodes may appear in multiple branches.
4. **Contextual Actions**: Maintain independent search and creation logic for different views (Library, Feeds List, Focused Feed).
5. **3D Graph**: Ensure the Knowledge Graph only renders note-to-note `[[wikilink]]` connections for clarity.
