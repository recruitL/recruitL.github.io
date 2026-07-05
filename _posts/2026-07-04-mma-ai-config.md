---
title: "MMA 15 AI 配置流程：AI Assistant、Local MCP 与直连 API"
date: 2026-07-04 09:00:00 +0800
categories:
- 工具配置
tags:
- Mathematica
- Wolfram Language
- AI
- LLM
- MCP
feature_image: "https://raw.githubusercontent.com/recruitL/recruitL.github.io/main/document/picture/1300_400.jpg"
excerpt: "一份经过脱敏的 Mathematica 15 AI 配置流程：先分清内置 AI Assistant、外部 AI 调用本地 Wolfram，以及 Notebook 内直连模型 API。"
aside: true
share: false
---

这是一份可以公开保存的 MMA 15 / Wolfram Language 15 AI 配置流程。原始配置记录里涉及本机路径、账号状态、代理端口、API key 和客户端授权截图；下面统一改成通用占位写法，只保留配置思路、代码骨架和测试方法。

<!-- more -->

## 1. 总览：先分清三类 AI 配置

MMA 15 里的 AI 不只是一件事，至少要分成三层：

| 路线 | 方向 | 适合场景 |
|---|---|---|
| Wolfram AI Assistant / Chat Notebook | 在 Mathematica Notebook 里调用 Wolfram 官方 AI | 让 Notebook 解释代码、生成 Wolfram Language、辅助计算 |
| Wolfram Local MCP | 外部 AI 客户端调用本地 Wolfram | 让 Claude、Codex、Cursor 等把 Wolfram 当成本地计算工具 |
| 直连模型 API | 在 `init.m` 里封装自己的 LLM 函数 | 用自己的 GLM / DeepSeek / OpenAI 等 API key，绕开 Chatbook 侧栏 |

我的实际建议是：普通问答仍然用 AI App；MMA 里配置 AI 的价值，是把它变成 Notebook 内部的代码解释器、错误诊断器和公式说明器。

## 2. 路线 A：先检查 Wolfram 官方 AI Access

Wolfram 官方说明里，Version 15 开始，活跃的 Mathematica / Wolfram\|One 订阅会包含 AI Access Basic；AI Assistant 会用 LLM 把自然语言输入转成可执行的 Wolfram Language。官方的设置入口是：

```text
macOS: Wolfram / Settings / AI Settings / Services
其他系统: Edit / Preferences / AI Settings / Services
```

### 2.1 服务商：配置外部 API

如果你用的是官方 Chatbook / Chat Notebook，而不是本文后面的本地 HTTP 封装，那么 API 服务商入口就在 **AI 设置 -> 服务商**。这里可以选择直接连接服务商，例如 DeepSeek，并设置默认模型。

![Wolfram AI 设置中的服务商页，直接连接服务商处选择 DeepSeek 和模型。](/assets/images/mma-ai-config/provider-api-settings.png)

这张图里的重点是下面的 **直接连接服务商**，不是上面的 Wolfram AI Access 订阅卡片。DeepSeek / OpenAI / OpenRouter 这类服务商通常需要你自己的 API key，模型费用也按外部服务商规则走。

### 2.2 Ollama 本地中转：把第三方 API 包装成 Chatbook 模型

如果你用的是 GLM / Z.ai / BigModel 这类 **OpenAI-compatible** 接口，要注意 Wolfram 的 OpenAI 服务商面板通常只让你填 API key，不一定给你改 Base URL 的入口。OpenRouter 可以绕一层，但那走的是 OpenRouter 的账户和额度，不是你自己的第三方 API key。

更稳的做法是把第三方 API 包装成一个本机 Ollama-compatible 服务：

```text
Wolfram Chatbook
-> Ollama provider
-> http://127.0.0.1:11435
-> 第三方 OpenAI-compatible /chat/completions
```

这样 Wolfram 仍然选择 **Ollama** 服务商，本机 `127.0.0.1:11435` 负责把 `/api/chat`、`/api/generate`、`/api/tags` 等请求转发给上游模型。这里建议用 `11435`，因为 `11434` 是真实 Ollama 的默认端口，容易被 Ollama App、Wolfram 的 `UseLocalOllama` 或后台服务重新占走。完整代理代码不要放进网页正文，已经单独放到脱敏模板里：

- [查看 Ollama -> OpenAI-compatible 代理模板](/assets/docs/mma-ai-config/ollama-openai-compatible-proxy.md)

启动时只用占位符，不要把真实 key 写进 Markdown、截图、Git 仓库或 `init.m`：

