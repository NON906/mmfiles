from .mcp import mcp_server_main
from .ui.main_ui import main_ui

def main_mcp():
    mcp = mcp_server_main()
    mcp.run()

def main_app():
    main_ui()
