"""FB headers/ll/map_structures.bi + sequence blobs we must parse to reach tiles."""

from __future__ import annotations

from dataclasses import dataclass, field

from lynn.gfx.image import LLSystem_ImageHeader


@dataclass
class CommandData:
    active_ent: int = 0
    ent_state: int = 0
    hold_state: int = 0
    text: str = ""
    walk_speed: float = 0.0
    dest_y: int = 0
    dest_x: int = 0
    abs_x: int = 0
    abs_y: int = 0
    mod_y: int = 0
    mod_x: int = 0
    to_map: str = ""
    to_entry: int = 0
    jump_count: int = 0
    water_align: int = 0
    chap: int = 0
    carries_all: int = 0
    nocam: int = 0
    modify_direction: int = 0
    seq_pause: int = 0
    reserved_3: int = 0
    reserved_4: int = 0
    free_to_move: int = 0
    display_hud: int = 0
    fadeTime: float = 0.0
    reserved_9: int = 0
    reserved_10: int = 0


@dataclass
class CommandType:
    ents: int = 0
    ent: list[CommandData] = field(default_factory=list)


@dataclass
class SequenceType:
    ents: int = 0
    ent_code: list[int] = field(default_factory=list)
    commands: int = 0
    Command: list[CommandType] = field(default_factory=list)
    seq_type: str = ""
    seq_index: int = 0


@dataclass
class SpawnPair:
    code_index: int = 0
    code_state: int = 0


@dataclass
class ConditionalSpawn:
    wait_n: int = 0
    wait_spawn: list[SpawnPair] = field(default_factory=list)
    kill_n: int = 0
    kill_spawn: list[SpawnPair] = field(default_factory=list)
    active_n: int = 0
    active_spawn: list[SpawnPair] = field(default_factory=list)


@dataclass
class MapEnemyStub:
    """Instance fields stored in the map; XML object body is loaded later."""

    x_origin: int = 0
    y_origin: int = 0
    id: str = ""
    direction: int = 0
    seq_here: int = 0
    spawn_h: int = 0
    is_h_set: int = 0
    chap: int = 0
    spawn_d: int = 0
    is_d_set: int = 0
    reserved_5: int = 0
    seq: list[SequenceType] = field(default_factory=list)
    spawn_cond: int = 0
    spawn_info: ConditionalSpawn | None = None


@dataclass
class TeleportType:
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0
    to_room: int = 0
    to_map: str = ""
    dx: int = 0
    dy: int = 0
    dd: int = 0
    to_song: int = 0
    reserved: list[int] = field(default_factory=list)


@dataclass
class RoomType:
    x: int = 0
    y: int = 0
    parallax: int = 0
    para_filename: str = ""
    para_img: LLSystem_ImageHeader | None = None
    dark: int = 0
    teleports: int = 0
    teleport: list[TeleportType] = field(default_factory=list)
    song: int = 0
    song_changes: int = 0
    changes_to: int = 0
    reserved: list[int] = field(default_factory=list)
    seq_here: int = 0
    seq: list[SequenceType] = field(default_factory=list)
    enemies: int = 0
    enemy: list[MapEnemyStub] = field(default_factory=list)
    room_elem: int = 0
    layout: list[list[int]] = field(default_factory=list)


@dataclass
class MapEntryType:
    x: int = 0
    y: int = 0
    room: int = 0
    direction: int = 0
    seq_here: int = 0
    reserved: bytes = b""
    seq: list[SequenceType] = field(default_factory=list)


@dataclass
class MapType:
    filename: str = ""
    entries: int = 0
    entry: list[MapEntryType] = field(default_factory=list)
    rooms: int = 0
    room: list[RoomType] = field(default_factory=list)
    tileset_filename: str = ""
    tileset: LLSystem_ImageHeader | None = None
    isDungeon: int = 0
    dungeonName: str = ""
    bytes_remaining: int = 0
    bytes_total: int = 0
