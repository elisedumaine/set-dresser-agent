"""Set-dressing engine for Maya: scatters rocks and trees on a 40x40 ground.

No window code here. The window (set_dressing_ui.py) only reads its controls
and calls scatter() or clear().

    import set_dressing
    set_dressing.scatter(rock_count=60, tree_count=40, area=40, keep_clear=True)
    set_dressing.clear()
"""
import math
import random

import maya.cmds as cmds

GROUND_SIZE = 40.0
PATH_HALF_WIDTH = 2.0          # path is 4 wide, along Z, through x = 0
PATH_CLEARANCE = 1.0           # keep everything this far back from the path's edges
POND_CENTER = (10.0, 10.0)     # (x, z)
POND_RADIUS = 6.0
ROCK_TREE_GAP = 3.0            # no rock edge closer than this to a tree trunk
MAX_TRIES = 200                # random spots tried per object before giving up

# One top-level group per kind. Clear deletes these and nothing else.
GROUPS = {
    "ground": "SD_ground_grp",
    "rocks": "SD_rocks_grp",
    "trees": "SD_trees_grp",
}


# ---------------------------------------------------------------- rules

def is_allowed(x, z, keep_clear, margin=0.0, trees=()):
    """True if an object of radius `margin` may stand at (x, z).

    `trees` is a list of (x, z) trunk positions to keep ROCK_TREE_GAP away from
    (given when placing rocks).
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
        if math.hypot(x - tx, z - tz) < ROCK_TREE_GAP + margin:
            return False
    return True


# ---------------------------------------------------------------- makers

def make_ground():
    ground = cmds.polyPlane(name="SD_ground", width=GROUND_SIZE, height=GROUND_SIZE,
                            subdivisionsX=10, subdivisionsY=10, constructionHistory=False)[0]
    return cmds.parent(ground, _group("ground"))[0]


def make_rock(x, z, size):
    rock = cmds.polySphere(name="SD_rock_#", radius=1.0, subdivisionsAxis=7,
                           subdivisionsHeight=5, constructionHistory=False)[0]
    for vtx in cmds.ls(rock + ".vtx[*]", flatten=True):
        cmds.move(random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15),
                  vtx, relative=True)
    cmds.xform(rock,
               translation=(x, size * 0.25, z),
               rotation=(random.uniform(0, 360), random.uniform(0, 360), random.uniform(0, 360)),
               scale=(size * random.uniform(0.9, 1.2), size * random.uniform(0.5, 0.8), size * random.uniform(0.9, 1.2)))
    return cmds.parent(rock, _group("rocks"))[0]


def make_tree(x, z, height):
    trunk_h = height * 0.35
    crown_h = height * 0.75
    trunk = cmds.polyCylinder(radius=height * 0.06, height=trunk_h, subdivisionsAxis=6,
                              constructionHistory=False)[0]
    cmds.move(0, trunk_h / 2.0, 0, trunk)
    crown = cmds.polyCone(radius=height * 0.28, height=crown_h, subdivisionsAxis=7,
                          constructionHistory=False)[0]
    cmds.move(0, trunk_h + crown_h / 2.0 - height * 0.1, 0, crown)
    tree = cmds.polyUnite(trunk, crown, name="SD_tree_#", constructionHistory=False)[0]
    cmds.xform(tree, pivots=(0, 0, 0), worldSpace=True)
    cmds.xform(tree, translation=(x, 0, z), rotation=(0, random.uniform(0, 360), 0))
    return cmds.parent(tree, _group("trees"))[0]


# ---------------------------------------------------------------- actions

def scatter(rock_count, tree_count, area=GROUND_SIZE, keep_clear=True, seed=None):
    """Replace the previous result with a new scatter. One call = one undo.

    Returns {"rocks": placed, "trees": placed, "rocks_wanted": n, "trees_wanted": n}.
    """
    random.seed(seed)
    area = max(1.0, min(float(area), GROUND_SIZE))
    cmds.undoInfo(openChunk=True, chunkName="Set Dressing Scatter")
    try:
        clear()
        make_ground()
        # trees first, so the rocks know where the trees are
        tree_spots = []
        for _ in range(int(tree_count)):
            height = random.uniform(3.0, 6.0)
            spot = _find_spot(area, keep_clear, height * 0.28)
            if spot:
                make_tree(spot[0], spot[1], height)
                tree_spots.append(spot)
        placed_rocks = 0
        for _ in range(int(rock_count)):
            size = random.uniform(0.4, 1.2)
            # 1.5 x size covers the rock's widest point (stretch + bumpy vertices)
            spot = _find_spot(area, keep_clear, size * 1.5, trees=tree_spots)
            if spot:
                make_rock(spot[0], spot[1], size)
                placed_rocks += 1
        placed_trees = len(tree_spots)
        _group("rocks")
        _group("trees")
        cmds.select(clear=True)
    finally:
        cmds.undoInfo(closeChunk=True)
    return {"seed": seed, "rocks": placed_rocks, "trees": placed_trees,
            "rocks_wanted": int(rock_count), "trees_wanted": int(tree_count)}


def clear():
    """Delete the tool's groups (and everything in them). Nothing else is touched."""
    existing = ["|" + name for name in GROUPS.values() if cmds.objExists("|" + name)]
    if existing:
        cmds.delete(existing)
    return len(existing)


# ---------------------------------------------------------------- helpers

def _group(kind):
    path = "|" + GROUPS[kind]
    if not cmds.objExists(path):
        cmds.group(empty=True, world=True, name=GROUPS[kind])
    return path


def _find_spot(area, keep_clear, margin, trees=()):
    half = area / 2.0
    for _ in range(MAX_TRIES):
        x = random.uniform(-half, half)
        z = random.uniform(-half, half)
        if is_allowed(x, z, keep_clear, margin, trees):
            return x, z
    return None
