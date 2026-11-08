"""Set-dressing engine for Maya: a low-poly glade of trees and rocks on a 40x40 ground.

No window code here. The window (set_dressing_ui.py) only reads its controls
and calls scatter(), clear() or random_seed().

    import set_dressing
    set_dressing.scatter(rock_count=50, tree_count=40, area=40, keep_clear=True, clumping=0.6, seed=12)
    set_dressing.clear()
"""
import math
import random

import maya.cmds as cmds

# ---------------------------------------------------------------- settings

GROUND_SIZE = 40.0
PATH_HALF_WIDTH = 2.0          # path is 4 wide, along Z, through x = 0
PATH_CLEARANCE = 1.0           # keep everything this far back from the path's edges
POND_CENTER = (10.0, 10.0)     # (x, z)
POND_RADIUS = 6.0
ROCK_TREE_GAP = 3.0            # no rock edge closer than this to a tree trunk
TREE_SPACING = 2.0             # no two tree trunks closer than this
MAX_TRIES = 200                # random spots tried per object before giving up

PINE_SHARE = 0.55              # share of trees that are pines (the rest are broadleaf)
TREES_PER_GROVE = 8            # one grove centre for every 8 trees
GROVE_SPREAD = 3.0             # how far trees stray from their grove centre
ROCK_PILE_CHANCE = 0.3         # chance a rock gets 1-2 smaller rocks beside it
ROCK_REACH = 1.6               # a rock's widest point, as a multiple of its size

# Flat colours (RGB 0-1), one lambert material each, named SD_mat_<key>.
PALETTE = {
    "ground": (0.38, 0.58, 0.27),
    "path": (0.78, 0.66, 0.46),
    "water": (0.22, 0.52, 0.78),
    "rock_light": (0.64, 0.62, 0.58),
    "rock_mid": (0.50, 0.50, 0.48),
    "rock_dark": (0.38, 0.40, 0.42),
    "trunk": (0.38, 0.25, 0.15),
    "pine_dark": (0.10, 0.33, 0.20),
    "pine_light": (0.16, 0.43, 0.25),
    "leaf_green": (0.36, 0.60, 0.20),
    "leaf_lime": (0.52, 0.70, 0.24),
    "leaf_autumn": (0.88, 0.56, 0.18),
}

# One top-level group per kind. Clear deletes these and nothing else.
GROUPS = {
    "ground": "SD_ground_grp",
    "path": "SD_path_grp",
    "pond": "SD_pond_grp",
    "rocks": "SD_rocks_grp",
    "trees": "SD_trees_grp",
}


# ---------------------------------------------------------------- rules

def is_allowed(x, z, keep_clear, margin=0.0, trees=(), tree_spacing=False):
    """True if an object of radius `margin` may stand at (x, z).

    `trees` is a list of (x, z) trunk positions already placed. A rock keeps
    ROCK_TREE_GAP from them; a tree (tree_spacing=True) keeps TREE_SPACING
    between trunks instead.
    """
    half = GROUND_SIZE / 2.0 - margin
    if abs(x) > half or abs(z) > half:
        return False
    if keep_clear:
        if abs(x) < PATH_HALF_WIDTH + PATH_CLEARANCE + margin:
            return False
        if math.hypot(x - POND_CENTER[0], z - POND_CENTER[1]) < POND_RADIUS + margin:
            return False
    for tx, tz in trees:
        if tree_spacing:
            if math.hypot(x - tx, z - tz) < TREE_SPACING:
                return False
        elif math.hypot(x - tx, z - tz) < ROCK_TREE_GAP + margin:
            return False
    return True


# ---------------------------------------------------------------- makers

def make_ground():
    ground = cmds.polyPlane(name="SD_ground", width=GROUND_SIZE, height=GROUND_SIZE,
                            subdivisionsX=20, subdivisionsY=20, constructionHistory=False)[0]
    _paint(ground, "ground")
    return cmds.parent(ground, _group("ground"))[0]


def make_path():
    path = cmds.polyPlane(name="SD_path", width=PATH_HALF_WIDTH * 2, height=GROUND_SIZE,
                          subdivisionsX=1, subdivisionsY=20, constructionHistory=False)[0]
    cmds.move(0, 0.02, 0, path)
    _paint(path, "path")
    return cmds.parent(path, _group("path"))[0]


