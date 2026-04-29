import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.attachments import AttachmentService
from services.moc import MOCService
from services.notes import NoteService
from services import vault as vault_module
from services.vault import VaultManager
from routers import labels as labels_router
from models import LabelCreate


@pytest.fixture
def services(tmp_path):
    settings_dir = tmp_path / "settings"
    original_dir = vault_module.SETTINGS_DIR
    original_file = vault_module.SETTINGS_FILE
    vault_module.SETTINGS_DIR = settings_dir
    vault_module.SETTINGS_FILE = settings_dir / "settings.json"

    vault = tmp_path / "vault"
    manager = VaultManager()
    manager.set_active_vault(str(vault))

    moc = MOCService(manager)
    moc.load()
    attachments = AttachmentService(manager)
    notes = NoteService(moc, attachments, manager)
    try:
        yield manager, moc, notes
    finally:
        vault_module.SETTINGS_DIR = original_dir
        vault_module.SETTINGS_FILE = original_file


def hierarchy_map(moc):
    return {node.id: list(node.children) for node in moc.get().hierarchy}


def test_supports_multiple_note_parents_on_create(services):
    _, moc, notes = services

    moc.add_to_hierarchy("feed:alpha")
    moc.add_to_hierarchy("label:beta", "feed:alpha")

    notes.create_note("Shared Note", labels=["feed:alpha", "label:beta"])

    graph = hierarchy_map(moc)
    assert "note:shared_note" in graph["feed:alpha"]
    assert "note:shared_note" in graph["label:beta"]


def test_supports_cross_type_nesting_and_siblings(services):
    _, moc, notes = services

    moc.add_to_hierarchy("feed:eryserysery")
    notes.create_note("Parent Note", labels=["feed:eryserysery"])
    notes.create_note("Sibling Note", labels=["feed:eryserysery"])
    moc.add_to_hierarchy("label:child", "feed:eryserysery")

    moc.move_node("label:child", "note:parent_note")

    graph = hierarchy_map(moc)
    assert set(graph["feed:eryserysery"]) == {
        "note:parent_note",
        "note:sibling_note",
    }
    assert graph["note:parent_note"] == ["label:child"]


def test_create_note_directly_under_note_parent(services):
    _, moc, notes = services

    moc.add_to_hierarchy("feed:stack")
    notes.create_note("Parent", labels=["feed:stack"])
    notes.create_note("Child", labels=["note:parent"])

    graph = hierarchy_map(moc)
    assert graph["feed:stack"] == ["note:parent"]
    assert graph["note:parent"] == ["note:child"]


def test_prevents_cycles_when_reparenting(services):
    _, moc, notes = services

    moc.add_to_hierarchy("feed:f")
    notes.create_note("Parent", labels=["feed:f"])
    moc.add_to_hierarchy("label:l", "note:parent")

    moc.move_node("note:parent", "label:l")

    graph = hierarchy_map(moc)
    assert graph["feed:f"] == ["note:parent"]
    assert graph["note:parent"] == ["label:l"]
    assert graph["label:l"] == []


def test_updating_note_labels_preserves_nested_children(services):
    _, moc, notes = services

    moc.add_to_hierarchy("feed:old")
    moc.add_to_hierarchy("feed:new")
    notes.create_note("Carrier", labels=["feed:old"])
    moc.add_to_hierarchy("label:nested", "note:carrier")

    notes.update_note("carrier", labels=["feed:new"])

    graph = hierarchy_map(moc)
    assert "note:carrier" not in graph["feed:old"]
    assert "note:carrier" in graph["feed:new"]
    assert graph["note:carrier"] == ["label:nested"]


@pytest.mark.anyio
async def test_nested_label_creation_does_not_promote_to_feed(services):
    _, moc, _ = services
    labels_router.moc_service = moc

    moc.add_to_hierarchy("feed:parent")
    await labels_router.create_label(LabelCreate(name="label:child", parent="feed:parent"))

    graph = hierarchy_map(moc)
    assert "label:child" in graph["feed:parent"]
    assert "feed:child" not in graph


def test_reorder_children_preserves_manual_order(services):
    _, moc, notes = services

    moc.add_to_hierarchy("feed:ordered")
    notes.create_note("First", labels=["feed:ordered"])
    notes.create_note("Second", labels=["feed:ordered"])
    moc.add_to_hierarchy("label:third", "feed:ordered")

    moc.reorder_node("label:third", "feed:ordered", 0)

    graph = hierarchy_map(moc)
    assert graph["feed:ordered"] == ["label:third", "note:first", "note:second"]


def test_reorder_root_nodes_preserves_manual_order(services):
    _, moc, notes = services

    moc.add_to_hierarchy("feed:alpha")
    notes.create_note("Root Note")
    moc.add_to_hierarchy("feed:beta")

    moc.reorder_node("note:root_note", None, 0)

    root_ids = [node.id for node in moc.get().hierarchy if node.id in {"feed:alpha", "note:root_note", "feed:beta"}]
    assert root_ids[:3] == ["note:root_note", "feed:alpha", "feed:beta"]
