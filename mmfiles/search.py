import os
import sys
import hashlib
from io import BytesIO
import sqlite3
from contextlib import redirect_stdout
from dotenv import load_dotenv
from torch.utils.data import DataLoader
from PIL import Image
import librosa
from colpali_engine.models import ColQwen2_5Omni, ColQwen2_5OmniProcessor
import torch
from transformers import BitsAndBytesConfig
from tqdm import tqdm
import numpy as np

load_dotenv()

db_path = os.getenv("MMFILES_DB_PATH") or ".mmfiles.db"
base_dir_path = "."

load_in_4bit = True
if os.getenv("LOAD_IN_4BIT") is not None:
    load_in_4bit = bool(os.getenv("LOAD_IN_4BIT"))
with redirect_stdout(sys.stderr):
    model = ColQwen2_5Omni.from_pretrained(
        "vidore/colqwen-omni-v0.1",
        torch_dtype=torch.bfloat16,
        device_map=os.getenv("DEVICE_MAP") or "cuda",  # or "mps" if on Apple Silicon
        #attn_implementation="flash_attention_2" # if is_flash_attn_2_available() else None,
        quantization_config=BitsAndBytesConfig(load_in_4bit=load_in_4bit)
    ).eval()
    processor = ColQwen2_5OmniProcessor.from_pretrained("vidore/colqwen-omni-v0.1")

file_vectors = None
file_details = None

def tensor_to_buffer(tensor: torch.Tensor) -> bytes:
    buffer = BytesIO()
    torch.save(tensor, buffer)
    return buffer.getvalue()

def buffer_to_tensor(buffer: bytes) -> torch.Tensor:
    return torch.load(BytesIO(buffer))

def change_base_dir(path: str):
    global base_dir_path
    base_dir_path = path

files_init_allow_types = ["text", "image", "audio"]
def files_init(allow_types=None):
    global file_vectors, file_details, files_init_allow_types

    if allow_types is None:
        allow_types = files_init_allow_types
    if files_init_allow_types == allow_types and file_vectors is not None:
        return
    files_init_allow_types = allow_types

    db_conn = sqlite3.connect(db_path)
    file_vectors = []
    file_details = []
    for current, subfolders, subfiles in os.walk(base_dir_path):
        for subfile in subfiles:
            subfile_path = os.path.abspath(os.path.join(current, subfile))
            cursor = db_conn.cursor()
            sql = """SELECT vector, note FROM file_hashes INNER JOIN search_vectors USING(file_hash) LEFT OUTER JOIN notes USING(file_hash) WHERE path=?"""
            cursor.execute(sql, (subfile_path, ))
            results = cursor.fetchall()
            for result in results:
                _, ext = os.path.splitext(subfile_path)
                ext = ext.lower()
                if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"]:
                    file_type = "image"
                elif ext in [".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a"]:
                    file_type = "audio"
                elif ext in [".mp4", ".mov", ".wmv", ".avi", ".webm", ".flv", ".mkv"]:
                    file_type = "video"
                elif ext in [".pdf", ".docx", ".pptx"]:
                    file_type = "document"
                else:
                    file_type = "text"
                if file_type in allow_types:
                    file_vectors.append(buffer_to_tensor(result[0]))
                    file_details.append({
                        "path": subfile_path,
                        "note": result[1],
                        "type": file_type
                    })

