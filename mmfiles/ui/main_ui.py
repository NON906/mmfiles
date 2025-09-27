import gradio as gr
import argparse

from .files_ui import files_ui, files_ui_init_inputs, files_ui_init, files_ui_base_path_on_changed
from .search_ui import search_ui, search_ui_init_inputs, search_ui_init, search_ui_base_path_on_changed
from .. import search

def base_dir_changed(path):
    search.change_base_dir(path)
    search.update()
    search.files_init()

def main_ui():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", default="files", help="Default directory path.")
    parser.add_argument("--disable_auto_launch", action='store_true', help="Disable auto launch a browser.")
    args = parser.parse_args()

    base_dir_changed(args.path)

    with gr.Blocks() as demo:
        with gr.Row():
            base_path_textbox = gr.Textbox(label="Directory path / ディレクトリパス")
        with gr.Row():
            with gr.Tab("Files"):
                files_ui_outputs, files_ui_base_path_on_changed_outputs = files_ui()
            with gr.Tab("Search"):
                search_ui_outputs, search_ui_base_path_on_changed_outputs = search_ui()
            #with gr.Tab("Chat"):
            #    pass
            with gr.Tab("MCP"):
                pass

        files_ui_init_inputs(args.path)
        search_ui_init_inputs(args.path)

        base_path_textbox.input(
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
        )

        demo.load(
            files_ui_init,
            outputs=files_ui_outputs
        ).then(
            search_ui_init,
            outputs=search_ui_outputs
        ).then(
            lambda: args.path,
            outputs=[base_path_textbox, ]
        )

    demo.launch(inbrowser=not args.disable_auto_launch)