import gradio as gr
import os
from dotenv import load_dotenv
import sqlite3

from ..search import edit_note

load_dotenv()
db_path = os.getenv("MMFILES_DB_PATH") or ".mmfiles.db"

global_base_path = None

def files_ui_init_inputs(base_path):
    global global_base_path
    global_base_path = base_path

def files_ui_init():
    return gr.update(root_dir=global_base_path)

def files_base_path_on_changed(base_path):
    global global_base_path
    global_base_path = base_path
    return gr.update(root_dir=global_base_path)

def file_explorer_change(file_path):
    if file_path is None:
        return gr.update(value="", interactive=False), gr.update(interactive=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

    abs_path = os.path.abspath(os.path.join(global_base_path, file_path))

    db_conn = sqlite3.connect(db_path)

    cursor = db_conn.cursor()
    sql = """SELECT note FROM file_hashes INNER JOIN notes USING(file_hash) WHERE path=?"""
    cursor.execute(sql, (abs_path, ))
    note_temp = cursor.fetchone()
    if note_temp is not None:
        note = note_temp[0]
    else:
        note = ""

    db_conn.close()

    _, ext = os.path.splitext(abs_path)
    ext = ext.lower()
    if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"]:
        return gr.update(value=note, interactive=True), gr.update(interactive=True), gr.update(visible=False), gr.update(value=abs_path, visible=True), gr.update(visible=False), gr.update(visible=False)
    elif ext in [".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a"]:
        return gr.update(value=note, interactive=True), gr.update(interactive=True), gr.update(visible=False), gr.update(visible=False), gr.update(value=abs_path, visible=True), gr.update(visible=False)
    elif ext in [".mp4", ".mov", ".wmv", ".avi", ".webm", ".flv", ".mkv"]:
        return gr.update(value=note, interactive=True), gr.update(interactive=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(value=abs_path, visible=True)
    elif ext in [".pdf", ".docx", ".pptx"]:
        pass
    else:
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                file_data = f.read()
            return gr.update(value=note, interactive=True), gr.update(interactive=True), gr.update(value=file_data, visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
        except:
            pass
    return gr.update(value=note, interactive=True), gr.update(interactive=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

def note_input(note, file_path):
    abs_path = os.path.abspath(os.path.join(global_base_path, file_path))
    edit_note(note, abs_path)

def files_ui():
    with gr.Row():
        with gr.Column():
            file_explorer = gr.FileExplorer(label="Files / ファイル", file_count="single")
        with gr.Column():
            note_textbox = gr.Textbox(label="Note / ノート", interactive=False, lines=3)
            note_save_button = gr.Button(value="Save / 保存", interactive=False)
            text_preview = gr.Code(label="Preview / プレビュー", interactive=False, visible=False)
            image_preview = gr.Image(label="Preview / プレビュー", interactive=False, visible=False, type="filepath")
            audio_preview = gr.Audio(label="Preview / プレビュー", interactive=False, visible=False, type="filepath")
            video_preview = gr.Video(label="Preview / プレビュー", interactive=False, visible=False)

    file_explorer.change(file_explorer_change,
        inputs=[file_explorer, ],
        outputs=[note_textbox, note_save_button, text_preview, image_preview, audio_preview, video_preview])

    note_save_button.click(note_input,
        inputs=[note_textbox, file_explorer]
    )

    files_ui_outputs = [file_explorer, ]
    files_base_path_on_changed_outputs = [file_explorer, ]

    return files_ui_outputs, files_base_path_on_changed_outputs