from .mcp import mcp_server_main

def main_mcp():
    mcp = mcp_server_main()
    mcp.run()