from mcp.server.fastmcp import FastMCP, Image, Audio
from mcp.server.fastmcp.prompts import base
import argparse

from . import search

def search_prompt_common(question: str, top_k: int, query: str):
    datas = [query, ]
    search.update()
    search_result = search.search(question, k=top_k)
    for index, result_item in enumerate(search_result):
        add_text = f'{index + 1}. {result_item["path"]}'
        if result_item["note"] is not None:
            add_text += "\nNOTE: " + result_item["note"]
        datas[-1] += add_text
        if result_item["type"] == "text":
            with open(result_item["path"], "r", encoding="utf-8") as f:
                datas[-1] += "\n" + f.read() + "\n\n"
        elif result_item["type"] == "image":
            datas.append(Image(result_item["path"]).to_image_content())
            if index < len(search_result) - 1:
                datas.append("")
        elif result_item["type"] == "audio":
            datas.append(Audio(result_item["path"]).to_audio_content())
            if index < len(search_result) - 1:
                datas.append("")

    ret_datas = []
    for data in datas:
        ret_datas.append(base.UserMessage(data))

    return ret_datas

def mcp_server_main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", default="files", help="Target directory path.")
    parser.add_argument("--disable_text", action="store_true", help="Disable text search.")
    parser.add_argument("--disable_image", action="store_true", help="Disable image search.")
    parser.add_argument("--disable_audio", action="store_true", help="Disable audio search.")
    args = parser.parse_args()

    mcp = FastMCP("mmfiles")

    @mcp.prompt(title="Search by multi-modal RAG")
    def mmfiles_search_prompt_en(question: str, top_k: int = 5) -> list:
        return search_prompt_common(question, top_k, f"""Please answer the questions below.

**Question:**
> {question}

**Retrieved Information:**
Below is the information the RAG system searched and referenced to generate the answer.

""")

    @mcp.prompt(title="マルチモーダルRAGで検索（日本語）")
    def mmfiles_search_prompt_ja(question: str, top_k: int = 5) -> list:
        return search_prompt_common(question, top_k, f"""以下の質問に答えてください。

**質問文:**
> {question}

**参照情報 (Retrieved Information):**
以下は、回答を生成するためにRAGシステムが検索・参照した情報です。

""")

    @mcp.tool()
    def mmfiles_search_rag(query: str, top_k: int = 5) -> tuple:
        """Retrieve files using Multi-modal RAG

Arguments:
- query: The search query string.
- top_k: The maximum number of items to fetch.
         If this result exceeds maximum length, reduce it."""
        search.update()
        search_result = search.search(query, k=top_k)
        ret_list = [search_result, ]
        for result_item in search_result:
            if result_item["type"] == "text":
                with open(result_item["path"], "r", encoding="utf-8") as f:
                    ret_list.append(f.read())
            elif result_item["type"] == "image":
                ret_list.append(Image(result_item["path"]))
            elif result_item["type"] == "audio":
                ret_list.append(Audio(result_item["path"]))
        return tuple(ret_list)

    allow_types = []
    if not args.disable_text:
        allow_types.append("text")
    if not args.disable_image:
        allow_types.append("image")
    if not args.disable_audio:
        allow_types.append("audio")

    search.change_base_dir(args.path)
    search.update()
    search.files_init(allow_types=allow_types)

    return mcp