"""Set Dressing window for Maya. Reads its controls and calls set_dressing.

    import set_dressing_ui
    set_dressing_ui.show()
"""
import maya.cmds as cmds

import set_dressing

WINDOW = "setDressingWindow"


def show():
    if cmds.window(WINDOW, exists=True):
        cmds.deleteUI(WINDOW)
    cmds.window(WINDOW, title="Set Dressing", widthHeight=(380, 240), sizeable=False)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=6, columnAttach=("both", 8))
    cmds.separator(height=6, style="none")
    cmds.intSliderGrp("sdRocks", label="Rocks", field=True, minValue=0, maxValue=300,
                      fieldMaxValue=1000, value=60, columnWidth3=(60, 50, 240))
    cmds.intSliderGrp("sdTrees", label="Trees", field=True, minValue=0, maxValue=200,
                      fieldMaxValue=1000, value=40, columnWidth3=(60, 50, 240))
    cmds.floatSliderGrp("sdArea", label="Area", field=True, minValue=5, maxValue=40,
                        value=40, precision=1, columnWidth3=(60, 50, 240))
    cmds.intSliderGrp("sdSeed", label="Seed", field=True, minValue=0, maxValue=100,
                      fieldMaxValue=99999, value=1, columnWidth3=(60, 50, 240))
    cmds.checkBox("sdKeepClear", label="Keep path and pond clear", value=True)
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(180, 180), adjustableColumn=1)
    cmds.button(label="Scatter", height=32, command=_on_scatter)
    cmds.button(label="Clear", height=32, command=_on_clear)
    cmds.setParent("..")
    cmds.text("sdStatus", label="", align="left")
    cmds.showWindow(WINDOW)


def _on_scatter(*_):
    result = set_dressing.scatter(
        rock_count=cmds.intSliderGrp("sdRocks", query=True, value=True),
        tree_count=cmds.intSliderGrp("sdTrees", query=True, value=True),
        area=cmds.floatSliderGrp("sdArea", query=True, value=True),
        keep_clear=cmds.checkBox("sdKeepClear", query=True, value=True),
        seed=cmds.intSliderGrp("sdSeed", query=True, value=True),
    )
    message = "Seed %d: placed %d rocks and %d trees." % (result["seed"], result["rocks"], result["trees"])
    if result["rocks"] < result["rocks_wanted"] or result["trees"] < result["trees_wanted"]:
        message += " Not enough room for all of them: try a bigger area."
    cmds.text("sdStatus", edit=True, label=message)


def _on_clear(*_):
    set_dressing.clear()
    cmds.text("sdStatus", edit=True, label="Cleared.")
