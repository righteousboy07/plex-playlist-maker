from types import SimpleNamespace

import plex_curator as core
import plex_curator_api as api


class FakeSession:
    delete = object()


class FakeServer:
    def __init__(self):
        self._session = FakeSession()
        self.deleted_keys = []

    def query(self, key, method=None):
        self.deleted_keys.append((key, method))


class FakePlaylist:
    def __init__(self, title="Test Playlist", items=None, smart=False):
        self.title = title
        self.key = "/playlists/99"
        self.smart = smart
        self.playlistType = "video"
        self.ratingKey = "99"
        self.updatedAt = None
        self._server = FakeServer()
        self._items = list(items or [])
        self.moves = []

    def items(self):
        return list(self._items)

    def moveItem(self, item, after=None):
        self.moves.append((item.playlistItemID, getattr(after, "playlistItemID", None)))
        return self


class FakePlex:
    def __init__(self):
        self.created = []

    def createPlaylist(self, name, items):
        created = FakePlaylist(title=name, items=items)
        created.ratingKey = "100"
        self.created.append((name, list(items)))
        return created


def media(rating_key, playlist_item_id, title):
    return SimpleNamespace(
        ratingKey=str(rating_key),
        playlistItemID=playlist_item_id,
        title=title,
    )


def test_playlist_remove_item_targets_exact_playlist_occurrence(monkeypatch):
    first = media(1, 11, "Episode")
    duplicate = media(1, 12, "Episode")
    playlist = FakePlaylist(items=[first, duplicate])
    plex = FakePlex()

    monkeypatch.setattr(core, "connect", lambda: plex)
    monkeypatch.setattr(core, "find_playlist", lambda _plex, _name: playlist)

    result = api.playlist_remove_item(
        name="Test Playlist",
        playlist_item_id=12,
        _authorized=True,
    )

    assert result["ok"] is True
    assert result["removed_count"] == 1
    assert result["item_count"] == 1
    assert playlist._server.deleted_keys[0][0] == "/playlists/99/items/12"


def test_playlist_move_up_uses_previous_previous_item_as_anchor(monkeypatch):
    items = [media(1, 11, "A"), media(2, 12, "B"), media(3, 13, "C")]
    playlist = FakePlaylist(items=items)
    plex = FakePlex()

    monkeypatch.setattr(core, "connect", lambda: plex)
    monkeypatch.setattr(core, "find_playlist", lambda _plex, _name: playlist)

    result = api.playlist_move_item(
        name="Test Playlist",
        request=api.PlaylistItemMoveRequest(playlist_item_id=13, direction="up"),
        _authorized=True,
    )

    assert result["moved"] is True
    assert playlist.moves == [(13, 11)]


def test_playlist_move_first_item_up_is_noop(monkeypatch):
    items = [media(1, 11, "A"), media(2, 12, "B")]
    playlist = FakePlaylist(items=items)
    plex = FakePlex()

    monkeypatch.setattr(core, "connect", lambda: plex)
    monkeypatch.setattr(core, "find_playlist", lambda _plex, _name: playlist)

    result = api.playlist_move_item(
        name="Test Playlist",
        request=api.PlaylistItemMoveRequest(playlist_item_id=11, direction="up"),
        _authorized=True,
    )

    assert result["moved"] is False
    assert playlist.moves == []


def test_playlist_move_down_anchors_after_next_item(monkeypatch):
    items = [media(1, 11, "A"), media(2, 12, "B"), media(3, 13, "C")]
    playlist = FakePlaylist(items=items)
    plex = FakePlex()

    monkeypatch.setattr(core, "connect", lambda: plex)
    monkeypatch.setattr(core, "find_playlist", lambda _plex, _name: playlist)

    result = api.playlist_move_item(
        name="Test Playlist",
        request=api.PlaylistItemMoveRequest(playlist_item_id=12, direction="down"),
        _authorized=True,
    )

    assert result["moved"] is True
    assert playlist.moves == [(12, 13)]


def test_playlist_copy_preserves_item_order(monkeypatch):
    items = [media(1, 11, "A"), media(2, 12, "B"), media(3, 13, "C")]
    source = FakePlaylist(items=items)
    plex = FakePlex()

    def find_playlist(_plex, name):
        if name == "Test Playlist":
            return source
        return None

    monkeypatch.setattr(core, "connect", lambda: plex)
    monkeypatch.setattr(core, "find_playlist", find_playlist)

    result = api.playlist_copy(
        api.PlaylistCopyRequest(
            current_name="Test Playlist",
            new_name="Test Playlist Copy",
        ),
        _authorized=True,
    )

    assert result["ok"] is True
    assert result["playlist"]["title"] == "Test Playlist Copy"
    assert [item.playlistItemID for item in plex.created[0][1]] == [11, 12, 13]


def test_playlist_bulk_remove_targets_exact_ids(monkeypatch):
    items = [media(1, 11, "A"), media(2, 12, "B"), media(3, 13, "C")]
    playlist = FakePlaylist(items=items)
    plex = FakePlex()

    monkeypatch.setattr(core, "connect", lambda: plex)
    monkeypatch.setattr(core, "find_playlist", lambda _plex, _name: playlist)

    result = api.playlist_remove_items(
        name="Test Playlist",
        request=api.PlaylistItemsMutationRequest(playlist_item_ids=[11, 13]),
        _authorized=True,
    )

    assert result["removed_count"] == 2
    assert result["item_count"] == 1
    assert [entry[0] for entry in playlist._server.deleted_keys] == [
        "/playlists/99/items/11",
        "/playlists/99/items/13",
    ]


def test_playlist_copy_selection_preserves_source_order(monkeypatch):
    items = [media(1, 11, "A"), media(2, 12, "B"), media(3, 13, "C")]
    source = FakePlaylist(items=items)
    plex = FakePlex()

    def find_playlist(_plex, name):
        if name == "Test Playlist":
            return source
        return None

    monkeypatch.setattr(core, "connect", lambda: plex)
    monkeypatch.setattr(core, "find_playlist", find_playlist)

    result = api.playlist_copy_selection(
        api.PlaylistSelectionCopyRequest(
            current_name="Test Playlist",
            new_name="Picked",
            playlist_item_ids=[13, 11],
        ),
        _authorized=True,
    )

    assert result["ok"] is True
    assert result["playlist"]["item_count"] == 2
    assert [item.playlistItemID for item in plex.created[0][1]] == [11, 13]
