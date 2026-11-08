# Set Dresser (Maya)

Scatters rocks and trees across a 40x40 ground plane. With **Keep path and pond clear** on, nothing lands on the path (4 wide, along Z through the middle, with 1 unit of clearance) or in the round pond (radius 6 at x=10, z=10). No rock lands within 3 units of a tree. A window with sliders for rock count, tree count, area and seed, a **Scatter** button (one Ctrl+Z undoes it) and a **Clear** button (deletes only the tool's groups). The same seed with the same settings always gives the same set.

## Run it
In Maya's Script Editor (**Python** tab), change the path to the folder you cloned, then press Ctrl+Enter:

```python
import sys; sys.path.insert(0, r"C:\path\to\set-dresser-agent")
import set_dressing_ui; set_dressing_ui.show()
```

## Maya version
Maya 2027 (also runs in Maya 2026).