```bash
cd ~/glm_ollama_proxy
source .venv/bin/activate

export GLM_BASE_URL="<OPENAI_COMPATIBLE_BASE_URL>"
export GLM_API_KEY="<THIRD_PARTY_API_KEY>"
export GLM_MODEL="<UPSTREAM_MODEL>"
export LOCAL_MODEL_NAME="glm:latest"

uvicorn glm_ollama_proxy:app --host 127.0.0.1 --port 11435
```

`GLM_BASE_URL` 写服务商文档或后台给出的 OpenAI-compatible base URL，不要写到 `/chat/completions`，模板会自动拼接。`uvicorn` 绑定到 `127.0.0.1` 即可，不要暴露到公网。

先用终端测试：

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

再回 Wolfram 里测 Ollama：

```wl
Quiet@ServiceExecute["Ollama", "SetOllamaPort", {"Port" -> 11435}];
Quiet@ServiceExecute["Ollama", "SetOllamaIP", {"IP" -> "127.0.0.1"}];
ServiceExecute["Ollama", "TestConnection"]

ServiceExecute[
  "Ollama",
  "ChatService",
  {"Model" -> "glm:latest",
   "Messages" -> {<|"Role" -> "User", "Content" -> "只回答 GLM_PROXY_TEST"|>}}
]
```

如果终端能看到 `POST /api/chat ... 200 OK`，并且返回内容包含 `GLM_PROXY_TEST`，说明链路已经通了。Wolfram 偶尔提示 `PresencePenalty` 不被 Ollama 支持，这通常只是参数被忽略的警告，不代表代理失败。

#### Clash TUN 之后真实 Ollama 抢端口的 debug

如果关闭再打开 Clash TUN 后，原来可用的代理突然返回：

```text
model 'glm:latest' not found
```

优先不要改 Python 代码。这个错误通常不是上游 GLM / Z.ai / BigModel 返回的，而是 Wolfram 又连到了 **真实 Ollama**。真实 Ollama 会检查本机是否真的有 `glm:latest` 模型；本文的 Python 代理不会检查这个名字，而是直接转发到 `GLM_MODEL`。

先查端口：

```bash
lsof -i :11434
lsof -i :11435
```

理想状态是：

```text
11434 -> ollama 可以存在，不管它
11435 -> Python / uvicorn 必须存在
```

如果 `11434` 里看到 `ollama ... LISTEN`，同时 `11435` 没有 `Python` / `uvicorn`，说明真实 Ollama 抢回了默认端口，而你的 GLM 代理没有跑。Clash TUN 本身不是“启动 Ollama”的直接原因，但它会刷新 DNS、系统代理、路由、loopback 访问和已有 TCP 连接；Wolfram / Chatbook / ServiceConnection 重新探测本地 Ollama 时，可能触发 Ollama App、Login Item、`launchctl` agent、`ServiceExecute["Ollama", "Start"]` 或 `ServiceExecute["Ollama", "UseLocalOllama"]`，从而把真实 Ollama 拉起来。

所以代理模式下不要运行：

```wl
ServiceExecute["Ollama", "Start"]
ServiceExecute["Ollama", "UseLocalOllama"]
```

只设置 IP 和端口：

```wl
SetEnvironment["NO_PROXY" -> "localhost,127.0.0.1,::1"];
SetEnvironment["no_proxy" -> "localhost,127.0.0.1,::1"];

Quiet@ServiceExecute["Ollama", "SetOllamaIP", {"IP" -> "127.0.0.1"}];
Quiet@ServiceExecute["Ollama", "SetOllamaPort", {"Port" -> 11435}];

{
  ServiceExecute["Ollama", "GetOllamaIP"],
  ServiceExecute["Ollama", "GetOllamaPort"],
  ServiceExecute["Ollama", "TestConnection"]
}
```

如果 `GetOllamaPort` 返回 `11434`，说明 Wolfram 又指回真实 Ollama 了，重新设为 `11435`。

Clash TUN 改写 DNS 时，可以在系统层修 DNS 和本地绕过规则：

```bash
sudo networksetup -setdnsservers Wi-Fi 223.5.5.5 119.29.29.29 8.8.8.8 1.1.1.1
networksetup -getdnsservers Wi-Fi
networksetup -setproxybypassdomains Wi-Fi localhost 127.0.0.1 ::1 "*.local"
```

但 DNS 修复不能防止真实 Ollama 抢端口。最稳的固定方案是：

```text
真实 Ollama: 允许占 11434
GLM 代理: 固定跑 11435
Wolfram Ollama service: 固定指向 127.0.0.1:11435
```

可以把启动命令保存成 `~/glm_ollama_proxy/start.sh`：

