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
---

这是一份可以公开保存的 MMA 15 / Wolfram Language 15 AI 配置流程。原始配置记录里涉及本机路径、账号状态、代理端口、API key 和客户端授权截图；下面统一改成通用占位写法，只保留配置思路、代码骨架和测试方法。

<!-- more -->

## 先分清三类 AI 配置

MMA 15 里的 AI 不只是一件事，至少要分成三层：

| 路线 | 方向 | 适合场景 |
|---|---|---|
| Wolfram AI Assistant / Chat Notebook | 在 Mathematica Notebook 里调用 Wolfram 官方 AI | 让 Notebook 解释代码、生成 Wolfram Language、辅助计算 |
| Wolfram Local MCP | 外部 AI 客户端调用本地 Wolfram | 让 Claude、Codex、Cursor 等把 Wolfram 当成本地计算工具 |
| 直连模型 API | 在 `init.m` 里封装自己的 LLM 函数 | 用自己的 GLM / DeepSeek / OpenAI 等 API key，绕开 Chatbook 侧栏 |

我的实际建议是：普通问答仍然用 AI App；MMA 里配置 AI 的价值，是把它变成 Notebook 内部的代码解释器、错误诊断器和公式说明器。

## 路线 A：先检查 Wolfram 官方 AI Access

Wolfram 官方说明里，Version 15 开始，活跃的 Mathematica / Wolfram\|One 订阅会包含 AI Access Basic；AI Assistant 会用 LLM 把自然语言输入转成可执行的 Wolfram Language。官方的设置入口是：

```text
macOS: Wolfram / Settings / AI Settings / Services
其他系统: Edit / Preferences / AI Settings / Services
```

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

## 路线 B：让外部 AI 调用本地 Wolfram

这和 AI Assistant 是反方向的配置。AI Assistant 是“你在 MMA 里问 AI”；Local MCP 是“外部 AI 调用本地 Wolfram 来算东西”。

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

## 路线 C：在 `init.m` 里直连自己的模型 API

如果 Wolfram Chatbook / Notebook Assistant 订阅或稳定性不合适，可以把 Mathematica 当成普通 HTTP 客户端，直接调用自己的模型 API。这个路线不依赖 `ServiceConnect["DeepSeek"]`，也不需要把 key 发给 Wolfram Cloud。

关键原则：

- API key 放在 `$UserBaseDirectory/Private/` 下面；
- `init.m` 只保存读取 key 的逻辑，不保存真实 key；
- 请求 JSON 用 `ExportByteArray[..., "RawJSON"]`，避免中文被错误编码；
- 返回 JSON 用 `ImportByteArray[..., "RawJSON"]`，再从 `choices[[1]].message.content` 取文本。

### 1. 保存 API key

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

### 2. 写入脱敏版 `init.m`

`init.m` 的位置用 Wolfram 自己的变量拼出来，不写具体用户名：

```wl
FileNameJoin[{$UserBaseDirectory, "Kernel", "init.m"}]
```

下面是一份可作为起点的模板。代理配置留成注释，需要时自己打开并改成本机端口。