def make_pond():
    """Water disc ringed with small stones, all inside POND_RADIUS."""
    cx, cz = POND_CENTER
    water = cmds.polyCylinder(name="SD_pond_water", radius=POND_RADIUS - 0.8, height=0.06,
                              subdivisionsAxis=18, constructionHistory=False)[0]
    cmds.move(cx, 0.03, cz, water)
    _paint(water, "water")
    parts = [water]
    stones = 16
    for i in range(stones):
        angle = (i + random.uniform(-0.3, 0.3)) * 2 * math.pi / stones
        size = random.uniform(0.3, 0.45)
        stone = _rock_mesh("SD_pond_stone_#", size, random.choice(["rock_light", "rock_mid"]))
        r = POND_RADIUS - 0.75
        cmds.move(cx + r * math.cos(angle), size * 0.15, cz + r * math.sin(angle), stone)
        parts.append(stone)
    cmds.parent(parts, _group("pond"))
    return _group("pond")


def make_rock(x, z, size):
    rock = _rock_mesh("SD_rock_#", size, random.choice(["rock_light", "rock_mid", "rock_dark"]))
    cmds.move(x, size * 0.15, z, rock)
    return cmds.parent(rock, _group("rocks"))[0]


def make_pine(x, z, height):
    """Trunk + three stacked cones."""
    trunk_h = height * 0.25
    parts = [_trunk(height * 0.05, trunk_h)]
    colour = random.choice(["pine_dark", "pine_light"])
    for tier in range(3):
        cone_h = height * (0.42 - tier * 0.06)
        cone = cmds.polyCone(radius=height * (0.30 - tier * 0.07), height=cone_h,
                             subdivisionsAxis=7, constructionHistory=False)[0]
        cmds.move(0, trunk_h * 0.8 + tier * height * 0.22 + cone_h / 2.0, 0, cone)
        cmds.rotate(0, random.uniform(0, 360), 0, cone)
        _paint(cone, colour)
        parts.append(cone)
    return _place_tree(cmds.group(parts, name="SD_pine_#"), x, z)


def make_broadleaf(x, z, height):
    """Trunk + a big faceted crown and a smaller blob beside it."""
    trunk_h = height * 0.45
    parts = [_trunk(height * 0.06, trunk_h)]
    colour = "leaf_autumn" if random.random() < 0.12 else random.choice(["leaf_green", "leaf_lime"])
    crown_r = height * 0.30
    crown = _blob("SD_crown", crown_r, colour)
    cmds.move(0, trunk_h + crown_r * 0.6, 0, crown)
    angle = random.uniform(0, 2 * math.pi)
    side = _blob("SD_crown", crown_r * 0.65, colour)
    cmds.move(math.cos(angle) * crown_r * 0.6, trunk_h + crown_r * 0.3, math.sin(angle) * crown_r * 0.6, side)
    parts += [crown, side]
    return _place_tree(cmds.group(parts, name="SD_broadleaf_#"), x, z)


# ---------------------------------------------------------------- actions

def scatter(rock_count, tree_count, area=GROUND_SIZE, keep_clear=True, clumping=0.6, seed=None):
    """Replace the previous result with a new scatter. One call = one undo.

    Same seed + same settings = same set. Returns what was placed.
    """
    random.seed(seed)
    area = max(1.0, min(float(area), GROUND_SIZE))
    cmds.undoInfo(openChunk=True, chunkName="Set Dressing Scatter")
    try:
        clear()
        make_ground()
        if keep_clear:
            make_path()
            make_pond()

        # trees first, in groves, so the rocks know where the trees are
        groves = [spot for spot in (_find_spot(area, keep_clear, 0.0)
                                    for _ in range(max(1, round(tree_count / TREES_PER_GROVE)))) if spot]
        tree_spots, pines = [], 0
        for _ in range(int(tree_count)):
            if random.random() < PINE_SHARE:
                maker, height = make_pine, random.uniform(3.5, 6.5)
                reach = height * 0.35
            else:
                maker, height = make_broadleaf, random.uniform(3.0, 5.0)
                reach = height * 0.50
            spot = _find_spot(area, keep_clear, reach, trees=tree_spots, tree_spacing=True,
                              groves=groves, clumping=clumping)
            if spot:
                maker(spot[0], spot[1], height)
                tree_spots.append(spot)
                pines += maker is make_pine

        # rocks, some in little piles
        placed_rocks = 0
        while placed_rocks < int(rock_count):
            size = random.uniform(0.4, 1.2)
            spot = _find_spot(area, keep_clear, size * ROCK_REACH, trees=tree_spots)
            if not spot:
                break
            make_rock(spot[0], spot[1], size)
            placed_rocks += 1
            if random.random() < ROCK_PILE_CHANCE:
                for _ in range(random.randint(1, 2)):
                    if placed_rocks >= int(rock_count):
                        break
                    small = size * random.uniform(0.4, 0.6)
                    angle = random.uniform(0, 2 * math.pi)
                    dist = size * 1.2 + small
                    nx, nz = spot[0] + math.cos(angle) * dist, spot[1] + math.sin(angle) * dist
                    if is_allowed(nx, nz, keep_clear, small * ROCK_REACH, tree_spots):
                        make_rock(nx, nz, small)
                        placed_rocks += 1

        _group("rocks")
        _group("trees")
        cmds.select(clear=True)
    finally:
        cmds.undoInfo(closeChunk=True)
    return {"seed": seed, "rocks": placed_rocks, "trees": len(tree_spots),
            "pines": pines, "broadleaves": len(tree_spots) - pines,
            "rocks_wanted": int(rock_count), "trees_wanted": int(tree_count)}