```bash
#!/bin/bash
cd ~/glm_ollama_proxy
source .venv/bin/activate

export GLM_BASE_URL="<OPENAI_COMPATIBLE_BASE_URL>"
export GLM_API_KEY="<THIRD_PARTY_API_KEY>"
export GLM_MODEL="<UPSTREAM_MODEL>"
export LOCAL_MODEL_NAME="glm:latest"

uvicorn glm_ollama_proxy:app --host 127.0.0.1 --port 11435
```

以后启动只需要：

```bash
chmod +x ~/glm_ollama_proxy/start.sh
~/glm_ollama_proxy/start.sh
```

如果之前在聊天记录、截图或终端日志里贴过真实 API key，应当去服务商后台删除旧 key，重新生成一个。

### 2.3 角色：不要选 Wolfram AI Assistant

如果你决定暂时使用官方 Chatbook 气泡界面，那么 **角色** 标签里建议保持普通聊天角色，并把 LLM 服务商设为 DeepSeek / OpenAI 等外部服务商。不要把角色或入口切到 Wolfram AI Assistant / Wolfram AI Access，除非你确实有对应订阅；否则很容易再次进入 Wolfram 自家 AI Access / Cloud 登录流程。

![Wolfram AI 设置中的角色页，角色保持普通聊天人，LLM 服务商选择 DeepSeek。](/assets/images/mma-ai-config/role-not-wolfram-ai.png)

### 2.4 工具：启用 LLM 可调用能力

