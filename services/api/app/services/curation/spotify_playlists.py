"""Persona-keyed Spotify playlist deep-links for the Growth Feed.

No Spotify OAuth — public playlist URLs only. Selection is deterministic per
user (hash of user_id + bottleneck + identity labels) so two users with
different personas see different playlists, and the same user stays stable.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import httpx

from app.schemas.feed import FeedItem
from app.schemas.stack import StackExplanation

# playlist_id → cover URL (or "" if oEmbed failed). Avoids repeat network hits.
_THUMBNAIL_CACHE: dict[str, str] = {}


@dataclass(frozen=True)
class SpotifyPlaylist:
    playlist_id: str
    title: str
    curator: str
    mood: str
    why: str

    @property
    def url(self) -> str:
        return f"https://open.spotify.com/playlist/{self.playlist_id}"


def fetch_playlist_thumbnail(playlist_id: str, *, timeout: float = 1.5) -> str | None:
    """Resolve cover art via Spotify's public oEmbed endpoint (no OAuth)."""
    if playlist_id in _THUMBNAIL_CACHE:
        cached = _THUMBNAIL_CACHE[playlist_id]
        return cached or None

    url = f"https://open.spotify.com/oembed?url=https://open.spotify.com/playlist/{playlist_id}"
    try:
        with httpx.Client(timeout=timeout) as client:
            res = client.get(url)
            if res.status_code != 200:
                _THUMBNAIL_CACHE[playlist_id] = ""
                return None
            data = res.json()
            thumb = data.get("thumbnail_url") if isinstance(data, dict) else None
            if isinstance(thumb, str) and thumb.startswith("http"):
                _THUMBNAIL_CACHE[playlist_id] = thumb
                return thumb
    except Exception:
        pass

    _THUMBNAIL_CACHE[playlist_id] = ""
    return None


