from __future__ import annotations

from app.services.curation.feed import build_feed
from app.services.curation.spotify_playlists import (
    playlists_as_feed_items,
    select_playlists_for_user,
)


def test_different_users_get_different_playlist_sets() -> None:
    signatures = {
        tuple(
            p.playlist_id
            for p in select_playlists_for_user(f"user-{i}", bottleneck="focus", count=2)
        )
        for i in range(24)
    }
    # Same bottleneck, different user hashes → more than one playlist pairing.
    assert len(signatures) > 1


def test_persona_labels_shift_playlist_theme() -> None:
    focus = playlists_as_feed_items(
        "user-same",
        bottleneck="focus",
        attribute_labels=["Deep Work Engineer"],
    )
    burnout = playlists_as_feed_items(
        "user-same",
        bottleneck="focus",
        attribute_labels=["Recovering from burnout"],
    )
    assert focus and burnout
    assert focus[0].metadata["persona_bottleneck"] == "focus"
    assert burnout[0].metadata["persona_bottleneck"] == "burnout"
    assert focus[0].url != burnout[0].url or focus[0].title != burnout[0].title


def test_feed_includes_spotify_persona_cards() -> None:
    feed = build_feed(
        None,
        user_id="user-spotify-demo",
        attribute_labels=["Public speaking confidence"],
    )
    spotify = [item for item in feed.items if item.tag == "Spotify"]
    assert len(spotify) >= 1
    assert all(item.metadata.get("provider") == "spotify" for item in spotify)
    assert all(item.url and "open.spotify.com/playlist/" in item.url for item in spotify)


def test_spotify_oembed_thumbnail_resolved(monkeypatch) -> None:
    from app.services.curation import spotify_playlists as mod

    mod._THUMBNAIL_CACHE.clear()

    class _Resp:
        status_code = 200

        def json(self):
            return {
                "thumbnail_url": "https://i.scdn.co/image/ab67706f00000002deadbeef",
                "title": "Chill Hits",
            }

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url):
            assert "oembed" in url
            return _Resp()

    monkeypatch.setattr(mod.httpx, "Client", _Client)
    thumb = mod.fetch_playlist_thumbnail("37i9dQZF1DX4WYpdgoIcn6")
    assert thumb == "https://i.scdn.co/image/ab67706f00000002deadbeef"
    # Cached — second call must not need network.
    assert mod.fetch_playlist_thumbnail("37i9dQZF1DX4WYpdgoIcn6") == thumb
