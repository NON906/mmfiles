import gradio as gr
import os
from dotenv import load_dotenv
import sqlite3
from PIL import Image

from ..search import edit_note, search, search_image

load_dotenv()
db_path = os.getenv("MMFILES_DB_PATH") or ".mmfiles.db"

global_base_path = None
global_results = None
global_select_file_path = None
global_select_file_index = -1

def search_ui_init_inputs(base_path):
    global global_base_path
    if not os.path.isdir(base_path):
        return
    global_base_path = base_path

def search_ui_init():
    pass

def search_ui_base_path_on_changed(base_path):
    global global_base_path
    if not os.path.isdir(base_path):
        return
    global_base_path = base_path

def search_button_click(search_query_input, search_image_input, min_rate, top_k):
    global global_results

    if search_query_input is None or search_query_input == "":
        if search_image_input is None:
            global_results = []
            return []
        # image search
        if type(search_image_input) is str:
            search_image_input = Image.open(search_image_input)
        global_results = search_image(search_image_input, k=top_k, min_rate=min_rate)
    else:
        # query search
        global_results = search(search_query_input, k=top_k, min_rate=min_rate)

    ret_list = []
    for result in global_results:
        ret_list.append(result["path"])

    return ret_list

def file_list_select(evt: gr.SelectData):
    global global_select_file_path, global_select_file_index

    if evt.value is None:
        global_select_file_path = None
        global_select_file_index = -1
        return gr.update(value="", interactive=False), gr.update(interactive=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

    global_select_file_path = global_results[evt.index]["path"]
    global_select_file_index = evt.index
    note = global_results[evt.index]["note"]

    if global_results[evt.index]["type"] == "image":
        return gr.update(value=note, interactive=True), gr.update(interactive=True), gr.update(visible=False), gr.update(value=global_select_file_path, visible=True), gr.update(visible=False), gr.update(visible=False)
    elif global_results[evt.index]["type"] == "audio":
        return gr.update(value=note, interactive=True), gr.update(interactive=True), gr.update(visible=False), gr.update(visible=False), gr.update(value=global_select_file_path, visible=True), gr.update(visible=False)
    elif global_results[evt.index]["type"] == "video":
        return gr.update(value=note, interactive=True), gr.update(interactive=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(value=global_select_file_path, visible=True)
    elif global_results[evt.index]["type"] == "document":
        pass
    elif global_results[evt.index]["type"] == "text":
        try:
            with open(global_select_file_path, "r", encoding="utf-8") as f:
                file_data = f.read()
            return gr.update(value=note, interactive=True), gr.update(interactive=True), gr.update(value=file_data, visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
        except:
            pass
    return gr.update(value=note, interactive=True), gr.update(interactive=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

def file_list_delete():
    ret_list = []
    for result in global_results:
        ret_list.append(result["path"])
    return ret_list

def note_input(note):
    global global_results

    if global_select_file_path is None:
        return
    global_results[global_select_file_index]["note"] = note
    edit_note(note, global_select_file_path)

def search_ui():
    with gr.Row():
        with gr.Column(scale=3):
            with gr.Row():
                with gr.Column():
                    search_query_textbox = gr.Textbox(label="Search query / 検索内容")
                    search_button = gr.Button(value="Search / 検索", variant="primary")
                with gr.Column():
                    search_image_input = gr.Image(label="Search image / 検索画像", type="pil")
        with gr.Column(scale=1):
            min_rate_slider = gr.Slider(label="Minimum rate / 閾値（割合）", value=0.75, minimum=0.0, maximum=1.0)
            top_k_number = gr.Number(label="Top k / 最大表示項目数", value=100)
    with gr.Row():
        with gr.Column():
            file_list = gr.File(label="Files / ファイル", file_count="multiple", interactive=False)
        with gr.Column():
            note_textbox = gr.Textbox(label="Note / ノート", interactive=False, lines=3)
            note_save_button = gr.Button(value="Save / 保存", interactive=False)
            text_preview = gr.Code(label="Preview / プレビュー", interactive=False, visible=False)
            image_preview = gr.Image(label="Preview / プレビュー", interactive=False, visible=False, type="filepath")
            audio_preview = gr.Audio(label="Preview / プレビュー", interactive=False, visible=False, type="filepath")
            video_preview = gr.Video(label="Preview / プレビュー", interactive=False, visible=False)

    search_image_input.upload(lambda: "", outputs=[search_query_textbox, ])

    search_button.click(search_button_click,
        inputs=[search_query_textbox, search_image_input, min_rate_slider, top_k_number],
        outputs=[file_list, ]
    )

    file_list.select(file_list_select,
        outputs=[note_textbox, note_save_button, text_preview, image_preview, audio_preview, video_preview]
    )
    file_list.delete(file_list_delete,
        outputs=[file_list, ]
    )

    note_save_button.click(note_input,
        inputs=[note_textbox, ]
    )

    search_ui_outputs = []
    search_ui_base_path_on_changed_outputs = []

    return search_ui_outputs, search_ui_base_path_on_changed_outputs