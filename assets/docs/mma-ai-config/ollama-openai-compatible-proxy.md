# Ollama local proxy for OpenAI-compatible APIs

这是《MMA 15 AI 配置流程：AI Assistant、Local MCP 与直连 API》的配套脱敏模板，用来把第三方 OpenAI-compatible API 包装成本机 Ollama-compatible 服务。

适用场景：

- Wolfram Chatbook 支持 Ollama；
- Wolfram 的 OpenAI 服务商面板不能改 Base URL；
- 你想使用自己的 GLM / Z.ai / BigModel 等第三方 API key，而不是走 Wolfram AI Access 或 OpenRouter 账户。

链路：

```text
Wolfram Chatbook
-> Ollama provider
-> http://127.0.0.1:11434
-> 第三方 OpenAI-compatible /chat/completions
```

本文只保留占位符。不要把真实 API key、个人目录、账单信息、服务商截图或后台 URL 写进公开仓库。

## 1. 创建目录和环境

```bash
mkdir -p ~/glm_ollama_proxy
cd ~/glm_ollama_proxy

python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn requests
```

## 2. 代理代码

保存为 `~/glm_ollama_proxy/glm_ollama_proxy.py`。

```python
import json
import os
import time
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse


app = FastAPI(title="OpenAI-Compatible Ollama Proxy")


# Environment configuration.
UPSTREAM_API_KEY = os.environ.get("GLM_API_KEY", "").strip()
UPSTREAM_BASE_URL = os.environ.get("GLM_BASE_URL", "").rstrip("/")
UPSTREAM_MODEL = os.environ.get("GLM_MODEL", "<UPSTREAM_MODEL>").strip()

# Model name exposed to Wolfram/Ollama-compatible clients.
LOCAL_MODEL_NAME = os.environ.get("LOCAL_MODEL_NAME", "glm:latest").strip()


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def ollama_done_fields() -> Dict[str, Any]:
    # Some clients expect these fields even when the proxy cannot measure them.
    return {
        "done_reason": "stop",
        "total_duration": 1,
        "load_duration": 1,
        "prompt_eval_count": 0,
        "prompt_eval_duration": 1,
        "eval_count": 1,
        "eval_duration": 1,
    }


def model_from_request(body: Dict[str, Any]) -> str:
    return body.get("model") or LOCAL_MODEL_NAME


def normalize_messages(messages: Any) -> List[Dict[str, str]]:
    if not isinstance(messages, list):
        return []

    normalized: List[Dict[str, str]] = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue

        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role not in {"system", "user", "assistant", "tool"}:
            role = "user"

        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False)

        normalized.append({"role": role, "content": content})

    return normalized


def openai_params_from_ollama_body(body: Dict[str, Any]) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    options = body.get("options") or {}
    if not isinstance(options, dict):
        options = {}

    if "temperature" in options:
        params["temperature"] = options["temperature"]
    if "top_p" in options:
        params["top_p"] = options["top_p"]
    if "num_predict" in options:
        params["max_tokens"] = options["num_predict"]

    if body.get("temperature") is not None:
        params["temperature"] = body["temperature"]
    if body.get("top_p") is not None:
        params["top_p"] = body["top_p"]
    if body.get("max_tokens") is not None:
        params["max_tokens"] = body["max_tokens"]

    # Wolfram may pass unsupported parameters such as PresencePenalty.
    # Ollama services ignore unsupported parameters; the proxy follows that behavior.
    return params


def call_upstream_chat(
    messages: List[Dict[str, str]],
    stream: bool,
    body: Optional[Dict[str, Any]] = None,
) -> requests.Response:
    if not UPSTREAM_API_KEY:
        raise RuntimeError("GLM_API_KEY is empty")

    if not UPSTREAM_BASE_URL:
        raise RuntimeError("GLM_BASE_URL is empty")

    url = f"{UPSTREAM_BASE_URL}/chat/completions"
    payload: Dict[str, Any] = {
        "model": UPSTREAM_MODEL,
        "messages": messages,
        "stream": stream,
    }
    payload.update(openai_params_from_ollama_body(body or {}))

    return requests.post(
        url,
        headers={
            "Authorization": f"Bearer {UPSTREAM_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        stream=stream,
        timeout=300,
    )


def extract_nonstream_content(data: Dict[str, Any]) -> str:
    try:
        return data["choices"][0]["message"].get("content", "") or ""
    except Exception:
        return ""


def extract_stream_delta(line: str) -> str:
    line = line.strip()
    if not line:
        return ""

    if line.startswith("data: "):
        line = line[6:].strip()

    if line == "[DONE]":
        return ""

    try:
        data = json.loads(line)
        delta = data["choices"][0].get("delta", {})
        return delta.get("content", "") or ""
    except Exception:
        return ""


def upstream_error(status_code: int, text: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": "upstream error",
            "upstream_status_code": status_code,
            "upstream_body": text,
        },
    )


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "openai-compatible-ollama-proxy",
        "local_model": LOCAL_MODEL_NAME,
        "upstream_model": UPSTREAM_MODEL,
    }


@app.get("/api/version")
def version():
    return {"version": "0.1.0"}


@app.get("/api/tags")
def tags():
    return {
        "models": [
            {
                "name": LOCAL_MODEL_NAME,
                "model": LOCAL_MODEL_NAME,
                "modified_at": now_iso(),
                "size": 1,
                "digest": "openai-compatible-proxy",
                "details": {
                    "parent_model": "",
                    "format": "proxy",
                    "family": "openai-compatible",
                    "families": ["openai-compatible"],
                    "parameter_size": "proxy",
                    "quantization_level": "proxy",
                },
            }
        ]
    }


@app.post("/api/show")
async def show(request: Request):
    body = await request.json()
    name = body.get("name") or LOCAL_MODEL_NAME

    return {
        "license": "",
        "modelfile": f"FROM {name}",
        "parameters": "",
        "template": "{{ .Prompt }}",
        "details": {
            "parent_model": "",
            "format": "proxy",
            "family": "openai-compatible",
            "families": ["openai-compatible"],
            "parameter_size": "proxy",
            "quantization_level": "proxy",
        },
        "model_info": {
            "general.architecture": "openai-compatible-proxy",
            "general.file_type": 0,
        },
        "capabilities": ["completion", "tools"],
    }


@app.get("/api/ps")
def ps():
    return {"models": []}


@app.post("/api/chat")
async def api_chat(request: Request):
    body = await request.json()
    client_model_name = model_from_request(body)
    messages = normalize_messages(body.get("messages", []))
    stream = bool(body.get("stream", False))

    if not messages:
        return JSONResponse(status_code=400, content={"error": "messages is required"})

    if not stream:
        try:
            response = call_upstream_chat(messages, stream=False, body=body)
        except Exception as exc:
            return JSONResponse(
                status_code=500,
                content={"error": "proxy error", "detail": str(exc)},
            )

        if response.status_code >= 400:
            return upstream_error(response.status_code, response.text)

        try:
            data = response.json()
        except Exception:
            return JSONResponse(
                status_code=502,
                content={"error": "invalid upstream json", "body": response.text},
            )

        content = extract_nonstream_content(data)
        result = {
            "model": client_model_name,
            "created_at": now_iso(),
            "message": {"role": "assistant", "content": content},
            "done": True,
        }
        result.update(ollama_done_fields())
        return result

    def event_stream():
        try:
            response = call_upstream_chat(messages, stream=True, body=body)
        except Exception as exc:
            yield json.dumps(
                {
                    "model": client_model_name,
                    "created_at": now_iso(),
                    "message": {"role": "assistant", "content": f"[proxy error] {exc}"},
                    "done": True,
                    **ollama_done_fields(),
                },
                ensure_ascii=False,
            ) + "\n"
            return

        if response.status_code >= 400:
            yield json.dumps(
                {
                    "model": client_model_name,
                    "created_at": now_iso(),
                    "message": {
                        "role": "assistant",
                        "content": f"[upstream error {response.status_code}] {response.text}",
                    },
                    "done": True,
                    **ollama_done_fields(),
                },
                ensure_ascii=False,
            ) + "\n"
            return

        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line:
                continue

            if raw_line.strip() in {"data: [DONE]", "[DONE]"}:
                break

            content = extract_stream_delta(raw_line)
            if content:
                yield json.dumps(
                    {
                        "model": client_model_name,
                        "created_at": now_iso(),
                        "message": {"role": "assistant", "content": content},
                        "done": False,
                    },
                    ensure_ascii=False,
                ) + "\n"

        yield json.dumps(
            {
                "model": client_model_name,
                "created_at": now_iso(),
                "message": {"role": "assistant", "content": ""},
                "done": True,
                **ollama_done_fields(),
            },
            ensure_ascii=False,
        ) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@app.post("/api/generate")
async def api_generate(request: Request):
    body = await request.json()
    client_model_name = model_from_request(body)
    prompt = body.get("prompt", "")
    stream = bool(body.get("stream", False))

    if not isinstance(prompt, str):
        prompt = json.dumps(prompt, ensure_ascii=False)

    messages = [{"role": "user", "content": prompt}]

    if not stream:
        try:
            response = call_upstream_chat(messages, stream=False, body=body)
        except Exception as exc:
            return JSONResponse(
                status_code=500,
                content={"error": "proxy error", "detail": str(exc)},
            )

        if response.status_code >= 400:
            return upstream_error(response.status_code, response.text)

        try:
            data = response.json()
        except Exception:
            return JSONResponse(
                status_code=502,
                content={"error": "invalid upstream json", "body": response.text},
            )

        content = extract_nonstream_content(data)
        result = {
            "model": client_model_name,
            "created_at": now_iso(),
            "response": content,
            "done": True,
            "context": [],
        }
        result.update(ollama_done_fields())
        return result

    def event_stream():
        try:
            response = call_upstream_chat(messages, stream=True, body=body)
        except Exception as exc:
            yield json.dumps(
                {
                    "model": client_model_name,
                    "created_at": now_iso(),
                    "response": f"[proxy error] {exc}",
                    "done": True,
                    "context": [],
                    **ollama_done_fields(),
                },
                ensure_ascii=False,
            ) + "\n"
            return

        if response.status_code >= 400:
            yield json.dumps(
                {
                    "model": client_model_name,
                    "created_at": now_iso(),
                    "response": f"[upstream error {response.status_code}] {response.text}",
                    "done": True,
                    "context": [],
                    **ollama_done_fields(),
                },
                ensure_ascii=False,
            ) + "\n"
            return

        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line:
                continue

            if raw_line.strip() in {"data: [DONE]", "[DONE]"}:
                break

            content = extract_stream_delta(raw_line)
            if content:
                yield json.dumps(
                    {
                        "model": client_model_name,
                        "created_at": now_iso(),
                        "response": content,
                        "done": False,
                    },
                    ensure_ascii=False,
                ) + "\n"

        yield json.dumps(
            {
                "model": client_model_name,
                "created_at": now_iso(),
                "response": "",
                "done": True,
                "context": [],
                **ollama_done_fields(),
            },
            ensure_ascii=False,
        ) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")
```

