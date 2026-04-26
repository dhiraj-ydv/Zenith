# Zenith

> **A local-first, opinionated note-taking app for personal knowledge management and LLM agent integration.**

Zenith enforces a **flat file structure** while providing a powerful **virtual hierarchy**. All relationships are managed via a central YAML index (Map of Content) and `[[wikilinks]]` in Markdown files.

---

## Features

- **Unified Virtual Hierarchy** — Nest labels in labels, notes in labels, and even labels in notes. Organize your knowledge without being constrained by physical folders.
- **Feeds & Library Views** — Toggle between a hierarchical, curated **Feeds** view and a flat, master **Library** view of all notes.
- **3D Knowledge Graph** — An immersive, Obsidian-style 3D visualization of your notes and their wikilink connections.
- **Multi-Parent "Mentions"** — A single note can exist in multiple locations in your hierarchy simultaneously.
- **Context-Aware Actions** — Independent search and creation actions tailored to your current view (Feeds, Library, or focused Hierarchy).
- **YAML Map of Content** — `graph_moc.yaml` is the single source of truth for all virtual relationships and hierarchies.
- **Flat Vault Architecture** — Notes live in a single `/notes` directory. No subdirectories permitted.
- **LLM-Native API** — Token-efficient endpoints designed for AI agent consumption and graph traversal.

---

## Tech Stack

| Layer     | Technology                               |
|-----------|------------------------------------------|
| Backend   | Python 3.10+ · FastAPI · PyYAML          |
| Frontend  | Vue 3 · Vite · Pinia                     |
| Graph     | 3d-force-graph (Three.js)                |
| Markdown  | marked                                   |
| Database  | File System (Markdown + YAML)            |

---

## Getting Started

### Prerequisites

- **Python 3.10+** with `pip`
- **Node.js 18+** with `npm`

### 1. Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Start Developing

```bash
# Start Backend (Port 8000)
cd backend
python main.py

# Start Frontend (Port 5173)
cd ../frontend
npm run dev
```

---

## Vault Structure

```
/vault
├── /notes           # Flat .md files only
├── /attachments     # Media files (images, PDFs)
└── graph_moc.yaml   # Master index (hierarchy + edges)
```

---

## API Endpoints

### Hierarchy & Labels
| Method   | Endpoint                  | Description                     |
|----------|---------------------------|---------------------------------|
| `GET`    | `/api/labels`             | List full hierarchy nodes       |
| `POST`   | `/api/labels`             | Create a new label/node         |
| `POST`   | `/api/labels/{id}/move`   | Move or mention a node          |
| `DELETE` | `/api/labels/{id}`        | Remove node from hierarchy      |

### Notes
| Method   | Endpoint                  | Description            |
|----------|---------------------------|------------------------|
| `GET`    | `/api/notes`              | List all notes         |
| `GET`    | `/api/notes/{id}`         | Get note by ID         |
| `POST`   | `/api/notes`              | Create note            |
| `PUT`    | `/api/notes/{id}`         | Update note + labels   |
| `DELETE` | `/api/notes/{id}`         | Delete note + GC       |

---

## YAML MOC Schema (v1.1)

```yaml
version: 1.1
hierarchy:
  - id: "label:Work"
    children: ["label:Work/Projects", "note:meeting_notes"]
  - id: "label:Work/Projects"
    children: ["note:project_zenith"]
  - id: "note:project_zenith"
    children: []
edges:
  - from: note_id_1
    to: note_id_2
    type: reference
```

---

## License

MIT