def clear():
    """Delete the tool's groups (and everything in them). Nothing else is touched."""
    existing = ["|" + name for name in GROUPS.values() if cmds.objExists("|" + name)]
    if existing:
        cmds.delete(existing)
    return len(existing)


def random_seed():
    """A fresh seed number, not tied to the current set."""
    return random.SystemRandom().randint(0, 9999)


# ---------------------------------------------------------------- helpers

def _group(kind):
    path = "|" + GROUPS[kind]
    if not cmds.objExists(path):
        cmds.group(empty=True, world=True, name=GROUPS[kind])
    return path


def _find_spot(area, keep_clear, margin, trees=(), tree_spacing=False, groves=(), clumping=0.0):
    half = area / 2.0
    for _ in range(MAX_TRIES):
        if groves and random.random() < clumping:
            gx, gz = random.choice(groves)
            x, z = random.gauss(gx, GROVE_SPREAD), random.gauss(gz, GROVE_SPREAD)
            if abs(x) > half or abs(z) > half:
                continue
        else:
            x, z = random.uniform(-half, half), random.uniform(-half, half)
        if is_allowed(x, z, keep_clear, margin, trees, tree_spacing):
            return x, z
    return None


def _material(key):
    """Shading group for a palette colour, made once and reused."""
    shader = "SD_mat_" + key
    if not cmds.objExists(shader):
        cmds.shadingNode("lambert", asShader=True, name=shader)
        cmds.setAttr(shader + ".color", *PALETTE[key], type="double3")
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shader + "SG")
        cmds.connectAttr(shader + ".outColor", sg + ".surfaceShader", force=True)
    return shader + "SG"


def _paint(obj, key):
    cmds.sets(obj, edit=True, forceElement=_material(key))
    cmds.polySoftEdge(obj, angle=0, constructionHistory=False)   # hard edges = faceted look


def _rock_mesh(name, size, colour):
    """A lumpy rock with a flat bottom, sitting on y = 0 (before being moved)."""
    rock = cmds.polySphere(name=name, radius=1.0, subdivisionsAxis=6, subdivisionsHeight=4,
                           constructionHistory=False)[0]
    for i in range(cmds.polyEvaluate(rock, vertex=True)):
        vtx = "%s.vtx[%d]" % (rock, i)
        x, y, z = cmds.pointPosition(vtx, local=True)
        cmds.xform(vtx, objectSpace=True, translation=(
            x + random.uniform(-0.2, 0.2),
            max(y + random.uniform(-0.2, 0.2), -0.35),
            z + random.uniform(-0.2, 0.2)))
    cmds.xform(rock, rotation=(0, random.uniform(0, 360), 0),
               scale=(size * random.uniform(0.9, 1.2), size * random.uniform(0.55, 0.8),
                      size * random.uniform(0.9, 1.2)))
    _paint(rock, colour)
    return rock


def _blob(name, radius, colour):
    blob = cmds.polySphere(name=name + "_#", radius=radius, subdivisionsAxis=7, subdivisionsHeight=5,
                           constructionHistory=False)[0]
    for i in range(cmds.polyEvaluate(blob, vertex=True)):
        cmds.move(*[random.uniform(-0.12, 0.12) * radius for _ in range(3)],
                  "%s.vtx[%d]" % (blob, i), relative=True)
    cmds.scale(1, 0.85, 1, blob)
    _paint(blob, colour)
    return blob


def _trunk(radius, height):
    trunk = cmds.polyCylinder(name="SD_trunk_#", radius=radius, height=height, subdivisionsAxis=6,
                              constructionHistory=False)[0]
    cmds.move(0, height / 2.0, 0, trunk)
    _paint(trunk, "trunk")
    return trunk


def _place_tree(tree, x, z):
    """Stand the tree at (x, z) with a random turn and a slight lean, pivot at its base."""
    cmds.xform(tree, pivots=(0, 0, 0), worldSpace=True)
    cmds.xform(tree, translation=(x, 0, z),
               rotation=(random.uniform(-4, 4), random.uniform(0, 360), random.uniform(-4, 4)))
    return cmds.parent(tree, _group("trees"))[0]
