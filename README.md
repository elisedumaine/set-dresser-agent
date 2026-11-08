# Set Dressing (Maya)

Scatters low-poly rocks and trees on a 40x40 ground plane. With **Keep path and pond clear** on, nothing lands on the path (4 wide, along Z through the middle, plus 1 unit of clearance) or in the pond (radius 6 at x=10, z=10). No rock lands within 3 units of a tree. The same **Seed** with the same settings always gives the same set.

**Maya version:** Maya 2027 (window tested) and Maya 2026 (engine tested). Uses only `maya.cmds`, no plugins.

## Run it
In Maya: **Windows > General Editors > Script Editor**, **Python** tab. Paste these two lines, change the path to the folder you cloned, and press Ctrl+Enter:

```python
import sys; sys.path.insert(0, r"C:\path\to\maya-set-dressing")
import set_dressing_ui; set_dressing_ui.show()
```

To get a shelf button, select the two lines and middle-mouse drag them onto your shelf.

## The window
- **Rocks / Trees**: how many to place.
- **Area**: size of the square they are scattered in (the ground stays 40x40).
- **Seed**: which random set you get. Note the number of a set you like.
- **Keep path and pond clear**: nothing lands on the path or in the pond.
- **Scatter**: replaces the previous scatter. One Ctrl+Z undoes it.
- **Clear**: deletes `SD_ground_grp`, `SD_rocks_grp` and `SD_trees_grp` only. Your own objects are never touched.

## Files
- `set_dressing.py`: the engine. Settings at the top (path width, clearance, pond, rock-tree gap); `is_allowed()` holds all placement rules; one `make_*()` per thing it makes; `scatter()` and `clear()`.
- `set_dressing_ui.py`: the window. It only reads its controls and calls the engine.
- `test_set_dressing.py`: checks the engine without Maya's window: `mayapy test_set_dressing.py`.
- `send_to_maya.py`: runs Python in an open Maya through a command port on 7001 (developer helper, not needed to use the tool).
