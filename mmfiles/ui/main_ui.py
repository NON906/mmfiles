import gradio as gr
import argparse
import os

from .files_ui import files_ui, files_ui_init_inputs, files_ui_init, files_ui_base_path_on_changed
from .search_ui import search_ui, search_ui_init_inputs, search_ui_init, search_ui_base_path_on_changed
from .mcp_ui import mcp_ui, mcp_ui_init_inputs, mcp_ui_init, mcp_ui_base_path_on_changed
from .. import search

def base_dir_changed(path):
    if not os.path.isdir(path):
        print("Incorrect path.")
        return
    search.change_base_dir(path)
    search.update()
    search.files_init()

def main_ui():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help="Default directory path.")
    parser.add_argument("--disable_auto_launch", action='store_true', help="Disable auto launch a browser.")
    args = parser.parse_args()

    base_path = args.path
    if base_path is None:
        base_path = os.path.abspath("files")
        os.makedirs(base_path, exist_ok=True)

    base_dir_changed(base_path)

    with gr.Blocks() as demo:
        with gr.Row(equal_height=True):
            with gr.Column(scale=4):
                base_path_textbox = gr.Textbox(label="Directory path / ディレクトリパス")
            with gr.Column(scale=1):
                base_path_button = gr.Button(value="Change / 変更")
        with gr.Row():
            with gr.Tab("Files"):
                files_ui_outputs, files_ui_base_path_on_changed_outputs = files_ui()
            with gr.Tab("Search"):
                search_ui_outputs, search_ui_base_path_on_changed_outputs = search_ui()
            with gr.Tab("MCP"):
                mcp_ui_outputs, mcp_ui_base_path_on_changed_outputs = mcp_ui()
            #with gr.Tab("Chat"):
            #    pass

        files_ui_init_inputs(base_path)
        search_ui_init_inputs(base_path)
        mcp_ui_init_inputs(base_path)

        base_path_button.click(
            base_dir_changed,
            inputs=[base_path_textbox, ]
        ).then(
            files_ui_base_path_on_changed,
            inputs=[base_path_textbox, ],
            outputs=files_ui_base_path_on_changed_outputs
        ).then(
            search_ui_base_path_on_changed,
            inputs=[base_path_textbox, ],
            outputs=search_ui_base_path_on_changed_outputs
        ).then(
            mcp_ui_base_path_on_changed,
            inputs=[base_path_textbox, ],
            outputs=mcp_ui_base_path_on_changed_outputs
        )

        demo.load(
            files_ui_init,
            outputs=files_ui_outputs
        ).then(
            search_ui_init,
            outputs=search_ui_outputs
        ).then(
            mcp_ui_init,
            outputs=mcp_ui_outputs
        ).then(
            lambda: base_path,
            outputs=[base_path_textbox, ]
        )

    demo.launch(inbrowser=not args.disable_auto_launch)