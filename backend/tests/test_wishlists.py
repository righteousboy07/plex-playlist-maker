from types import SimpleNamespace

import pytest

import plex_curator_api as api


class FakePlaylist:
    def __init__(self, title, items=None, rating_key="1"):
        self.title = title
        self.leafCount = len(items or [])
        self.ratingKey = rating_key
        self._items = items or []

    def items(self):
        return list(self._items)


def _patch_wishlist_paths(tmp_path, monkeypatch):
    config = tmp_path / "config"
    examples = tmp_path / "examples"
    config.mkdir()
    examples.mkdir()
    monkeypatch.setattr(api.core, "CONFIG_DIR", config)
    monkeypatch.setattr(api, "KIDS_SCARY_WISHLIST", config / "kids-scary-wishlist.txt")
    monkeypatch.setattr(api, "KIDS_SCARY_WISHLIST_SEED", examples / "kids-scary-missing-wishlist.txt")
    monkeypatch.setattr(api, "WISHLISTS_FILE", config / "wishlists.json")
    return config, examples


def test_wishlist_migration_preserves_legacy_entries(tmp_path, monkeypatch):
    _config, examples = _patch_wishlist_paths(tmp_path, monkeypatch)
    (examples / "kids-scary-missing-wishlist.txt").write_text(
        "Coraline | 2009\nMonster House | 2006\n",
        encoding="utf-8",
    )

    data = api.load_wishlists()

    assert len(data["wishlists"]) == 1
    wishlist = data["wishlists"][0]
    assert wishlist["id"] == "kids-scary"
    assert wishlist["name"] == "Kids Scary"
    assert wishlist["entries"] == [
        {"title": "Coraline", "year": 2009},
        {"title": "Monster House", "year": 2006},
    ]


def test_wishlist_create_update_delete(tmp_path, monkeypatch):
    _patch_wishlist_paths(tmp_path, monkeypatch)
    api.save_wishlists({"version": 1, "wishlists": []})

    created = api.create_wishlist(
        api.WishlistDefinitionRequest(
            name="Halloween",
            description="October movies",
            library="Movies",
            keywords=["halloween", "spooky"],
            entries=[api.WishlistItemRequest(title="Coraline", year=2009)],
        ),
        _authorized=True,
    )
    wishlist_id = created["wishlist"]["id"]

    _data, wishlist = api.wishlist_or_404(wishlist_id)
    assert wishlist["keywords"] == ["halloween", "spooky"]

    updated = api.update_wishlist(
        wishlist_id,
        api.WishlistDefinitionRequest(
            name="Family Halloween",
            description="Updated",
            library="Movies",
            keywords=["kids", "Halloween", "kids"],
            entries=[
                api.WishlistItemRequest(title="Coraline", year=2009),
                api.WishlistItemRequest(title="Coraline", year=2009),
            ],
        ),
        _authorized=True,
    )
    assert updated["wishlist"]["name"] == "Family Halloween"
    _data, wishlist = api.wishlist_or_404(wishlist_id)
    assert wishlist["keywords"] == ["kids", "Halloween"]
    assert len(wishlist["entries"]) == 1

    api.delete_wishlist(wishlist_id, _authorized=True)
    assert api.load_wishlists()["wishlists"] == []


def test_keyword_playlist_discovery_is_case_insensitive(tmp_path, monkeypatch):
    _patch_wishlist_paths(tmp_path, monkeypatch)
    wishlist = {
        "id": "halloween",
        "name": "Halloween",
        "description": "",
        "library": "Movies",
        "keywords": ["scary", "Kids"],
        "entries": [],
    }
    fake_plex = SimpleNamespace(
        playlists=lambda: [
            FakePlaylist("Kids Halloween"),
            FakePlaylist("Really Scary Movies"),
            FakePlaylist("Comedy"),
        ]
    )
    monkeypatch.setattr(api.core, "connect", lambda: fake_plex)

    matches = api.matching_plex_playlists(wishlist)

    assert [item["title"] for item in matches] == [
        "Kids Halloween",
        "Really Scary Movies",
    ]
    assert matches[0]["matched_keywords"] == ["Kids"]
    assert matches[1]["matched_keywords"] == ["scary"]