在 **工具** 标签里，可以管理 LLM 能调用的工具，例如文档检索、WolframAlpha、Wolfram Language 代码执行、网页抓取和网页搜索等。需要安装更多工具时，可以点 **LLM 工具库**，它指向 Wolfram 官方的 [LLM Tool Repository](https://resources.wolframcloud.com/LLMToolRepository?ChannelID=5a7929e0-d26d-4d29-9928-4ed9e8cb9c60)。这个页面是 Wolfram 提供的 LLM 工具接口集合，用来给 LLM 增加可调用的工具能力。

![Wolfram AI 设置中的工具页，可以启用文档检索、WolframAlpha、Wolfram Language Evaluator 和网页工具。](/assets/images/mma-ai-config/llm-tools-settings.png)

### 2.5 Cell style：区分代码、文本和聊天输入

Notebook 顶部工具栏的 **单元的样式** 下拉菜单，决定当前 cell 是可执行代码、普通文字、标题，还是 Chatbook 相关的聊天输入。

![Wolfram Notebook 工具栏里的单元样式菜单，包含 Input、NaturalLanguageInput、ChatInput、ChatSystemInput 等样式。](/assets/images/mma-ai-config/cell-style-menu.png)

最常用的区分是：

| 样式 | 用途 | 什么时候用 |
|---|---|---|
| `Input` | Wolfram Language 可执行输入 | 写 `Series`、`NDSolve`、`FullSimplify` 等代码 |
| `Text` / `CodeText` | 普通说明文字 | 给 notebook 写解释、步骤、注释，不执行 |
| `NaturalLanguageInput` | Wolfram 自然语言输入 | 让 Wolfram 尝试把自然语言转成 Wolfram Language |
| `ChatInput` | Chatbook 的用户聊天输入 | 使用官方 Chatbook 时，把问题发给当前 LLM |
| `ChatSystemInput` | Chatbook 的系统提示词 | 给同一段聊天设定角色，比如“你是 Wolfram Language 专家” |
| `SideChat` | 侧边栏聊天相关样式 | 主要由 Chatbook 前端生成，通常不需要手动选 |
| `ChatBlockDivider` / `ChatDelimiter` | 聊天块分隔 | 用于 Chatbook 内部分隔对话轮次，一般不要手动改 |

实际使用时可以这么记：

```text
写代码并让 Kernel 执行 -> Input
写普通笔记说明 -> Text 或 CodeText
问官方 Chatbook 一个问题 -> ChatInput
给官方 Chatbook 设定长期角色 -> ChatSystemInput
```

### 2.6 最小测试：确认官方 AI Access 可用

进入后登录 Wolfram Account，再开一个新 Notebook 测试 Assistant。

在 Wolfram Language 里可以先检查：

```wl
$Version
$LLMEvaluator
```

再做一个最小测试：

```wl
LLMFunction["用一句话解释 Collect 和 FullSimplify 的区别。"][]
```

如果这一步失败，优先排查三件事：

- Wolfram Account 是否已经登录；
- 当前授权是否真的有 AI Access；
- Mathematica kernel 是否能访问外网。

网络可以用：

```wl
URLRead["https://www.wolfram.com"]
```

官方 `LLMFunction` 和 `LLMConfiguration` 走的是 Wolfram 的 LLM 功能体系，需要认证、计费或可用订阅，以及网络连接。

## 3. 路线 B：让外部 AI 调用本地 Wolfram

这和 AI Assistant 是反方向的配置。AI Assistant 是“你在 MMA 里问 AI”；Local MCP 是“外部 AI 调用本地 Wolfram 来算东西”。

### 3.1 MCP 服务入口

![Wolfram 面向 AI 的服务设置页，已配置 Claude Code、Claude Desktop 和 Codex CLI。](/assets/images/mma-ai-config/mcp-settings.png)

图中这个“面向 AI 的服务”页面就是 Local MCP / agent tools 的入口。这里配置的是外部 AI 环境能否访问本地 Wolfram，以及授予计算工具还是研发工具权限。

### 3.2 权限和测试

典型授权可以这样分：

| 客户端类型 | 推荐权限 | 原因 |
|---|---|---|
| 聊天型客户端 | Computation Tools | 主要用于积分、化简、绘图、数值计算 |
| 编码型 agent | Development Tools | 需要读写 Wolfram 项目、运行测试、检查 `.wl` / `.nb` |

例如，聊天客户端里可以测试：

```text
请调用 Wolfram 计算 Integrate[Sin[x]^2, {x, 0, Pi}]
```

如果返回 `Pi/2`，说明本地 Wolfram 计算链路基本通了。

安全上要保守一点：不信任的客户端不要给 Development Tools；含 API key、未公开论文数据、审稿材料的目录，不要随便让 agent 读写。只想让 AI 做数学计算时，优先给 Computation Tools。

## 4. 网络配置与修复：先保证 Kernel 能联网

Wolfram 的 AI Assistant、Chatbook、`LLMFunction`、`ServiceConnect`、Paclet 更新和本文的 HTTP 封装，最终都会落到 Mathematica Kernel 的网络能力上。浏览器、终端或 Codex 能联网，不等于 Mathematica 图形 App 里的 Kernel 一定能联网。

### 4.1 先在普通 Notebook 里测网络

不要先测 Chatbook 气泡界面。先开一个普通 input cell，按顺序跑：

```wl
URLRead["https://www.baidu.com"]
URLRead["https://www.wolfram.com"]
URLRead["https://api.deepseek.com"]
```

判断方式：

- `baidu.com` 成功、`api.deepseek.com` 失败：多半是代理分流或 DeepSeek 域名规则问题；
- 三个都失败：Mathematica Kernel 网络整体没通；
- Wolfram 成功、DeepSeek 失败：优先查 DeepSeek 域名是否被错误直连或错误代理；
- DeepSeek 成功，但 Chatbook 失败：再看 Chatbook paclet、模型资源或 Wolfram Cloud 登录状态。

如果看到：

```text
URLRead::ssl
URLFetch::ssl
libcurl error (35): TLS connect error
```

这通常不是 API key 问题，而是 Mathematica Kernel 到目标站点的 HTTPS/TLS 连接失败。

### 4.2 macOS 代理不要只看终端

macOS 图形 App 启动的 Mathematica 不一定继承终端里的 `HTTP_PROXY` / `HTTPS_PROXY` 环境变量。也就是说，浏览器、`curl` 或 Codex 能走代理，不代表 Wolfram Kernel 也走了同一条网络。

更稳的做法是让代理客户端开启：

```text
System Proxy: ON
TUN Mode: ON
```

然后彻底重启 Mathematica 和 WolframKernel，再重新测试：

```wl
URLRead["https://api.deepseek.com"]
```

如果必须从终端临时启动，可以用占位写法，不要把真实代理端口写进公开配置：

```bash
export HTTP_PROXY=http://<PROXY_HOST>:<PROXY_PORT>
export HTTPS_PROXY=http://<PROXY_HOST>:<PROXY_PORT>
export ALL_PROXY=socks5h://<PROXY_HOST>:<PROXY_PORT>
open -a Mathematica
```

这个办法在 macOS GUI App 上不一定稳定，优先级低于系统代理 / TUN。

### 4.3 网络通了以后再修 Chatbook / Paclet

如果先前出现过 `all-MiniLM-L6-v2 could not be found`、ChatbookInternal error、SemanticSearch 模型缺失，先不要急着重装所有东西。很多时候是首次下载模型或 paclet 时 SSL 失败，导致资源没装完整。

网络测通后，先更新 paclet 站点：

```wl
PacletSiteUpdate /@ PacletSites[]
```

再检查相关 paclet：

```wl
PacletFind["Wolfram/Chatbook"]
PacletFind["Wolfram/LLMFunctions"]
PacletFind["Wolfram/SemanticSearch"]
PacletFind["Wolfram/Embeddings"]
```

必要时重装 Chatbook 和 LLMFunctions：

```wl
PacletInstall["Wolfram/Chatbook", ForceVersionInstall -> True]
PacletInstall["Wolfram/LLMFunctions", ForceVersionInstall -> True]
```

这一步应放在网络修复之后。否则 paclet 重装本身也会继续失败。

### 4.4 旧连接和 MCP 干扰要分开排查

如果以前输错过 DeepSeek key，Wolfram 可能复用旧 service connection。可以先看：

```wl
ServiceConnections[]
```

再断开后重连：

```wl
ServiceDisconnect["DeepSeek"]
ServiceConnect["DeepSeek"]
```

如果 `ServiceDisconnect["DeepSeek"]` 不认，macOS 里可以到钥匙串搜索并删除旧的 Wolfram / DeepSeek / WolframConnector 凭据，再重新连接。

Chatbook 启动时如果同时部署 MCP / AgentTools，报错会混在一起。排查 DeepSeek 时，可以先在 **面向 AI 的服务** 页面临时禁用 Claude Code、Claude Desktop、Codex CLI 等 MCP 客户端，只测试：

```wl
URLRead["https://api.deepseek.com"]
LLMFunction["只输出 OK", LLMConfiguration["DeepSeek", "Model" -> "deepseek-chat"]][]
```

DeepSeek 和 Chatbook 都稳定后，再逐个启用 MCP。

### 4.5 推荐排查顺序

最省时间的顺序是：

```text
1. URLRead 测 baidu / wolfram / deepseek
2. 修系统代理、TUN 或 TLS 问题
3. ServiceConnect["DeepSeek"]
4. LLMFunction + LLMConfiguration["DeepSeek"]
5. PacletSiteUpdate 和 Chatbook paclet 修复
6. 打开官方 Chatbook
7. 最后再启用 Local MCP / AgentTools
```

不要反过来先折腾 Chatbook UI。底层网络没通时，DeepSeek API、模型下载、Chatbook 和 MCP 都会一起失败。

## 5. 路线 C：在 `init.m` 里直连自己的模型 API

如果 Wolfram Chatbook / Notebook Assistant 订阅或稳定性不合适，可以把 Mathematica 当成普通 HTTP 客户端，直接调用自己的模型 API。这个路线不依赖 `ServiceConnect["DeepSeek"]`，也不需要把 key 发给 Wolfram Cloud。

### 5.1 先判断哪些链路会触发 Cloud

后续实测后，边界可以这样分：

**可能走 Wolfram Cloud / ServiceConnect 的链路：**

- 右侧官方 Chatbook / AI Assistant 气泡界面：适合普通聊天；前提是接受登录 Wolfram Cloud。
- `LLMSynthesize` + `ServiceConnect["DeepSeek"]`：适合想使用 Wolfram 官方 LLM 框架时；它属于官方服务连接体系。

**不会走 Wolfram Cloud 的链路：**

- 本文的 `AskDeepSeek` / `DeepSeekChat` / `AskGLM`：适合公式解释、报错诊断、批处理和科研 notebook 工作流。
- 本文的 `DeepSeekBubbleChat[]` 本地面板：适合想要图形聊天界面，但不想接 Wolfram Cloud。

也就是说，**可以直接在 Mathematica 里用 chatbot，但不要把它接到 Wolfram 官方 Chatbook / Wolfram AI 体系上**。想彻底避开 Wolfram Cloud 弹窗，就走本文的 HTTP 封装和本地聊天面板。

关键原则：

- API key 放在 `$UserBaseDirectory/Private/` 下面；
- `init.m` 只保存读取 key 的逻辑，不保存真实 key；
- `init.m` 里不要启动时调用 `CloudConnect`、`ServiceConnect`、`LLMConfiguration` 或 `LLMSynthesize`；
- 请求 JSON 用 `ExportByteArray[..., "RawJSON"]`，避免中文被错误编码；
- 返回 JSON 用 `ImportByteArray[..., "RawJSON"]`，再从 `choices[[1]].message.content` 取文本。

### 5.2 保存 API key

先在 Mathematica 里创建私有目录：

```wl
CreateDirectory[
  FileNameJoin[{$UserBaseDirectory, "Private"}],
  CreateIntermediateDirectories -> True
]
```

然后把 key 写入本地私有文件。下面是占位符，不要把真实 key 写进 Git 仓库或公开文章。

```wl
Export[
  FileNameJoin[{$UserBaseDirectory, "Private", "glm_key.txt"}],
  "<PASTE_GLM_API_KEY_HERE>",
  "Text"
]

Export[
  FileNameJoin[{$UserBaseDirectory, "Private", "deepseek_key.txt"}],
  "<PASTE_DEEPSEEK_API_KEY_HERE>",
  "Text"
]
```

检查文件是否存在：

```wl
FileExistsQ /@ {
  FileNameJoin[{$UserBaseDirectory, "Private", "glm_key.txt"}],
  FileNameJoin[{$UserBaseDirectory, "Private", "deepseek_key.txt"}]
}
```

应该得到：

```wl
{True, True}
```

### 5.3 写入脱敏版 `init.m`

`init.m` 的位置用 Wolfram 自己的变量拼出来，不写具体用户名：

```wl
FileNameJoin[{$UserBaseDirectory, "Kernel", "init.m"}]
```

下面是一份可作为起点的模板。代理配置留成注释，需要时自己打开并改成本机端口。

完整模板已经移到独立 Markdown 文件，网页正文不再内嵌几百行代码：

- [查看完整 `init.m` 模板：Direct LLM API wrappers](/assets/docs/mma-ai-config/direct-llm-api-wrappers.md)
- 建议复制到 `FileNameJoin[{$UserBaseDirectory, "Kernel", "init.m"}]`。
- 模板包含 `AskGLM`、`AskDeepSeek`、`AskGLMShow`、`AskDeepSeekShow`、`DeepSeekBubbleChat[]`、`ExplainMMAError[...]`。
- API key 仍然只放在 `$UserBaseDirectory/Private/`，不要写进公开网页或 Git 仓库。

### 5.4 重启后测试

重启 Mathematica，先确认配置被加载：

```wl
?AskGLM
?AskDeepSeek
```

测试 GLM：

```wl
AskGLM["只输出 OK"]
```

测试 DeepSeek：

```wl
AskDeepSeek["只输出 OK", "deepseek-chat"]
```

查看真实返回模型，不要问模型“你是什么模型”：

```wl
GLMInspect["只输出 OK", "glm-4-flash"]["ReturnedModel"]
DeepSeekInspect["只输出 OK", "deepseek-chat"]["ReturnedModel"]
```

如果要诊断 Wolfram Language 报错：

```wl
ExplainMMAError[HoldForm[Series[x, {x, 1}]]]
```

这里用 `HoldForm` 是为了把错误输入交给诊断函数，而不是先让它在 Notebook 里直接报错。

如果不想只敲函数，也可以打开本地图形聊天面板：

```wl
DeepSeekBubbleChat[]
```

它会弹出一个小窗口，包含模型选择、输入框、发送按钮和上下文清空按钮。这个面板不是 Wolfram 官方右侧 Chatbook，底层仍然调用本文的 `DeepSeekChat[...]`，所以不会触发 Wolfram Cloud 登录流程。

## 6. 使用实例：Chatbook、自定义函数与 MCP

配置完成后，实际有三种常用入口：官方 Chatbook 气泡、本地自定义函数、外部 MCP。它们不是互相替代的关系，而是适合不同工作流。

### 6.1 Chatbook 气泡：最优雅的 Notebook 体验

如果你已经接受 Wolfram Cloud 登录 / service connection 的边界，那么官方 Chatbook 气泡是最优雅的用法。它直接嵌在 Notebook 里，可以在一段 Wolfram Language 输入和输出后面追问“我的代码在做什么？”，回答也能保留在同一个 notebook 记录里。

![Wolfram Notebook 里的 Chatbook 气泡在解释 Nest 微分算子和输出结果。](/assets/images/mma-ai-config/chatbook-bubble-example.png)

这类问题很适合用 Chatbook：

```text
我的代码在做什么？
这个输出能不能化成更物理的形式？
这里的 f'[r]、phi'[r] 和 phi''[r] 分别来自哪里？
```

优点是交互自然、排版好、上下文贴近当前 notebook。缺点是它仍然属于 Wolfram 官方 Chatbook / service connection 体系，可能碰到 Wolfram Cloud 登录、连接保存或 Chatbook paclet 状态问题。

### 6.2 自定义函数：最可控的科研工作流

如果你更在意可复现、批处理和本地 key 管理，就把表达式显式转成字符串，再交给自己的函数。截图里的函数名是本地自定义的 `DeepSeekChatShow`；本文模板里对应的是 `AskDeepSeekShow`。

![在 Wolfram Notebook 里把表达式转成 InputForm，再用自定义 DeepSeek 函数解释。](/assets/images/mma-ai-config/direct-api-example.png)

对应写法可以是：

```wl
expr = Nest[1/f[r] D[#, r] &, \[Phi][r], 2];

AskDeepSeekShow[
  "前面在做什么？请保留纯文本格式：\n" <>
  ToString[expr, InputForm]
]
```

这条路线没有 Chatbook 那么优雅，但很稳：API key 在本地文件里，请求体由你控制，输出可以直接进入 notebook 的计算记录。它尤其适合公式解释、报错诊断、论文语言整理和批量处理。

### 6.3 MCP：让外部 agent 调用 Wolfram

MCP 的用法是反过来的：不是在 Mathematica 里问 AI，而是在 Claude Code / Codex / Claude Desktop 这类外部 agent 里，让它调用本地 Wolfram 做计算。

![Claude Code 通过 Wolfram MCP 调用 Mathematica 计算微分表达式，并返回 LaTeX 形式结果。](/assets/images/mma-ai-config/mcp-claude-example.png)

适合这样问：

```text
调用 Mathematica 计算 1/f(r) d/dr(1/f(r) d/dr phi(r))，并把结果整理成 LaTeX。
```

这种方式适合外部代码 agent：它可以在终端、项目目录和 Wolfram 计算之间来回切换。缺点是阅读体验不如 Notebook 内的 Chatbook 气泡，更多是给 agent 执行任务，而不是给人边算边看。

### 6.4 怎么选

| 入口 | 最适合 | 评价 |
|---|---|---|
| 官方 Chatbook 气泡 | Notebook 里边算边问、解释当前 cell | 最优雅 |
| `AskDeepSeekShow` / 自定义函数 | 批处理、报错诊断、本地 key、可复现记录 | 最可控 |
| Local MCP | Claude / Codex 等外部 agent 调用 Wolfram | 最适合跨工具自动化 |

所以总结很简单：**人在 Notebook 里交互时，Chatbook chatbot 最优雅；要绕开 Cloud 或做批量科研工作流时，用本地自定义函数；要让外部 agent 算东西时，用 MCP。**

## 7. 为什么这比直接用 App 有用

如果只是问概念，直接用 ChatGPT / Claude / DeepSeek App 更方便。MMA 内接 AI 的优势是它能嵌进计算流：

```wl
expr = FullSimplify[...];

AskGLM[
  "请用黑洞微扰理论的语言解释下面 Wolfram Language 表达式结构：\n" <>
  ToString[expr, InputForm]
]
```

或者：

```wl
res = FullSimplify[expr, assumptions];

AskDeepSeekShow[
  "下面是一个符号化简结果。请说明它依赖哪些假设，以及可能的物理含义：\n" <>
  ToString[res, InputForm]
]
```

这样 Notebook 可以形成一条链：

```text
计算输入 -> 计算输出 -> 自动解释 -> 保存记录
```

这才是 MMA 里配置 AI 的主要价值。

## 8. 常见问题

### 8.1 `ServiceConnect["DeepSeek"]` 总是引导 Wolfram Cloud 登录怎么办？

如果只是想用自己的 DeepSeek API key，可以不用 `ServiceConnect`，直接按上面的 `HTTPRequest` 方式调用 API。`ServiceConnect` 是 Wolfram 官方服务连接体系，适合走官方认证流程；直连 API 更适合自己控制 key、模型名和错误处理。

要真正避开 Wolfram Cloud 弹窗，重点是两条：

```text
不要在 init.m 启动时运行 ServiceConnect / CloudConnect / LLMConfiguration / LLMSynthesize
不要把右侧官方 Chatbook 的默认服务商设成 DeepSeek 后又要求它不登录 Wolfram Cloud
```

可以用下面这段检查 `init.m` 是否还有会触发 Wolfram Cloud 的语句：

```wl
init = FileNameJoin[{$UserBaseDirectory, "Kernel", "init.m"}];

Select[
  StringSplit[Import[init, "Text"], "\n"],
  StringContainsQ[
    #,
    "ServiceConnect" | "CloudConnect" | "LLMConfiguration" | "LLMSynthesize"
  ] &
]
```

如果返回空列表，说明 `init.m` 基本干净。之后使用：

```wl
AskDeepSeek["只输出 OK"]
DeepSeekChat["继续解释"]
DeepSeekBubbleChat[]
```

这些都不会走 Wolfram Cloud。

如果弹窗仍出现，通常是官方 Chatbook 自己保存了 DeepSeek / ServiceConnect 设置。可以软重置前端里的 Chatbook 设置：

```wl
CurrentValue[
  $FrontEndSession,
  {PrivateFrontEndOptions, "InterfaceSettings", "ChatbookSettings"}
] = Inherited;

CurrentValue[
  $FrontEndSession,
  {PrivateFrontEndOptions, "InterfaceSettings", "AIAssistant"}
] = Inherited;

CurrentValue[
  $FrontEndSession,
  {PrivateFrontEndOptions, "InterfaceSettings", "LLM"}
] = Inherited;

CurrentValue[
  $FrontEndSession,
  {PrivateFrontEndOptions, "InterfaceSettings", "Chatbook"}
] = Inherited;
```

然后彻底重启 Wolfram。

如果坚持用官方右侧气泡 Chatbook，同时还把服务商设为 DeepSeek，那么最现实的做法是登录一次 Wolfram Cloud；不然它可能反复尝试同步 cloud-stored connections。这个登录弹窗不是 `Off[ServiceConnect::warnnosync]` 能彻底解决的；`Off[...]` 只能隐藏 warning，不能阻止登录流程。

### 8.2 Chatbook 修复后还能直接用吗？

可以。后续实测里，执行过类似：

```wl
PacletSiteUpdate /@ PacletSites[];
PacletUninstall /@ PacletFind["Wolfram/Chatbook"];
PacletInstall["Wolfram/Chatbook"];
```

之后官方 Chatbook 可能恢复正常。但这只修复 Chatbook paclet / 前端状态，不改变它和 Wolfram Cloud / ServiceConnect 的关系。

所以最稳的分工是：

| 用法 | 推荐处理 |
|---|---|
| 普通气泡聊天 | 官方 Chatbook + DeepSeek，接受登录 Wolfram Cloud |
| 科研表达式、代码、报错诊断 | `AskDeepSeek` / `AskGLM` / `ExplainMMAError` |
| 想要图形界面但不想登录 Cloud | `DeepSeekBubbleChat[]` |

### 8.3 只登录 Wolfram Cloud、不订阅 Wolfram AI Access 有什么影响？

影响不大，但要分清：

```text
登录 Wolfram Cloud != 订阅 Wolfram AI Access
```

只登录 Wolfram Cloud，通常只是让 Wolfram 能保存或同步 service connection，减少官方 Chatbook 反复弹登录窗口。它不会自动给你 Wolfram AI Access 订阅，也不等于开始使用 Wolfram 自家的 AI 额度。

需要注意的是：如果你在官方 Chatbook / ServiceConnect 里保存 DeepSeek API key，这个连接配置可能进入 Wolfram 的 connection 管理系统，是否同步到 Wolfram Cloud 取决于你当时的保存选项和登录状态。介意 key 保存位置或科研内容流向时，优先用本文的本地 key 文件和 `HTTPRequest` 封装。

### 8.4 返回中文乱码怎么办？

优先检查请求体是否用字节方式导出：

```wl
ExportByteArray[body, "RawJSON"]
```

不要先 `ExportString` 再塞给 HTTP body。中文请求在 Wolfram 里被错误转码时，模型会收到乱码，回答自然会不对。

### 8.5 模型说自己不是我指定的版本，是否说明路由错了？

不一定。模型的自我介绍不可靠。判断实际路由要看 API 返回里的 `model` 字段：

```wl
GLMInspect["只输出 OK", "glm-4-flash"]["ReturnedModel"]
```

### 8.6 没有 LLM Kit 是否还能用 Local MCP？

Wolfram 官方 Local MCP 页面说明 Local MCP 面向已安装的 Wolfram 应用，Version 15 可直接开始使用，并且 Q&A 写明不需要额外订阅。LLM Kit 或 AI Access 的订阅边界主要影响 Wolfram 自己的 AI Assistant / Chat Notebook / LLM 功能，不要把它和外部 AI 调用本地 Wolfram 的 MCP 链路混在一起。

## 9. 安全边界

- 不要把 API key 写进 `init.m` 或 Git 仓库；
- 如果 key 曾经发到聊天窗口或公开页面，直接去平台重置；
- 不要把未公开论文全文、审稿材料、私有数据直接交给外部模型；
- 只需要计算时给外部客户端 Computation Tools，确实要改代码时再给 Development Tools；
- 公开教程里不要出现真实用户名、真实本机路径、真实代理端口、真实账号状态截图。

## 10. 参考

- [Wolfram AI Assistant](https://www.wolfram.com/ai-assistant/)
- [Wolfram AI Access Subscriptions](https://www.wolfram.com/ai-access/)
- [How do I set up Wolfram AI Access?](https://support.wolfram.com/67504)
- [LLMFunction 文档](https://reference.wolfram.com/language/ref/LLMFunction.html)
- [LLMConfiguration 文档](https://reference.wolfram.com/language/ref/LLMConfiguration.html)
- [DeepSeek Service Connection 文档](https://reference.wolfram.com/language/ref/service/DeepSeek.html)
- [Wolfram Local MCP](https://www.wolfram.com/artificial-intelligence/mcp/local/)
- [Wolfram LLM Tool Repository](https://resources.wolframcloud.com/LLMToolRepository?ChannelID=5a7929e0-d26d-4d29-9928-4ed9e8cb9c60)
