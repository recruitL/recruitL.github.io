# Ollama local proxy for OpenAI-compatible APIs

这是《MMA 15 AI 配置流程：AI Assistant、Local MCP 与直连 API》的配套脱敏模板，用来把第三方 OpenAI-compatible API 包装成本机 Ollama-compatible 服务。

适用场景：

- Wolfram Chatbook 支持 Ollama，但第三方服务商面板不能改 Base URL；
- 你想使用自己的 GLM / Z.ai / BigModel / OpenAI-compatible API key；
- 你不想把 Notebook 的普通聊天链路接到 Wolfram AI Access / Wolfram Cloud 弹窗上；
- Clash TUN 或真实 Ollama 会把默认 `11434` 端口重新占走。

稳定链路如下：

```text
Wolfram Chatbook
-> Wolfram Ollama ServiceConnection
-> 127.0.0.1:11435
-> glm_ollama_proxy.py
-> optional Clash HTTP proxy
-> third-party OpenAI-compatible /chat/completions
```

本文只保留占位符。不要把真实 API key、个人目录、账单信息、服务商后台 URL、账号状态截图或真实代理地址写进公开仓库。

## 1. 文件分工

| 文件 | 是否必须 | 作用 |
|---|---:|---|
| `~/glm_ollama_proxy/glm_ollama_proxy.py` | 是 | 本机 Ollama-compatible HTTP 服务，把 `/api/chat`、`/api/generate`、`/api/tags` 转给上游 OpenAI-compatible API。 |
| `~/glm_ollama_proxy/.env` | 是 | 保存上游 Base URL、API key、模型名、可选 Clash HTTP 代理。这个文件不要提交到 Git。 |
| `~/glm_ollama_proxy/start.sh` | 是 | 固定启动代理，检查 `11435` 是否已经被占用。 |
| `$UserBaseDirectory/Kernel/init.m` | 是 | 让 Wolfram 启动后固定把 Ollama service 指向 `127.0.0.1:11435`。 |
| `~/Library/LaunchAgents/com.example.glm-ollama-proxy.plist` | 可选 | 让 macOS 登录后自动拉起代理。 |

`init.m` 不负责启动 Python 代理；它只告诉 Wolfram 去哪里找 Ollama-compatible 服务。Python 代理要由 `start.sh` 或 launchd 启动。

## 2. 创建目录和环境

```bash
mkdir -p ~/glm_ollama_proxy
cd ~/glm_ollama_proxy

python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn requests
```

## 3. `.env`

保存为 `~/glm_ollama_proxy/.env`：

```bash
export GLM_BASE_URL="<OPENAI_COMPATIBLE_BASE_URL>"
export GLM_API_KEY="<THIRD_PARTY_API_KEY>"
export GLM_MODEL="<UPSTREAM_MODEL>"
export LOCAL_MODEL_NAME="glm:latest"

# Optional. Use this only when Python requests to the upstream API must go through Clash.
# Example shape: http://<CLASH_HTTP_HOST>:<CLASH_HTTP_PORT>
export GLM_HTTPS_PROXY="<CLASH_HTTP_PROXY_URL>"

# Keep local Wolfram -> proxy traffic on loopback. Do not send localhost through Clash.
export NO_PROXY="localhost,127.0.0.1,::1"
export no_proxy="localhost,127.0.0.1,::1"

# Optional debug request logging inside the local proxy.
export DEBUG_LOG="0"
```

权限建议收紧：

```bash
chmod 600 ~/glm_ollama_proxy/.env
```

`GLM_BASE_URL` 写服务商文档或后台给出的 OpenAI-compatible base URL，不要写到 `/chat/completions`，代理代码会自动拼接。`GLM_HTTPS_PROXY` 只在 Python 到上游 API 出现 TLS / SSL EOF / 直连不稳定时启用；如果直连稳定，可以删掉这一行或留空。

## 4. `glm_ollama_proxy.py`

保存为 `~/glm_ollama_proxy/glm_ollama_proxy.py`：