# Bottleneck → editorial / well-known public playlists (Spotify open URLs).
_BY_BOTTLENECK: dict[str, tuple[SpotifyPlaylist, ...]] = {
    "focus": (
        SpotifyPlaylist(
            "37i9dQZF1DWZeKCadgRdKQ",
            "Deep Focus",
            "Spotify",
            "deep work",
            "Instrumental focus music matched to a focus-drift bottleneck.",
        ),
        SpotifyPlaylist(
            "37i9dQZF1DX8NTLI2TtZa6",
            "Intense Studying",
            "Spotify",
            "study flow",
            "Keeps cognitive load low while you ship the next micro-rep.",
        ),
        SpotifyPlaylist(
            "37i9dQZF1DWWQRwui0ExPn",
            "lofi beats",
            "Spotify",
            "lo-fi",
            "Soft loops that reduce tab-hopping during declared focus windows.",
        ),
        SpotifyPlaylist(
            "37i9dQZF1DX4sWSpwq3LiO",
            "Peaceful Piano",
            "Spotify",
            "calm piano",
            "Quiet backdrop for deep work without lyric distraction.",
        ),
    ),
    "confidence": (
        SpotifyPlaylist(
            "37i9dQZF1DX1g0iEXLFyA2",
            "Confidence Boost",
            "Spotify",
            "uplift",
            "Upbeat energy before a public speaking or visibility rep.",
        ),
        SpotifyPlaylist(
            "37i9dQZF1DX1s9knjP51Oa",
            "Calm Before the Storm",
            "Spotify",
            "pre-stage calm",
            "Settles nerves before a high-stakes moment.",
        ),
        SpotifyPlaylist(
            "37i9dQZF1DX3rxVfibe1L0",
            "Mood Booster",
            "Spotify",
            "boost",
            "Lifts affect when the bottleneck is confidence, not knowledge.",
        ),
        SpotifyPlaylist(
            "37i9dQZF1DX0XUs1Wbyxck",
            "Latin Pop Classics",
            "Spotify",
            "energy",
            "Bright tempo for warming into a courageous micro-action.",
        ),
    ),
    "communication": (
        SpotifyPlaylist(
            "37i9dQZF1DXcBWIGoYBM5M",
            "Today's Top Hits",
            "Spotify",
            "current voice",
            "Contemporary phrasing cues while you practice clearer delivery.",
        ),
        SpotifyPlaylist(
            "37i9dQZF1DX0SM0LYsmbMT",
            "Jazz Vibes",
            "Spotify",
            "conversational jazz",
            "Call-and-response feel that mirrors good dialogue rhythm.",
        ),
        SpotifyPlaylist(
            "37i9dQZF1DWWEJlAGA9gs0",
            "Classical Essentials",
            "Spotify",
            "clarity",
            "Structured listening before a talk outline or pitch draft.",
        ),
        SpotifyPlaylist(
            "37i9dQZF1DX4WYpdgoIcn6",
            "Chill Hits",
            "Spotify",
            "ease",
            "Low-pressure soundtrack for rehearsal reps.",
        ),
    ),
    "discipline": (
        SpotifyPlaylist(
            "37i9dQZF1DX76Wlfdnj7AP",
            "Beast Mode",
            "Spotify",
            "drive",
            "High-intensity cue for sticking the planned block.",
        ),
        SpotifyPlaylist(
            "37i9dQZF1DX70RN3TfWWJh",
            "Workout",
            "Spotify",
            "stamina",
            "Keeps cadence when consistency is the limiting factor.",
        ),
        SpotifyPlaylist(
            "37i9dQZF1DX1lVhptIYRda",
            "Hot Country",
            "Spotify",
            "grit",
            "Straightforward drive for finishing what you started.",
        ),
        SpotifyPlaylist(
            "37i9dQZF1DX4dyzvuaRJ0n",
            "mint",
            "Spotify",
            "momentum",
            "Electronic pulse for time-boxed execution sprints.",
        ),
    ),
    "burnout": (
        SpotifyPlaylist(
            "37i9dQZF1DX4sWSpwq3LiO",
            "Peaceful Piano",
            "Spotify",
            "recover",
            "Downshifts nervous system when capacity is the constraint.",
        ),
        SpotifyPlaylist(
            "37i9dQZF1DWZd79rJ6a7lp",
            "Sleep",
            "Spotify",
            "rest",
            "Restorative listening when Guardian should protect, not push.",
        ),
        SpotifyPlaylist(
            "37i9dQZF1DX6VdMW310YC7",
            "Chill Vibes",
            "Spotify",
            "soft reset",
            "Gentle mix for recovery days without doomscroll residue.",
        ),
        SpotifyPlaylist(
            "37i9dQZF1DWV7EzJMK2FUI",
            "Jazz for Sleep",
            "Spotify",
            "wind down",
            "Soft jazz for evening decompression.",
        ),
    ),
    "knowledge": (
        SpotifyPlaylist(
            "37i9dQZF1DWZeKCadgRdKQ",
            "Deep Focus",
            "Spotify",
            "learn",
            "Study-friendly beds for knowledge acquisition blocks.",
        ),
        SpotifyPlaylist(
            "37i9dQZF1DX8NTLI2TtZa6",
            "Intense Studying",
            "Spotify",
            "absorb",
            "Supports reading / tutorial sessions without lyric hijack.",
        ),
        SpotifyPlaylist(
            "37i9dQZF1DWWQRwui0ExPn",
            "lofi beats",
            "Spotify",
            "retain",
            "Familiar loop that helps encoding new material.",
        ),
        SpotifyPlaylist(
            "37i9dQZF1DX4sWSpwq3LiO",
            "Peaceful Piano",
            "Spotify",
            "reflect",
            "Quiet space after learning to consolidate takeaways.",
        ),
    ),
}

_DEFAULT = _BY_BOTTLENECK["focus"]

