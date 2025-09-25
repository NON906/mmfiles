from mcp.server.fastmcp import FastMCP, Image, Audio
from mcp.server.fastmcp.prompts import base
from . import search

def mcp_server_main():
    mcp = FastMCP("mmfiles")

    @mcp.prompt(title="with multi-modal RAG")
    def search_prompt(question: str) -> str:
        datas = [
f"""以下の質問に答えてください。

**質問文:**
> {question}

**参照情報 (Retrieved Information):**
以下は、回答を生成するためにRAGシステムが検索・参照した情報です。

"""]
        search.update()
        search_result = search.search(question)
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

    search.change_base_dir("files")
    search.update()

    return mcp