```wl
(* ::Package:: *)

(* ========================================================= *)
(*  User init.m: Direct LLM API wrappers                     *)
(*  Providers: GLM / DeepSeek                                *)
(*  Keys are read from $UserBaseDirectory/Private/.           *)
(* ========================================================= *)

(* Optional proxy. Uncomment and edit only when needed.
$DefaultProxyRules["UseProxy"] = Manual;
$DefaultProxyRules["HTTP"] = {"127.0.0.1", 7890};
$DefaultProxyRules["HTTPS"] = {"127.0.0.1", 7890};
$DefaultProxyRules["Socks"] = None;
*)

ClearAll[AIPrivateFile, AIReadKey];

AIPrivateFile[name_String] :=
  FileNameJoin[{$UserBaseDirectory, "Private", name}];

AIReadKey[file_String] := Module[{x},
  If[! FileExistsQ[file],
    Return[Failure["MissingAPIKey", <|"ExpectedFile" -> file|>]]
  ];

  x = StringTrim[Import[file, "Text"]];

  If[StringLength[x] == 0,
    Failure["EmptyAPIKey", <|"ExpectedFile" -> file|>],
    x
  ]
];


ClearAll[$GLMEndpoint, $GLMKeyFile, $DeepSeekEndpoint, $DeepSeekKeyFile];

$GLMEndpoint =
  "https://open.bigmodel.cn/api/paas/v4/chat/completions";

$GLMKeyFile =
  AIPrivateFile["glm_key.txt"];

$DeepSeekEndpoint =
  "https://api.deepseek.com/chat/completions";

$DeepSeekKeyFile =
  AIPrivateFile["deepseek_key.txt"];


ClearAll[
  AIFailureQ, AIResponseRaw, AIResponseText, AIPath,
  AIParseJSON, AIContent, AIInspect, AIChatRaw
];

AIFailureQ[x_] := MatchQ[x, _Failure];

AIResponseRaw[resp_] :=
  Quiet @ Check[resp["Body"], Quiet @ Check[resp[[1]], $Failed]];

AIResponseText[raw_] := Which[
  Head[raw] === ByteArray,
    Quiet @ Check[ByteArrayToString[raw, "UTF-8"], ToString[raw, InputForm]],

  StringQ[raw],
    raw,

  True,
    ToString[raw, InputForm]
];

AIPath[x_, {}] := x;

AIPath[x_Association, {k_, rest___}] :=
  AIPath[Lookup[x, k, Missing["KeyAbsent", k]], {rest}];

AIPath[x_List, {i_Integer, rest___}] /; 1 <= i <= Length[x] :=
  AIPath[x[[i]], {rest}];

AIPath[_, path_] := Missing["PathAbsent", path];

AIParseJSON[raw_] := Module[{json, text},
  json = Which[
    Head[raw] === ByteArray,
      Quiet @ Check[ImportByteArray[raw, "RawJSON"], $Failed],

    StringQ[raw],
      Quiet @ Check[ImportString[raw, "RawJSON"], $Failed],

    True,
      $Failed
  ];

  If[AssociationQ[json] || ListQ[json],
    json,
    text = AIResponseText[raw];
    Failure["JSONParseFailed", <|"RawText" -> text|>]
  ]
];

AIContent[json_] := Module[{content},
  If[AIFailureQ[json], Return[json]];

  content = AIPath[json, {"choices", 1, "message", "content"}];

  If[StringQ[content],
    content,
    Failure["NoContent", <|"JSON" -> json|>]
  ]
];

AIInspect[json_, requestedModel_String] := Module[{msg},
  If[AIFailureQ[json], Return[json]];

  msg = AIPath[json, {"choices", 1, "message"}];

  <|
    "RequestedModel" -> requestedModel,
    "ReturnedModel" -> Lookup[json, "model", Missing["NoModelField"]],
    "Content" -> AIContent[json],
    "Reasoning" -> If[
      AssociationQ[msg],
      Lookup[msg, "reasoning_content", Missing["NoReasoning"]],
      Missing["NoMessage"]
    ],
    "Usage" -> Lookup[json, "usage", Missing["NoUsage"]]
  |>
];

AIChatRaw[
  endpoint_String,
  keyFile_String,
  model_String,
  messages_List,
  temperature_: 0.2,
  extra_Association: <||>
] := Module[
  {key, body, bodyBytes, req, resp, raw, status},

  key = AIReadKey[keyFile];
  If[AIFailureQ[key], Return[key]];

  body = Join[
    <|
      "model" -> model,
      "messages" -> messages,
      "temperature" -> temperature,
      "stream" -> False
    |>,
    extra
  ];

  bodyBytes = Quiet @ Check[ExportByteArray[body, "RawJSON"], $Failed];
  If[Head[bodyBytes] =!= ByteArray,
    Return[Failure["JSONExportFailed", <|"Body" -> body|>]]
  ];

  req = HTTPRequest[
    endpoint,
    <|
      "Method" -> "POST",
      "Headers" -> {
        "Authorization" -> "Bearer " <> key,
        "Content-Type" -> "application/json; charset=utf-8",
        "Accept" -> "application/json",
        "Accept-Encoding" -> "identity"
      },
      "Body" -> bodyBytes
    |>
  ];

  resp = Quiet @ Check[URLRead[req], $Failed];
  If[resp === $Failed,
    Return[Failure["URLReadFailed", <|"Endpoint" -> endpoint|>]]
  ];

  raw = AIResponseRaw[resp];
  status = Quiet @ Check[resp["StatusCode"], Missing["NoStatusCode"]];

  If[status =!= 200,
    Return[
      Failure[
        "APIError",
        <|
          "StatusCode" -> status,
          "Endpoint" -> endpoint,
          "RawText" -> AIResponseText[raw]
        |>
      ]
    ]
  ];

  AIParseJSON[raw]
];


ClearAll[AskGLM, GLMInspect, $GLMHistory, GLMChat, GLMClear];

If[! AssociationQ[$GLMHistory], $GLMHistory = <||>];

AskGLM[
  prompt_String,
  model_String: "glm-4-flash",
  temperature_: 0.2
] := Module[{json},
  json = AIChatRaw[
    $GLMEndpoint,
    $GLMKeyFile,
    model,
    {<|"role" -> "user", "content" -> prompt|>},
    temperature
  ];

  AIContent[json]
];

GLMInspect[
  prompt_String,
  model_String: "glm-4-flash",
  temperature_: 0.2
] := Module[{json},
  json = AIChatRaw[
    $GLMEndpoint,
    $GLMKeyFile,
    model,
    {<|"role" -> "user", "content" -> prompt|>},
    temperature
  ];

  AIInspect[json, model]
];

GLMClear[] := ($GLMHistory = <||>; Null);

GLMChat[
  text_String,
  model_String: "glm-4-flash",
  temperature_: 0.2
] := Module[{messages, json, content},
  messages = Append[
    Lookup[$GLMHistory, model, {}],
    <|"role" -> "user", "content" -> text|>
  ];

  json = AIChatRaw[$GLMEndpoint, $GLMKeyFile, model, messages, temperature];
  If[AIFailureQ[json], Return[json]];

  content = AIContent[json];
  If[AIFailureQ[content], Return[content]];

  AssociateTo[
    $GLMHistory,
    model -> Append[messages, <|"role" -> "assistant", "content" -> content|>]
  ];

  content
];


ClearAll[AskDeepSeek, DeepSeekInspect, $DeepSeekHistory, DeepSeekChat, DeepSeekClear];

If[! AssociationQ[$DeepSeekHistory], $DeepSeekHistory = <||>];

AskDeepSeek[
  prompt_String,
  model_String: "deepseek-chat",
  temperature_: 0.2
] := Module[{json},
  json = AIChatRaw[
    $DeepSeekEndpoint,
    $DeepSeekKeyFile,
    model,
    {<|"role" -> "user", "content" -> prompt|>},
    temperature
  ];

  AIContent[json]
];

DeepSeekInspect[
  prompt_String,
  model_String: "deepseek-chat",
  temperature_: 0.2
] := Module[{json},
  json = AIChatRaw[
    $DeepSeekEndpoint,
    $DeepSeekKeyFile,
    model,
    {<|"role" -> "user", "content" -> prompt|>},
    temperature
  ];

  AIInspect[json, model]
];

DeepSeekClear[] := ($DeepSeekHistory = <||>; Null);

DeepSeekChat[
  text_String,
  model_String: "deepseek-chat",
  temperature_: 0.2
] := Module[{messages, json, content},
  messages = Append[
    Lookup[$DeepSeekHistory, model, {}],
    <|"role" -> "user", "content" -> text|>
  ];

  json = AIChatRaw[$DeepSeekEndpoint, $DeepSeekKeyFile, model, messages, temperature];
  If[AIFailureQ[json], Return[json]];

  content = AIContent[json];
  If[AIFailureQ[content], Return[content]];

  AssociateTo[
    $DeepSeekHistory,
    model -> Append[messages, <|"role" -> "assistant", "content" -> content|>]
  ];

  content
];


ClearAll[AIShow, AskGLMShow, AskDeepSeekShow, ExplainMMAError];

AIShow[s_String, style_String: "Text"] := (
  CellPrint[Cell[StringReplace[s, {"\\n" -> "\n", "\\t" -> "\t"}], style]];
  Null
);

AIShow[x_, style_String: "Text"] := (Print[x]; Null);

AskGLMShow[
  prompt_String,
  model_String: "glm-4-flash",
  temperature_: 0.2
] := AIShow @ AskGLM[
  "请用适合 Wolfram Notebook Text 单元显示的纯文本回答。不要使用 Markdown 代码围栏。\n\n" <> prompt,
  model,
  temperature
];

AskDeepSeekShow[
  prompt_String,
  model_String: "deepseek-chat",
  temperature_: 0.2
] := AIShow @ AskDeepSeek[
  "请用适合 Wolfram Notebook Text 单元显示的纯文本回答。不要使用 Markdown 代码围栏。\n\n" <> prompt,
  model,
  temperature
];

ExplainMMAError[
  held_HoldForm,
  model_String: "glm-4-flash"
] := Module[{input, result, msgs, prompt},
  input = ToString[held, InputForm];

  Block[{$MessageList = {}},
    result = Quiet @ Check[ReleaseHold[held], $Failed];
    msgs = $MessageList;
  ];

  prompt =
    "请解释下面 Mathematica / Wolfram Language 输入为什么报错，并给出正确写法。\n\n" <>
    "输入：\n" <> input <> "\n\n" <>
    "返回值：\n" <> ToString[result, InputForm] <> "\n\n" <>
    "消息列表：\n" <> ToString[msgs, InputForm];

  AskGLMShow[prompt, model]
];

Print["Loaded direct LLM API wrappers: GLM + DeepSeek."];
```