def test_import_matching_playlists_deduplicates_entries(tmp_path, monkeypatch):
    _patch_wishlist_paths(tmp_path, monkeypatch)
    api.save_wishlists({
        "version": 1,
        "wishlists": [{
            "id": "halloween",
            "name": "Halloween",
            "description": "",
            "library": "Movies",
            "keywords": ["halloween"],
            "entries": [{"title": "Coraline", "year": 2009}],
        }],
    })

    fake_plex = SimpleNamespace(
        playlists=lambda: [
            FakePlaylist(
                "Halloween Favorites",
                items=[
                    SimpleNamespace(title="Coraline", year=2009),
                    SimpleNamespace(title="Monster House", year=2006),
                ],
            ),
            FakePlaylist("Comedy", items=[SimpleNamespace(title="Elf", year=2003)]),
        ]
    )
    monkeypatch.setattr(api.core, "connect", lambda: fake_plex)

    result = api.import_wishlist_playlists(
        "halloween",
        api.WishlistImportRequest(playlist_names=[]),
        _authorized=True,
    )

    assert result["playlist_count"] == 1
    assert result["imported_count"] == 1
    assert result["entry_count"] == 2
    _data, wishlist = api.wishlist_or_404("halloween")
    assert wishlist["entries"] == [
        {"title": "Coraline", "year": 2009},
        {"title": "Monster House", "year": 2006},
    ]


def test_import_matching_playlists_enumerates_plex_once(tmp_path, monkeypatch):
    _patch_wishlist_paths(tmp_path, monkeypatch)
    api.save_wishlists({
        "version": 1,
        "wishlists": [{
            "id": "halloween",
            "name": "Halloween",
            "description": "",
            "library": "Movies",
            "keywords": ["halloween"],
            "entries": [],
        }],
    })

    calls = {"playlists": 0}

    class Plex:
        def playlists(self):
            calls["playlists"] += 1
            return [
                FakePlaylist(
                    "Halloween Favorites",
                    items=[SimpleNamespace(title="Coraline", year=2009)],
                )
            ]

    monkeypatch.setattr(api.core, "connect", lambda: Plex())

    result = api.import_wishlist_playlists(
        "halloween",
        api.WishlistImportRequest(playlist_names=[]),
        _authorized=True,
    )

    assert result["imported_count"] == 1
    assert calls["playlists"] == 1


def test_wishlist_rejects_blank_name_and_library(tmp_path, monkeypatch):
    _patch_wishlist_paths(tmp_path, monkeypatch)
    api.save_wishlists({"version": 1, "wishlists": []})

    with pytest.raises(api.HTTPException) as name_error:
        api.create_wishlist(
            api.WishlistDefinitionRequest(
                name="   ",
                library="Movies",
            ),
            _authorized=True,
        )
    assert name_error.value.status_code == 422
    assert "name" in name_error.value.detail.lower()

    with pytest.raises(api.HTTPException) as library_error:
        api.create_wishlist(
            api.WishlistDefinitionRequest(
                name="Halloween",
                library="   ",
            ),
            _authorized=True,
        )
    assert library_error.value.status_code == 422
    assert "library" in library_error.value.detail.lower()


def test_store_automation_uses_structured_kids_scary_wishlist(tmp_path, monkeypatch):
    _patch_wishlist_paths(tmp_path, monkeypatch)
    api.save_wishlists({
        "version": 1,
        "wishlists": [{
            "id": "kids-scary",
            "name": "Kids Scary",
            "description": "",
            "library": "Movies",
            "keywords": ["kids", "scary"],
            "entries": [
                {"title": "Coraline", "year": 2009},
                {"title": "Monster House", "year": 2006},
            ],
        }],
    })

    monkeypatch.setattr(
        api,
        "resolved_wishlist",
        lambda wishlist: {
            **api.wishlist_summary(wishlist),
            "found_count": 1,
            "missing_count": 1,
            "total_count": 2,
            "entries": [
                {
                    "requested_title": "Coraline",
                    "requested_year": 2009,
                    "found": True,
                    "matched_title": "Coraline",
                    "item": {},
                },
                {
                    "requested_title": "Monster House",
                    "requested_year": 2006,
                    "found": False,
                    "matched_title": None,
                    "item": None,
                },
            ],
        },
    )

    output = api._run_store_automation_job("kids-scary-wishlist")

    assert "Coraline (2009)" in output
    assert "Monster House (2006)" in output
    assert api.STORE_AUTOMATION_JOBS["kids-scary-wishlist"]["wishlist_id"] == "kids-scary"
    assert "args" not in api.STORE_AUTOMATION_JOBS["kids-scary-wishlist"]