## 3. 启动代理

`GLM_BASE_URL` 写服务商文档或后台提供的 OpenAI-compatible base URL，不要写到 `/chat/completions`，代理会自动拼接。

```bash
cd ~/glm_ollama_proxy
source .venv/bin/activate

export GLM_BASE_URL="<OPENAI_COMPATIBLE_BASE_URL>"
export GLM_API_KEY="<THIRD_PARTY_API_KEY>"
export GLM_MODEL="<UPSTREAM_MODEL>"
export LOCAL_MODEL_NAME="glm:latest"

uvicorn glm_ollama_proxy:app --host 127.0.0.1 --port 11434
```

如果端口被真正的 Ollama 占用，先退出 Ollama App，或换一个端口并在 Wolfram 里同步设置端口。不要把 `uvicorn` 绑定到 `0.0.0.0` 暴露给公网。

## 4. 终端测试

新开一个终端：

```bash
curl http://127.0.0.1:11434/api/tags
```

应该看到 `glm:latest` 一类的本地模型名。

继续测试聊天：

```bash
curl http://127.0.0.1:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm:latest",
    "stream": false,
    "messages": [
      {"role": "user", "content": "只回答 GLM_PROXY_TEST"}
    ]
  }'
```

如果返回内容里有 `GLM_PROXY_TEST`，说明本地代理到上游 API 的链路已经通了。