### 3. 重启后测试

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

## 为什么这比直接用 App 有用

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

## 常见问题

### `ServiceConnect["DeepSeek"]` 总是引导 Wolfram Cloud 登录怎么办？

如果只是想用自己的 DeepSeek API key，可以不用 `ServiceConnect`，直接按上面的 `HTTPRequest` 方式调用 API。`ServiceConnect` 是 Wolfram 官方服务连接体系，适合走官方认证流程；直连 API 更适合自己控制 key、模型名和错误处理。

### 返回中文乱码怎么办？

优先检查请求体是否用字节方式导出：

```wl
ExportByteArray[body, "RawJSON"]
```

不要先 `ExportString` 再塞给 HTTP body。中文请求在 Wolfram 里被错误转码时，模型会收到乱码，回答自然会不对。

### 模型说自己不是我指定的版本，是否说明路由错了？

不一定。模型的自我介绍不可靠。判断实际路由要看 API 返回里的 `model` 字段：

```wl
GLMInspect["只输出 OK", "glm-4-flash"]["ReturnedModel"]
```

### 没有 LLM Kit 是否还能用 Local MCP？

Wolfram 官方 Local MCP 页面说明 Local MCP 面向已安装的 Wolfram 应用，Version 15 可直接开始使用，并且 Q&A 写明不需要额外订阅。LLM Kit 或 AI Access 的订阅边界主要影响 Wolfram 自己的 AI Assistant / Chat Notebook / LLM 功能，不要把它和外部 AI 调用本地 Wolfram 的 MCP 链路混在一起。

## 安全边界

- 不要把 API key 写进 `init.m` 或 Git 仓库；
- 如果 key 曾经发到聊天窗口或公开页面，直接去平台重置；
- 不要把未公开论文全文、审稿材料、私有数据直接交给外部模型；
- 只需要计算时给外部客户端 Computation Tools，确实要改代码时再给 Development Tools；
- 公开教程里不要出现真实用户名、真实本机路径、真实代理端口、真实账号状态截图。

## 参考

- [Wolfram AI Assistant](https://www.wolfram.com/ai-assistant/)
- [Wolfram AI Access Subscriptions](https://www.wolfram.com/ai-access/)
- [How do I set up Wolfram AI Access?](https://support.wolfram.com/67504)
- [LLMFunction 文档](https://reference.wolfram.com/language/ref/LLMFunction.html)
- [LLMConfiguration 文档](https://reference.wolfram.com/language/ref/LLMConfiguration.html)
- [DeepSeek Service Connection 文档](https://reference.wolfram.com/language/ref/service/DeepSeek.html)
- [Wolfram Local MCP](https://www.wolfram.com/artificial-intelligence/mcp/local/)
