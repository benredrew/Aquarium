"""Run OCPViewer with its Tools and Info panels initially collapsed."""

from ocp_vscode import standalone
from ocp_vscode.__main__ import main

# Use the viewer's public panel controls after its initial scene is created.
# Keep these defaults outside the installed package so upgrades preserve them.
standalone.INIT = '''onload="showViewer(); window.viewer.showToolsPanel(false); window.viewer.showInfoPanel(false);"'''

if __name__ == "__main__":
    main()
