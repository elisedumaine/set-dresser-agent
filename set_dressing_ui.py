"""Set Dressing window for Maya. Reads its controls and calls set_dressing.

    import set_dressing_ui
    set_dressing_ui.show()
"""
import importlib
import os
import sys

import maya.cmds as cmds

# Always use the engine that sits next to this window. If Maya already loaded
# another copy of set_dressing (an older clone, another folder), drop it.
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
_old = sys.modules.get("set_dressing")
if _old and os.path.dirname(os.path.abspath(getattr(_old, "__file__", "") or "")) != HERE:
    del sys.modules["set_dressing"]

import set_dressing  # noqa: E402
importlib.reload(set_dressing)

WINDOW = "setDressingWindow"
COLUMNS = (70, 55, 230)


def show():
    if cmds.window(WINDOW, exists=True):
        cmds.deleteUI(WINDOW)
    cmds.window(WINDOW, title="Set Dressing", sizeable=False, resizeToFitChildren=True)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    cmds.frameLayout(label="Amounts", marginWidth=8, marginHeight=6)
    cmds.intSliderGrp("sdRocks", label="Rocks", field=True, minValue=0, maxValue=200,
                      fieldMaxValue=1000, value=50, columnWidth3=COLUMNS)
    cmds.intSliderGrp("sdTrees", label="Trees", field=True, minValue=0, maxValue=150,
                      fieldMaxValue=1000, value=40, columnWidth3=COLUMNS)
    cmds.setParent("..")

    cmds.frameLayout(label="Layout", marginWidth=8, marginHeight=6)
    cmds.floatSliderGrp("sdArea", label="Area", field=True, minValue=5, maxValue=40,
                        value=40, precision=1, columnWidth3=COLUMNS)
    cmds.floatSliderGrp("sdClumping", label="Clumping", field=True, minValue=0, maxValue=1,
                        value=0.6, precision=2, columnWidth3=COLUMNS,
                        annotation="0 = trees spread evenly, 1 = trees in groves")
    cmds.checkBox("sdKeepClear", label="Keep path and pond clear (and show them)", value=True)
    cmds.setParent("..")

    cmds.frameLayout(label="Seed", marginWidth=8, marginHeight=6)
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(300, 60), adjustableColumn=1)
    cmds.intSliderGrp("sdSeed", label="Seed", field=True, minValue=0, maxValue=9999,
                      value=12, columnWidth3=(70, 55, 170),
                      annotation="Same seed + same settings = same set")
    cmds.button(label="Random", command=_on_random)
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.rowLayout(numberOfColumns=2, columnWidth2=(180, 180), adjustableColumn=1,
                   columnAttach2=("both", "both"), columnOffset2=(8, 8))
    cmds.button(label="Scatter", height=36, backgroundColor=(0.33, 0.52, 0.30), command=_on_scatter)
    cmds.button(label="Clear", height=36, command=_on_clear)
    cmds.setParent("..")
    cmds.text("sdStatus", label="Pick your settings, then Scatter.", align="left")
    cmds.showWindow(WINDOW)


def _on_scatter(*_):
    result = set_dressing.scatter(
        rock_count=cmds.intSliderGrp("sdRocks", query=True, value=True),
        tree_count=cmds.intSliderGrp("sdTrees", query=True, value=True),
        area=cmds.floatSliderGrp("sdArea", query=True, value=True),
        keep_clear=cmds.checkBox("sdKeepClear", query=True, value=True),
        clumping=cmds.floatSliderGrp("sdClumping", query=True, value=True),
        seed=cmds.intSliderGrp("sdSeed", query=True, value=True),
    )
    message = "  Seed %d: %d trees (%d pines, %d broadleaf), %d rocks." % (
        result["seed"], result["trees"], result["pines"], result["broadleaves"], result["rocks"])
    if result["rocks"] < result["rocks_wanted"] or result["trees"] < result["trees_wanted"]:
        message += " Not enough room for all: try a bigger area or fewer trees."
    cmds.text("sdStatus", edit=True, label=message)


def _on_random(*_):
    cmds.intSliderGrp("sdSeed", edit=True, value=set_dressing.random_seed())
    _on_scatter()


def _on_clear(*_):
    set_dressing.clear()
    cmds.text("sdStatus", edit=True, label="  Cleared.")