def update():
    global file_vectors, file_details

    db_conn = sqlite3.connect(db_path)

    cursor = db_conn.cursor()
    sql = """SELECT name FROM sqlite_master WHERE TYPE='table'"""
    cursor.execute(sql)
    table_names = cursor.fetchall()
    if not ("file_hashes", ) in table_names:
        cursor = db_conn.cursor()
        sql = """CREATE TABLE IF NOT EXISTS file_hashes(path STRING PRIMARY KEY, file_hash STRING)"""
        cursor.execute(sql)
    if not ("notes", ) in table_names:
        cursor = db_conn.cursor()
        sql = """CREATE TABLE IF NOT EXISTS notes(file_hash STRING PRIMARY KEY, note STRING)"""
        cursor.execute(sql)
    if not ("search_vectors", ) in table_names:
        cursor = db_conn.cursor()
        sql = """CREATE TABLE IF NOT EXISTS search_vectors(file_hash STRING PRIMARY KEY, type INTEGER, vector BLOB)"""
        cursor.execute(sql)

    target_text_files = []
    target_image_files = []
    target_audio_files = []
    for current, subfolders, subfiles in os.walk(base_dir_path):
        for subfile in subfiles:
            subfile_path = os.path.abspath(os.path.join(current, subfile))
            cursor = db_conn.cursor()
            sql = """SELECT file_hash FROM file_hashes WHERE path=?"""
            cursor.execute(sql, (subfile_path, ))
            hash_temp = cursor.fetchone()
            if hash_temp is not None:
                hash_on_db = hash_temp[0]
            else:
                hash_on_db = None
            with open(subfile_path, "rb") as f:
                file_data = f.read()
                hash_on_file = hashlib.sha256(file_data).hexdigest()
            if hash_on_db is None:
                cursor = db_conn.cursor()
                sql = """INSERT INTO file_hashes VALUES(?,?)"""
                cursor.execute(sql, (subfile_path, hash_on_file))
            elif hash_on_db != hash_on_file:
                cursor = db_conn.cursor()
                sql = """UPDATE file_hashes SET file_hash=? WHERE path=?"""
                cursor.execute(sql, (hash_on_file, subfile_path))
                cursor = db_conn.cursor()
                sql = """UPDATE notes SET file_hash=? WHERE file_hash=?"""
                cursor.execute(sql, (hash_on_file, hash_on_db))
                cursor = db_conn.cursor()
                sql = """UPDATE search_vectors SET file_hash=? WHERE file_hash=? AND type=1"""
                cursor.execute(sql, (hash_on_file, hash_on_db))
                cursor = db_conn.cursor()
                sql = """DELETE search_vectors WHERE file_hash=? AND type=0"""
                cursor.execute(sql, (hash_on_db, ))
            if hash_on_db is None or hash_on_db != hash_on_file:
                _, ext = os.path.splitext(subfile_path)
                ext = ext.lower()
                if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"]:
                    target_image_files.append({
                        "path": subfile_path,
                        "hash": hash_on_file
                    })
                elif ext in [".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a"]:
                    target_audio_files.append({
                        "path": subfile_path,
                        "hash": hash_on_file
                    })
                elif ext in [".mp4", ".mov", ".wmv", ".avi", ".webm", ".flv", ".mkv"]:
                    # video file
                    pass
                elif ext in [".pdf", ".docx", ".pptx"]:
                    # document file
                    pass
                else:
                    try:
                        with open(subfile_path, "r", encoding="utf-8") as f:
                            f.read()
                        target_text_files.append({
                            "path": subfile_path,
                            "hash": hash_on_file
                        })
                    except:
                        pass

    def data_embedding(dataloader):
        ds = []
        for batch_doc in tqdm(dataloader):
            with torch.no_grad():
                batch_doc = {k: v.to(model.device) for k, v in batch_doc.items()}
                embeddings_doc = model(**batch_doc)
            ds.extend(list(torch.unbind(embeddings_doc.to("cpu"))))
        return ds

    if len(target_text_files) > 0:
        target_text_datas = []
        for target_file in target_text_files:
            with open(target_file["path"], "r", encoding="utf-8") as f:
                target_text_datas.append(f.read())
        dataloader = DataLoader(
            dataset=target_text_datas,
            batch_size=4,
            shuffle=False,
            collate_fn=lambda x: processor.process_queries(x),
        )
        with redirect_stdout(sys.stderr):
            print("Embedding texts.")
            ds = data_embedding(dataloader)
        for target_file, target_vector in zip(target_text_files, ds):
            cursor = db_conn.cursor()
            sql = """INSERT INTO search_vectors VALUES(?,0,?)"""
            cursor.execute(sql, (target_file["hash"], tensor_to_buffer(target_vector)))
        del target_text_datas

    if len(target_image_files) > 0:
        target_image_datas = []
        for target_file in target_image_files:
            target_image_datas.append(Image.open(target_file["path"]))
        dataloader = DataLoader(
            dataset=target_image_datas,
            batch_size=2,
            shuffle=False,
            collate_fn=lambda x: processor.process_images(x),
        )
        with redirect_stdout(sys.stderr):
            print("Embedding images.")
            ds = data_embedding(dataloader)
        for target_file, target_vector in zip(target_image_files, ds):
            cursor = db_conn.cursor()
            sql = """INSERT INTO search_vectors VALUES(?,0,?)"""
            cursor.execute(sql, (target_file["hash"], tensor_to_buffer(target_vector)))
        del target_image_datas

    if len(target_audio_files) > 0:
        target_audio_datas = []
        for target_file in target_audio_files:
            data, _ = librosa.load(target_file["path"], sr=24000, mono=True)
            target_audio_datas.append(data)
        dataloader = DataLoader(
            dataset=target_audio_datas,
            batch_size=2,
            shuffle=False,
            collate_fn=lambda x: processor.process_audios(x),
        )
        with redirect_stdout(sys.stderr):
            print("Embedding audios.")
            ds = data_embedding(dataloader)
        for target_file, target_vector in zip(target_audio_files, ds):
            cursor = db_conn.cursor()
            sql = """INSERT INTO search_vectors VALUES(?,0,?)"""
            cursor.execute(sql, (target_file["hash"], tensor_to_buffer(target_vector)))
        del target_audio_datas

    file_vectors = None
    file_details = None

    db_conn.commit()
    db_conn.close()

def search(query: str, k=5) -> list:
    global file_vectors, file_details

    files_init()

    db_conn = sqlite3.connect(db_path)
    
    batch_queries = processor.process_queries([query]).to(model.device)
    with torch.no_grad():
        query_embeddings = model(**batch_queries)
    scores = processor.score_multi_vector(query_embeddings, file_vectors)
    rank_list = scores[0].topk(len(file_vectors)).indices.tolist()

    ret_list = []
    for rank_index in rank_list:
        next_flag = False
        for ret_item in ret_list:
            if file_details[rank_index]["path"] == ret_item["path"]:
                next_flag = True
                break
        if next_flag:
            continue
        
        ret_list.append(file_details[rank_index])

        if len(ret_list) >= k:
            break

    db_conn.close()

    return ret_list

if __name__ == "__main__":
    change_base_dir("files")
    update()
    files_init()
    print(search("テストファイル"))