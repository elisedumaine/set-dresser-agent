"""Checks the set-dressing engine without the Maya window.

    "C:\\Program Files\\Autodesk\\Maya2027\\bin\\mayapy.exe" Tools/maya/test_set_dressing.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds

import set_dressing as sd

cmds.undoInfo(state=True, infinity=True)


def children(group):
    return cmds.listRelatives("|" + group, children=True, fullPath=True) or []


def footprint_ok(obj):
    # every vertex at ground level (y < 0.5) must obey the rules (no margin)
    for x, y, z in _points(obj):
        if y < 0.5 and not sd.is_allowed(x, z, keep_clear=True):
            return False
    return True


def _points(obj):
    flat = cmds.xform(obj + ".vtx[*]", query=True, translation=True, worldSpace=True)
    return [flat[i:i + 3] for i in range(0, len(flat), 3)]


# rules
assert not sd.is_allowed(0, 15, True)            # on the path
assert not sd.is_allowed(2.5, 15, True)          # off the path but inside the clearance
assert sd.is_allowed(3.1, -15, True)             # just past the clearance
assert not sd.is_allowed(10, 10, True)           # in the pond
assert not sd.is_allowed(25, 0, True)            # off the ground
assert sd.is_allowed(-10, -10, True)
assert sd.is_allowed(0, 15, False)               # path allowed when unchecked

# a user object that Clear must never touch
cmds.polyCube(name="userCube")

result = sd.scatter(rock_count=60, tree_count=40, area=40, keep_clear=True, seed=1)
print("scatter:", result)
rocks, trees = children(sd.GROUPS["rocks"]), children(sd.GROUPS["trees"])
assert len(rocks) == result["rocks"] and len(trees) == result["trees"]
assert len(children(sd.GROUPS["ground"])) == 1
bad = [o for o in rocks + trees if not footprint_ok(o)]
assert not bad, "objects on path/pond: %s" % bad

# no part of any rock within ROCK_TREE_GAP of a tree trunk
trunks = [cmds.xform(t, query=True, translation=True, worldSpace=True) for t in trees]
closest = min(math.hypot(px - tx, pz - tz)
              for r in rocks for px, _, pz in _points(r)
              for tx, _, tz in trunks)
print("closest rock to a trunk: %.2f (gap %.1f)" % (closest, sd.ROCK_TREE_GAP))
assert closest >= sd.ROCK_TREE_GAP, "a rock is too close to a tree"
assert not sd.is_allowed(-10, -10, True, trees=[(-10, -12)])     # 2 from a trunk
assert sd.is_allowed(-10, -10, True, trees=[(-10, -14)])         # 4 from a trunk

# one scatter = one undo
cmds.undo()
assert not any(cmds.objExists("|" + g) for g in sd.GROUPS.values()), "undo left objects"
assert cmds.objExists("userCube")
cmds.redo()
assert len(children(sd.GROUPS["rocks"])) == result["rocks"]

# re-scatter replaces, does not pile up
sd.scatter(rock_count=10, tree_count=5, area=40, keep_clear=True, seed=2)
assert len(children(sd.GROUPS["rocks"])) == 10

# same seed + same settings = same set, every time
def snapshot():
    objs = children(sd.GROUPS["rocks"]) + children(sd.GROUPS["trees"])
    return [[round(v, 6) for v in cmds.xform(o + ".vtx[*]", query=True, translation=True, worldSpace=True)]
            for o in objs]

sd.scatter(rock_count=60, tree_count=40, area=30, keep_clear=True, seed=12)
first = snapshot()
sd.scatter(rock_count=5, tree_count=5, area=40, keep_clear=False, seed=99)   # something else in between
sd.scatter(rock_count=60, tree_count=40, area=30, keep_clear=True, seed=12)
assert snapshot() == first, "seed 12 did not give the same set"
sd.scatter(rock_count=60, tree_count=40, area=30, keep_clear=True, seed=13)
assert snapshot() != first, "seed 13 gave the same set as seed 12"

# clear deletes only the tool's groups
sd.clear()
assert not any(cmds.objExists("|" + g) for g in sd.GROUPS.values())
assert cmds.objExists("userCube")

print("ALL TESTS PASSED")
maya.standalone.uninitialize()
