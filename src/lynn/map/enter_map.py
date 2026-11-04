"""FB engine--LL.bas enter_map: seat Lynn on a map entry.

Lives beside ``change_room`` the way both sit in engine--LL.bas. Host state
(``MapDemo``) is still passed in; room enemy setup and entry-seq promote stay
in demos helpers for now.
"""

from __future__ import annotations

from pathlib import Path

import lynn.events as events
from lynn.constants import TRUE
from lynn.events import bind_hero
from lynn.gfx.image import frame_surfaces
from lynn.hero import place_hero
from lynn.map.loader import load_mapV
from lynn.map.minimap import attach_minimap, visited_bytes
from lynn.paths import resolve_map_path


def apply_enter_visibility(hero, only) -> None:
    """FB change_room case 2: show Lynn unless invisibleEntry is set."""
    if hero is None:
        return
    if only is None or getattr(only, "invisibleEntry", 0) == 0:
        hero.invisible = 0
        return
    only.invisibleEntry = 0
    hero.invisible = 1


def enter_map(
    demo,
    map_name: str,
    entry_i: int,
    load_images: bool | None = None,
    load_tileset: bool = True,
    from_change_room: bool = False,
) -> None:
    """FB enter_map + set_up_room_enemies. Keep the hero; swap the map.

    When ``from_change_room`` is set (FSM case 2), fades and song stay under
    change_room control, entry seq is deferred to case 5, and switch_room is
    left armed until the fade-in finishes.
    """
    from lynn.audio import stop_looping_samples
    from lynn.demos import (
        _maybe_start_entry_seq,
        _start_current_room_song,
        set_up_room_enemies,
    )

    # Title gulls leave looping sea on mixer channels; drop those, keep Lynn's cricket.
    keep = getattr(demo.hero, "playing_handle", None) if demo.hero is not None else None
    stop_looping_samples(keep=keep)
    if load_images is None:
        load_images = demo.load_images != 0
    path = resolve_map_path(map_name)
    game_map = load_mapV(str(path), load_tileset=load_tileset)
    if load_tileset and (game_map.tileset is None or game_map.rooms == 0):
        raise FileNotFoundError(path)
    demo.game_map = game_map
    if demo.palette is not None and not from_change_room:
        from lynn.gfx.palette import reset_palette_ramps

        demo.palette.restore_master()
        reset_palette_ramps()
    demo.tile_surfs = []
    demo._tile_epoch = -1
    if load_tileset and game_map.tileset is not None:
        demo.tile_surfs = frame_surfaces(game_map.tileset, demo.palette)
        if demo.palette is not None:
            demo._tile_epoch = int(demo.palette.epoch)
    demo.para_cache = {}
    demo.objects_by_room = [[] for _ in game_map.room]
    demo.load_images = TRUE if load_images else 0
    demo.load_tileset = TRUE if load_tileset else 0
    for i in range(game_map.rooms):
        set_up_room_enemies(demo, i, load_images=load_images)
    if demo.hero is not None:
        demo.hero_room = place_hero(demo.hero, game_map, entry_i)
        if not from_change_room:
            demo.hero.switch_room = -1
            demo.hero.to_map = ""
        # FB enter_map only seats coords/direction/room/entry seq. It does not
        # reset current_anim — title Begin sets active_anim_1 (unconscious)
        # before change_map, and that pose must survive the fade FSM swap.
        bind_hero(demo.hero)
        if not from_change_room:
            apply_enter_visibility(demo.hero, demo.hero_only)
        if 0 <= demo.hero_room < len(game_map.room):
            events.dark = game_map.room[demo.hero_room].dark
            from lynn.map.landing import resolve_ignia_mace_return

            resolve_ignia_mace_return(
                demo.hero,
                game_map,
                entry_i,
                demo.objects_by_room[demo.hero_room],
            )
    events.load_images = TRUE if load_images else 0
    events.do_chap = 0
    if not from_change_room:
        events.fade_black = 0
        events.fade_white = 0
        events.fade_red = 0
        events.color_mode = 0
    events.palette = demo.palette
    events.current_cam = None
    events.map_filename = Path(path).name
    events.hero_room = demo.hero_room
    if from_change_room:
        # FB enter_map does not touch do_hud. change_room case 2 only forces
        # HUD on for isLoading; entry/room seqs clear it when they promote.
        # Clearing here left Arx (entry 0, no seq) HUD-dark after the hop.
        demo.seq = None
    else:
        _maybe_start_entry_seq(demo, entry_i)
        _start_current_room_song(demo)
    # FB enter_map restores hero_only.roomVisited onto the new .mni. That pointer
    # is only filled on save-load; mid-game map hops (Gelidus → Ice Field for the
    # engraved key) destroyed the old minimap with no stash. Keep visits across a
    # hop that has no .mni, and re-apply when the matching dungeon is entered again.
    visited = events.pending_visited
    events.pending_visited = None
    if visited is None and demo.minimap is not None:
        visited = visited_bytes(demo.minimap)
    attach_minimap(demo, visited)
    if demo.minimap is None and visited is not None:
        events.pending_visited = visited
    if demo.palette is not None:
        demo.pal_epoch = demo.palette.epoch
