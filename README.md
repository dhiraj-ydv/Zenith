# Zenith

> **A local-first, opinionated note-taking app for personal knowledge management and LLM agent integration.**

Zenith enforces a **flat file structure** while providing a powerful **virtual hierarchy**. All relationships are managed via a central YAML index (Map of Content) and `[[wikilinks]]` in Markdown files.

---

## Features

- **Unified Virtual Hierarchy** — Nest labels in labels, notes in labels, and even labels in notes. Organize your knowledge without being constrained by physical folders.
- **Visual Brainstorming with Excalidraw** — Full-screen, immersive drawing editor integrated directly into the note-taking workflow.
- **In-Note Drawing Embeds** — Embed drawings in any Markdown note using `![[DrawingName.excalidraw]]`.
- **Live SVG Previews** — Drawings render as crisp, interactive SVGs directly within your notes, bridging the gap between text and visuals.
- **Slash Commands** — Use `/excali` within any note to instantly create and jump into a new drawing.
- **Attachment Uploads** — Use `/upload` in the editor to add images, video, audio, or PDFs into the current note and store them under `/attachments/Uploads`.
- **Inline Attachment Embeds** — Images render directly in preview; other attachments insert as embeds or preview blocks depending on file type.
- **Feeds & Library Views** — Toggle between a hierarchical, curated **Feeds** view and a flat, master **Library** view of all notes.
- **3D Knowledge Graph** — An immersive, Obsidian-style 3D visualization of your notes and their wikilink connections.
- **Multi-Parent "Mentions"** — A single note can exist in multiple locations in your hierarchy simultaneously.
- **YAML Map of Content** — `graph_moc.yaml` is the single source of truth for all virtual relationships and hierarchies.
- **LLM-Native API** — Token-efficient endpoints designed for AI agent consumption and graph traversal.

---

## Tech Stack

| Layer     | Technology                               |
|-----------|------------------------------------------|
| Backend   | Python 3.10+ · FastAPI · PyYAML          |
| Frontend  | Vue 3 · Vite · Pinia                     |
| Drawing   | Excalidraw (React-in-Vue via Veaury)     |
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
├── /notes           # Flat .md and .excalidraw files
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
| `POST`   | `/api/notes`              | Create note or drawing |
| `PUT`    | `/api/notes/{id}`         | Update note content    |
| `DELETE` | `/api/notes/{id}`         | Delete note + GC       |

### Attachments
| Method   | Endpoint                      | Description                         |
|----------|-------------------------------|-------------------------------------|
| `POST`   | `/api/attachments`            | Upload a media file                 |
| `GET`    | `/api/attachments/{filename}` | Serve an uploaded attachment inline |

---

## Notes

- Attachment upload is available through the editor's `/upload` command.
- PDF preview rendering is browser-dependent; if inline rendering fails, the app falls back to a direct file link.

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
