# Set Dressing (Maya)

Scatters a low-poly glade on a 40x40 ground: pines and broadleaf trees growing in groves, rocks (some in little piles), a dirt path and a pond ringed with stones. Flat colours, faceted look.

With **Keep path and pond clear** on, the path (4 wide, along Z through the middle) and the pond (radius 6 at x=10, z=10) are shown and nothing lands on them; everything keeps 1 unit back from the path's edges. No rock lands within 3 units of a tree, and no two trees stand closer than 2. The same **Seed** with the same settings always gives the same set.

**Maya version:** Maya 2027 (window tested) and Maya 2026 (engine tested). Uses only `maya.cmds`, no plugins.

## Run it
In Maya: **Windows > General Editors > Script Editor**, **Python** tab. Paste these two lines, change the path to the folder you cloned, and press Ctrl+Enter:

```python
import sys; sys.path.insert(0, r"C:\path\to\set-dresser-agent"); sys.modules.pop("set_dressing_ui", None)
import set_dressing_ui; set_dressing_ui.show()
```
The first line also makes Maya forget any copy of the tool it loaded before, so running the lines again always picks up the files in your clone.

To get a shelf button, select the two lines and middle-mouse drag them onto your shelf.

## The window
- **Rocks / Trees**: how many to place.
- **Area**: size of the square they are scattered in (the ground stays 40x40).
- **Clumping**: 0 = trees spread evenly, 1 = trees in tight groves.
- **Keep path and pond clear**: shows the path and pond and keeps everything off them.
- **Seed**: which set you get. Note the number of a set you like. **Random** picks a new seed and scatters.
- **Scatter**: replaces the previous scatter. One Ctrl+Z undoes it.
- **Clear**: deletes `SD_ground_grp`, `SD_path_grp`, `SD_pond_grp`, `SD_rocks_grp` and `SD_trees_grp` only. Your own objects are never touched. The colours (`SD_mat_*` materials) stay in the scene so the next scatter reuses them.

## Files
- `set_dressing.py`: the engine. Settings and colours at the top; `is_allowed()` holds all placement rules; one `make_*()` per thing it makes (ground, path, pond, rock, pine, broadleaf); `scatter()`, `clear()`, `random_seed()`.
- `set_dressing_ui.py`: the window. It only reads its controls and calls the engine.
- `test_set_dressing.py`: checks the engine without Maya's window: `mayapy test_set_dressing.py`.
- `send_to_maya.py`: runs Python in an open Maya through a command port on 7001 (developer helper, not needed to use the tool).