```python
import json
import os
import time
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


app = FastAPI(title="OpenAI-Compatible Ollama Proxy")


UPSTREAM_API_KEY = os.environ.get("GLM_API_KEY", "").strip()
UPSTREAM_BASE_URL = os.environ.get("GLM_BASE_URL", "").rstrip("/")
UPSTREAM_MODEL = os.environ.get("GLM_MODEL", "<UPSTREAM_MODEL>").strip()
LOCAL_MODEL_NAME = os.environ.get("LOCAL_MODEL_NAME", "glm:latest").strip()
UPSTREAM_PROXY = os.environ.get("GLM_HTTPS_PROXY", "").strip()
DEBUG_LOG = os.environ.get("DEBUG_LOG", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


@app.middleware("http")
async def log_requests(request: Request, call_next):
    if not DEBUG_LOG:
        return await call_next(request)

    body = await request.body()
    print("---- INCOMING REQUEST ----")
    print(request.method, request.url.path)
    print(body.decode("utf-8", errors="replace")[:2000])

    async def receive():
        return {"type": "http.request", "body": body}

    request = Request(request.scope, receive)
    response = await call_next(request)
    print("---- RESPONSE STATUS ----", response.status_code)
    return response


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def ollama_done_fields() -> Dict[str, Any]:
    # Some clients use these duration/count fields as a rough success signal.
    return {
        "done_reason": "stop",
        "total_duration": 1000000000,
        "load_duration": 1000000,
        "prompt_eval_count": 1,
        "prompt_eval_duration": 1000000,
        "eval_count": 1,
        "eval_duration": 1000000,
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

    return params


def build_session() -> requests.Session:
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["POST"]),
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Do not accidentally inherit shell or GUI proxy variables. The only upstream
    # proxy used by this service is GLM_HTTPS_PROXY from .env.
    session.trust_env = False
    return session


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

    proxies = None
    if UPSTREAM_PROXY:
        proxies = {"http": UPSTREAM_PROXY, "https": UPSTREAM_PROXY}

    session = build_session()
    return session.post(
        url,
        headers={
            "Authorization": f"Bearer {UPSTREAM_API_KEY}",
            "Content-Type": "application/json",
            "Connection": "close",
            "User-Agent": "glm-ollama-proxy/0.1",
        },
        json=payload,
        stream=stream,
        timeout=(10, 300),
        proxies=proxies,
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
        "upstream_proxy": "enabled" if UPSTREAM_PROXY else "disabled",
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
            "general.architecture": "glm",
            "general.file_type": 0,
            "glm.context_length": 131072,
            "llama.context_length": 131072,
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

## 5. `start.sh`

保存为 `~/glm_ollama_proxy/start.sh`：

```bash
#!/bin/bash
set -e

cd "$HOME/glm_ollama_proxy"

source .venv/bin/activate

if [ -f .env ]; then
  source .env
else
  echo "Missing .env"
  exit 1
fi

PORT="${GLM_PROXY_PORT:-11435}"

echo "[1/4] Checking local proxy config..."
echo "  GLM_BASE_URL=$GLM_BASE_URL"
echo "  GLM_MODEL=$GLM_MODEL"
echo "  LOCAL_MODEL_NAME=$LOCAL_MODEL_NAME"
echo "  GLM_HTTPS_PROXY=${GLM_HTTPS_PROXY:-<empty>}"
echo "  GLM_API_KEY=<hidden>"

echo "[2/4] Checking port $PORT..."
if lsof -i :"$PORT" | grep -q LISTEN; then
  echo "Port $PORT is already occupied:"
  lsof -i :"$PORT"
  echo
  echo "If the listener is python/uvicorn, the proxy may already be running."
  echo "If the listener is real Ollama, stop it or move this proxy to another port."
  exit 1
fi

echo "[3/4] Starting proxy on 127.0.0.1:$PORT..."
uvicorn glm_ollama_proxy:app --host 127.0.0.1 --port "$PORT"
```

启动：

```bash
chmod +x ~/glm_ollama_proxy/start.sh
~/glm_ollama_proxy/start.sh
```

如果你确定永远不想让真实 Ollama 运行，可以在手动启动前执行：

```bash
pkill ollama 2>/dev/null || true
```

不建议把 `pkill ollama` 放进 launchd 的 `KeepAlive` 脚本里，否则自动重启时会反复杀掉真实 Ollama。

## 6. `init.m`

`init.m` 里只放 Wolfram 侧的固定指向，不放 API key，也不启动 Python 代理。

在 Wolfram Language 里先查看位置：

```wl
FileNameJoin[{$UserBaseDirectory, "Kernel", "init.m"}]
```

然后把下面内容放进去：

```wl
SetEnvironment["NO_PROXY" -> "localhost,127.0.0.1,::1"];
SetEnvironment["no_proxy" -> "localhost,127.0.0.1,::1"];

