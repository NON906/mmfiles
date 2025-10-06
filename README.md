# mmfiles

A multimodal search system (RAG) that can search for various files.
It uses [vidore/colqwen-omni-v0.1](https://huggingface.co/vidore/colqwen-omni-v0.1) from [ColPali](https://github.com/illuin-tech/colpali).
It has been tested on Windows.
It also supports MCP, allowing you to search with compatible LLM (Large Language Model) services.
Currently, it supports text, image, and audio files.
You can make files searchable just by putting them in the specified directory.

## How to Start

First, please [install](https://docs.astral.sh/uv/getting-started/installation/) [uv](https://docs.astral.sh/uv/).

After installation, execute the following command in a command prompt or similar.

```
uvx --from git+https://github.com/NON906/mmfiles mmfiles
```

You can change the directory to be searched by using `--path` (`-p`) as follows.
(The default is the `files` folder in the current directory).

```
uvx --from git+https://github.com/NON906/mmfiles mmfiles --path "D:\target_dir"
```

You can change the behavior by setting the following environment variables before starting.

| Environment Variable | Details |
| --- | --- |
| `MMFILES_DB_PATH` | Specifies the path to the database file that stores information about the files to be searched.<br>The default is the `.mmfiles.db` file in the current directory. |
| `LOAD_IN_4BIT` | Enables or disables 4-bit quantization.<br>The default is enabled. |
| `DEVICE_MAP` | Specifies the computation device.<br>You can specify `cuda`, `mps`, or `cpu`.<br>The default is `cuda`. |

When started, your browser will open automatically, and you can add file descriptions (Notes) (optional) and search for files.

In file search, you can specify either text or an image.
(If text is entered, the image will be disabled).
It is also possible to search for image and audio files with text.
If there is a file description (Note), it will also be included in the search.

## How to Use MCP

You can use it by appending the contents of the MCP tab after startup to the corresponding tool's JSON file (such as `claude_desktop_config.json`).

The list of specifiable options and environment variables is as follows.

| Option | Details |
| --- | --- |
| `--path` (`-p`) | Specifies the path of the directory to be searched.<br>The default is the `files` folder in the current directory. |
| `--disable_text` | Excludes text files from the search. |
| `--disable_image` | Excludes image files from the search. |
| `--disable_audio` | Excludes audio files from the search. |

| Environment Variable | Details |
| --- | --- |
| `MMFILES_DB_PATH` | Specifies the path to the database file that stores information about the files to be searched.<br>The default is the `.mmfiles.db` file in the current directory. |
| `LOAD_IN_4BIT` | Enables or disables 4-bit quantization.<br>The default is enabled. |
| `DEVICE_MAP` | Specifies the computation device.<br>You can specify `cuda`, `mps`, or `cpu`.<br>The default is `cuda`. |