## 5. Wolfram 测试

在 Mathematica / Wolfram Language 中：

```wl
Quiet@ServiceExecute["Ollama", "SetOllamaPort", {"Port" -> 11434}];
Quiet@ServiceExecute["Ollama", "SetOllamaIP", {"IP" -> "127.0.0.1"}];
ServiceExecute["Ollama", "TestConnection"]
```

再测试聊天：

```wl
ServiceExecute[
  "Ollama",
  "ChatService",
  {"Model" -> "glm:latest",
   "Messages" -> {<|"Role" -> "User", "Content" -> "只回答 GLM_PROXY_TEST"|>}}
]
```

如果 Wolfram 设置页没有显示 `glm:latest`，但终端日志里已经出现：

```text
POST /api/chat ... 200 OK
```

说明 Wolfram 已经访问本地代理。模型显示名可以和 `LOCAL_MODEL_NAME` 不完全一致，因为代理最终调用的上游模型由 `GLM_MODEL` 决定。

## 6. 常见问题

| 现象 | 判断 | 处理 |
|---|---|---|
| `curl /api/tags` 不通 | 本地代理没有启动或端口不对 | 检查 `uvicorn` 是否还在运行，确认端口是 `11434` |
| `curl /api/chat` 报上游错误 | 服务商 API 参数不对 | 检查 `GLM_BASE_URL`、`GLM_MODEL`、`GLM_API_KEY`，不要把 base URL 写到 `/chat/completions` |
| Wolfram 提示 `PresencePenalty` 不支持 | 通常只是参数忽略警告 | 只要终端显示 `POST /api/chat ... 200 OK`，先看返回内容是否正常 |
| Wolfram 红框但终端是 `200 OK` | Chatbook 前端期望的字段可能更多 | 看是否调用了 `/api/show`、`/api/generate`、`/api/ps`，必要时补兼容端点 |
| 终端一关就不能用了 | 代理进程被关闭 | 保持 `uvicorn` 终端运行，或写本机启动脚本 |

## 7. 安全提醒

- 真实 API key 只放在本机环境变量或私有密钥文件中。
- 不要把真实 key 写进 Markdown、Notebook、`init.m`、Git 仓库、截图或聊天记录。
- 如果 key 曾经贴进公开或半公开对话，应当删除旧 key 并重建。
- 本地代理只绑定 `127.0.0.1`，不要对公网开放。