Quiet@ServiceExecute["Ollama", "SetOllamaIP", {"IP" -> "127.0.0.1"}];
Quiet@ServiceExecute["Ollama", "SetOllamaPort", {"Port" -> 11435}];

Quiet@Needs["LLMServices`"];
Off[ChatSubmit::llmunsupported];
Off[LLMServices`ChatSubmit::llmunsupported];
```

不要把下面这些测试调用放进 `init.m`：

```wl
ServiceExecute["Ollama", "ChatService", ...]
LLMFunction[...]
ServiceConnect[...]
CloudConnect[...]
```

`init.m` 应该轻量、可重复加载、没有外部副作用。

## 7. 可选：launchd 自动启动

保存为 `~/Library/LaunchAgents/com.example.glm-ollama-proxy.plist`，把 `<USER>` 换成本机用户名：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.example.glm-ollama-proxy</string>

  <key>ProgramArguments</key>
  <array>
    <string>/Users/&lt;USER&gt;/glm_ollama_proxy/start.sh</string>
  </array>

  <key>WorkingDirectory</key>
  <string>/Users/&lt;USER&gt;/glm_ollama_proxy</string>

  <key>RunAtLoad</key>
  <true/>

  <key>KeepAlive</key>
  <false/>

  <key>StandardOutPath</key>
  <string>/Users/&lt;USER&gt;/glm_ollama_proxy/proxy.out.log</string>

  <key>StandardErrorPath</key>
  <string>/Users/&lt;USER&gt;/glm_ollama_proxy/proxy.err.log</string>

  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
</dict>
</plist>
```

加载：

```bash
launchctl unload ~/Library/LaunchAgents/com.example.glm-ollama-proxy.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.example.glm-ollama-proxy.plist
```

新式 `launchctl` 也可以这样：

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.glm-ollama-proxy.plist
launchctl enable gui/$(id -u)/com.example.glm-ollama-proxy
launchctl kickstart -k gui/$(id -u)/com.example.glm-ollama-proxy
```

看日志：

```bash
tail -f ~/glm_ollama_proxy/proxy.out.log
tail -f ~/glm_ollama_proxy/proxy.err.log
```

## 8. 健康检查

先查端口：

```bash
lsof -i :11434
lsof -i :11435
```

理想结构：

```text
11434 -> 真实 Ollama 可以存在
11435 -> Python / uvicorn 必须存在
```

终端测本地代理：

```bash
curl http://127.0.0.1:11435/api/tags

curl http://127.0.0.1:11435/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm:latest",
    "stream": false,
    "messages": [
      {"role": "user", "content": "只回答 GLM_PROXY_TEST"}
    ]
  }'
```

Wolfram 里测：

```wl
{
  ServiceExecute["Ollama", "GetOllamaIP"],
  ServiceExecute["Ollama", "GetOllamaPort"],
  ServiceExecute["Ollama", "TestConnection"]
}

ServiceExecute[
  "Ollama",
  "ChatService",
  {"Model" -> "glm:latest",
   "Messages" -> {<|"Role" -> "User", "Content" -> "只回答 GLM_PROXY_TEST"|>}}
]
```

如果终端能返回 `GLM_PROXY_TEST`，Wolfram 也打到 `127.0.0.1:11435`，代理链路就是通的。

## 9. Clash TUN / SSL EOF / 真实 Ollama 抢端口

### 9.1 `model 'glm:latest' not found`

这个错误通常不是上游 OpenAI-compatible API 返回的，而是 Wolfram 打到了真实 Ollama。真实 Ollama 会检查本机是否真的有 `glm:latest` 模型；本文代理不会检查这个名字，而是转发到 `GLM_MODEL`。

处理：

```bash
lsof -i :11434
lsof -i :11435
```

如果 `11435` 没有 `python` / `uvicorn`，先启动代理。如果 Wolfram 里：

```wl
ServiceExecute["Ollama", "GetOllamaPort"]
```

返回 `11434`，重新设为：

```wl
Quiet@ServiceExecute["Ollama", "SetOllamaIP", {"IP" -> "127.0.0.1"}];
Quiet@ServiceExecute["Ollama", "SetOllamaPort", {"Port" -> 11435}];
```

代理模式下不要运行：

```wl
ServiceExecute["Ollama", "Start"]
ServiceExecute["Ollama", "UseLocalOllama"]
```

这些命令可能启动真正的本地 Ollama。

### 9.2 Python 到上游出现 SSL EOF

如果本地代理能收到请求，但 Python 到上游 API 报类似：

```text
SSLEOFError
HTTPSConnectionPool
Max retries exceeded
```

先确认 Clash HTTP 代理本身能打到上游：

```bash
curl -x <CLASH_HTTP_PROXY_URL> -v \
  <OPENAI_COMPATIBLE_BASE_URL>/chat/completions
```

如果这里能返回 `401`、`403` 或服务商格式的认证错误，说明代理和 TLS 是通的，只是没有带 API key。然后把同一个代理地址写入 `.env`：

```bash
export GLM_HTTPS_PROXY="<CLASH_HTTP_PROXY_URL>"
```

本文代码会用 `requests.Session()`、`Retry`、`HTTPAdapter`、`session.trust_env = False`、显式 `proxies=...`、`Connection: close` 和 `User-Agent` 来绕开 Python requests 直连时的 SSL EOF 抖动。

### 9.3 Clash TUN 改写 DNS

Clash TUN 会刷新 DNS、系统代理、路由、loopback 访问和旧 TCP 连接。必要时可以修系统 DNS 和本地绕过：

```bash
sudo networksetup -setdnsservers Wi-Fi 223.5.5.5 119.29.29.29 8.8.8.8 1.1.1.1
networksetup -getdnsservers Wi-Fi
networksetup -setproxybypassdomains Wi-Fi localhost 127.0.0.1 ::1 "*.local"
```

但 DNS 修复不能防止真实 Ollama 抢 `11434`。最稳结构仍然是：

```text
真实 Ollama: 11434
GLM proxy: 11435
Wolfram Ollama service: 127.0.0.1:11435
```

## 10. 常见问题

| 现象 | 判断 | 处理 |
|---|---|---|
| `curl /api/tags` 不通 | 本地代理没有启动或端口不对 | 运行 `~/glm_ollama_proxy/start.sh`，确认 `lsof -i :11435` 是 `python` / `uvicorn`。 |
| `curl /api/chat` 报上游错误 | 服务商 API 参数或网络不对 | 检查 `GLM_BASE_URL`、`GLM_MODEL`、`GLM_API_KEY`、`GLM_HTTPS_PROXY`。 |
| `model 'glm:latest' not found` | Wolfram 打到了真实 Ollama | 让代理固定跑 `11435`，并在 Wolfram 里 `SetOllamaPort -> 11435`。 |
| `Port 11435 is already occupied` 且占用者是 `python` | 代理可能已经在运行 | 不要重复启动；直接用 `curl /api/chat` 测。 |
| `Port 11435 is already occupied` 且占用者是 `ollama` | 端口被真实 Ollama 占了 | 停掉真实 Ollama，或给代理换端口并同步改 Wolfram 端口。 |
| Python 报 `session is not defined` | 代码只局部替换过 | 直接用本文完整 `call_upstream_chat` 和 `build_session`。 |
| Python 报 `DEBUG_LOG is not defined` | middleware 里用了未定义变量 | 确认文件顶部有 `DEBUG_LOG = ...`。 |
| Wolfram 提示 `PresencePenalty` 不支持 | 通常只是参数忽略警告 | 只要终端显示 `POST /api/chat ... 200 OK`，先看返回内容是否正常。 |
| 终端一关就不能用了 | 代理进程被关闭 | 用 `start.sh` 常驻，或用 launchd 登录启动。 |
| `.env` 里 key 泄露 | 密钥已经不可信 | 立刻去服务商后台删除旧 key，重新生成，并确认 `.env` 权限是 `600`。 |

## 11. 安全提醒

- 真实 API key 只放在 `.env` 或本机私有密钥文件中；
- 不要把真实 key 写进 Markdown、Notebook、`init.m`、Git 仓库、截图或聊天记录；
- 如果 key 曾经贴进公开或半公开对话，应当删除旧 key 并重建；
- 本地代理只绑定 `127.0.0.1`，不要对公网开放；
- 公开教程里不要出现真实用户名、真实本机路径、真实代理地址或真实账号状态截图。
