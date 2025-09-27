import gradio as gr

from .files_ui import files_ui, files_ui_init_inputs, files_ui_init, files_ui_base_path_on_changed
from .search_ui import search_ui, search_ui_init_inputs, search_ui_init, search_ui_base_path_on_changed
from .. import search

def main_ui():
    search.change_base_dir("files")
    search.update()
    search.files_init()

    with gr.Blocks() as demo:
        with gr.Row():
            base_path_textbox = gr.Textbox(label="Directory Path / ディレクトリパス")
        with gr.Row():
            with gr.Tab("Files"):
                files_ui_outputs, files_ui_base_path_on_changed_outputs = files_ui()
            with gr.Tab("Search"):
                search_ui_outputs, search_ui_base_path_on_changed_outputs = search_ui()
            with gr.Tab("Chat"):
                pass
            with gr.Tab("MCP"):
                pass

        files_ui_init_inputs("files")
        search_ui_init_inputs("files")

        base_path_textbox.input(
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
            lambda: "files",
            outputs=[base_path_textbox, ]
        )

    return demo