# Identity-attribute keywords → preferred playlist themes (overrides pool order).
_ATTRIBUTE_HINTS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("speak", "presentation", "toastmaster", "public", "voice"), "communication"),
    (("focus", "deep work", "attention", "distract"), "focus"),
    (("burnout", "rest", "recover", "overwhelm"), "burnout"),
    (("discipline", "habit", "consistency", "routine"), "discipline"),
    (("confidence", "courage", "visibility"), "confidence"),
    (("learn", "knowledge", "study", "skill"), "knowledge"),
    (("music", "musician", "compose", "guitar", "piano"), "communication"),
)


def _normalize_bottleneck(raw: str | None) -> str:
    key = (raw or "focus").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "focus_drift": "focus",
        "execution": "discipline",
        "consistency": "discipline",
        "accountability": "discipline",
        "networking": "communication",
    }
    key = aliases.get(key, key)
    return key if key in _BY_BOTTLENECK else "focus"


def _persona_bucket(attribute_labels: list[str] | None) -> str | None:
    blob = " ".join(attribute_labels or []).lower()
    if not blob:
        return None
    for keywords, bucket in _ATTRIBUTE_HINTS:
        if any(word in blob for word in keywords):
            return bucket
    return None


def _stable_offset(user_id: str, salt: str, modulus: int) -> int:
    if modulus <= 0:
        return 0
    digest = hashlib.sha256(f"{user_id}:{salt}".encode()).hexdigest()
    return int(digest[:8], 16) % modulus


def select_playlists_for_user(
    user_id: str,
    *,
    bottleneck: str | None,
    attribute_labels: list[str] | None = None,
    count: int = 2,
) -> list[SpotifyPlaylist]:
    """Pick `count` playlists unique to this user + persona."""
    persona = _persona_bucket(attribute_labels)
    primary = _normalize_bottleneck(persona or bottleneck)
    pool = list(_BY_BOTTLENECK.get(primary, _DEFAULT))

    # Blend a second theme so two users with the same bottleneck still diverge.
    secondary_keys = [k for k in _BY_BOTTLENECK if k != primary]
    sec_idx = _stable_offset(user_id, "secondary", len(secondary_keys) or 1)
    if secondary_keys:
        pool.extend(_BY_BOTTLENECK[secondary_keys[sec_idx]][:2])

    # Deduplicate by playlist id while preserving order.
    seen: set[str] = set()
    unique: list[SpotifyPlaylist] = []
    for pl in pool:
        if pl.playlist_id in seen:
            continue
        seen.add(pl.playlist_id)
        unique.append(pl)

    if not unique:
        return []

    start = _stable_offset(user_id, f"playlist:{primary}", len(unique))
    rotated = unique[start:] + unique[:start]
    return rotated[:count]


def playlists_as_feed_items(
    user_id: str,
    *,
    bottleneck: str | None,
    attribute_labels: list[str] | None = None,
    count: int = 2,
) -> list[FeedItem]:
    items: list[FeedItem] = []
    for index, playlist in enumerate(
        select_playlists_for_user(
            user_id,
            bottleneck=bottleneck,
            attribute_labels=attribute_labels,
            count=count,
        )
    ):
        thumbnail = fetch_playlist_thumbnail(playlist.playlist_id)
        items.append(
            FeedItem(
                id=f"spotify-{user_id[:8]}-{playlist.playlist_id}-{index}",
                kind="resource",
                title=playlist.title,
                tag="Spotify",
                url=playlist.url,
                sourceBadge="Curated fallback",
                thumbnailUrl=thumbnail,
                channelTitle=f"{playlist.curator} · {playlist.mood}",
                explanation=StackExplanation(
                    whyThis=playlist.why,
                    whyNow=f"Matched to your {(_normalize_bottleneck(bottleneck))} bottleneck and declared identity.",
                    howReducesGap="Supports the emotional / attentional state needed for the next aligned action.",
                ),
                metadata={
                    "provider": "spotify",
                    "playlist_id": playlist.playlist_id,
                    "mood": playlist.mood,
                    "persona_bottleneck": _normalize_bottleneck(
                        _persona_bucket(attribute_labels) or bottleneck
                    ),
                },
            )
        )
    return items
