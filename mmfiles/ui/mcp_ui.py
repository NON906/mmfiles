import gradio as gr
import sys
import os
import json
import psutil

global_base_path = None

def generate_json_content():
    base_args = None
    try:
        # 現在のプロセスを取得
        parent_process = psutil.Process()

        while True:
            # 親プロセスを取得
            parent_process = psutil.Process(parent_process.ppid())
            check_command = os.path.splitext(os.path.basename(parent_process.exe()))[0]
            if check_command == "uvx" or check_command == "uv":
                cmdline = parent_process.cmdline()
                command = cmdline[0]
                base_args = cmdline[1:]

    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

    if base_args is None:
        # 代わりにsys.orig_argvを使用
        command = os.path.splitext(os.path.basename(sys.orig_argv[0]))[0]
        base_args = sys.orig_argv[1:]

    args = []
    for arg in base_args:
        if arg == "mmfiles":
            args.append("mmfiles-mcp")
            break
        args.append(arg)
    args.append("--path")
    args.append(os.path.abspath(global_base_path))

    json_base = {
        "mcpServers": {
            "mmfiles": {
                "command": command,
                "args": args
            }
        }
    }
    json_with_options_and_envs = {
        "mcpServers": {
            "mmfiles": {
                "command": command,
                "args": [
                    *args,
                    "--disable_text",
                    "--disable_image",
                    "--disable_audio"
                ],
                "env": {
                    "MMFILES_DB_PATH": ".mmfiles.db",
                    "LOAD_IN_4BIT": "1",
                    "DEVICE_MAP": "cuda"
                }
            }
        }
    }

    return json.dumps(json_base, indent=2), json.dumps(json_with_options_and_envs, indent=2)

def mcp_ui_init_inputs(base_path):
    global global_base_path
    if not os.path.isdir(base_path):
        return gr.update(), gr.update()
    global_base_path = base_path

def mcp_ui_init():
    return generate_json_content()

def mcp_ui_base_path_on_changed(base_path):
    global global_base_path
    if not os.path.isdir(base_path):
        return gr.update(), gr.update()
    global_base_path = base_path
    return generate_json_content()

def mcp_ui():
    gr.Markdown(value="""# How to use MCP

To use the features of this repository with MCP, add the following to the corresponding tool's JSON file (e.g., ``claude_desktop_config.json``).""")

    base_code = gr.Code(language="json")

    gr.Markdown(value="""You can change detailed settings using options and environment variables as shown below.""")

    with_options_and_envs_code = gr.Code(language="json")

    gr.Markdown(value="""The available options and environment variables are listed below.

| Option | Details |
| --- | --- |
| ``--path`` (``-p``) | Specifies the path to the directory to be searched.<br>Defaults to the ``files`` folder in the current directory. |
| ``--disable_text`` | Excludes text files from the search. |
| ``--disable_image`` | Excludes image files from the search. |
| ``--disable_audio`` | Excludes audio files from the search. |

| Environment Variable | Details |
| --- | --- |
| ``MMFILES_DB_PATH`` | Specifies the path to the database file that stores information about the files to be searched.<br>Defaults to the ``.mmfiles.db`` file in the current directory. |
| ``LOAD_IN_4BIT`` | Enables/disables 4-bit quantization.<br>Enabled by default. |
| ``DEVICE_MAP`` | Specifies the computation device.<br>Can be one of ``cuda``, ``mps``, or ``cpu``.<br>Defaults to ``cuda``. |
""")

    mcp_ui_outputs = [base_code, with_options_and_envs_code]
    mcp_base_path_on_changed_outputs = [base_code, with_options_and_envs_code]

    return mcp_ui_outputs, mcp_base_path_on_changed_outputs