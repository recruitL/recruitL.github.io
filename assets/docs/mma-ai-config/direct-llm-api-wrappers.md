# Direct LLM API wrappers for Mathematica `init.m`

这是《MMA 15 AI 配置流程：AI Assistant、Local MCP 与直连 API》的配套脱敏模板，用来放进 Wolfram Language 的 `init.m`。

建议位置：

```wl
FileNameJoin[{$UserBaseDirectory, "Kernel", "init.m"}]
```

API key 不写进 `init.m`，而是放在：

```text
$UserBaseDirectory/Private/glm_key.txt
$UserBaseDirectory/Private/deepseek_key.txt
```

完整模板如下：

```wl
(* ::Package:: *)

(* ========================================================= *)
(*  User init.m: Direct LLM API wrappers                     *)
(*  Providers: GLM / DeepSeek                                *)
(*  Keys are read from $UserBaseDirectory/Private/.           *)
(* ========================================================= *)

(* Optional proxy. Uncomment and edit only when needed.
$DefaultProxyRules["UseProxy"] = Manual;
$DefaultProxyRules["HTTP"] = {"<PROXY_HOST>", <PROXY_PORT>};
$DefaultProxyRules["HTTPS"] = {"<PROXY_HOST>", <PROXY_PORT>};
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


ClearAll[
  AITextNormalize, AIShow,
  AskGLMShow, AskDeepSeekShow,
  DeepSeekBubbleChat, ExplainMMAError
];

AITextNormalize[s_String] := StringReplace[
  s,
  {
    "\\n" -> "\n",
    "\\t" -> "\t",
    "\r\n" -> "\n",
    "```mathematica" -> "",
    "```wolfram" -> "",
    "```wl" -> "",
    "```" -> ""
  }
];

AITextNormalize[x_] := ToString[x, InputForm];

AIShow[s_String, style_String: "Text"] := (
  CellPrint[Cell[AITextNormalize[s], style]];
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

DeepSeekBubbleChat[] := CreatePalette[
  DynamicModule[
    {
      input = "",
      model = "deepseek-chat",
      busy = False,
      msgs = {}
    },
    Column[
      {
        Row[
          {
            Style["DeepSeek Local Chat", 16, Bold],
            Spacer[20],
            "模型：",
            PopupMenu[
              Dynamic[model],
              {
                "deepseek-chat" -> "deepseek-chat",
                "deepseek-reasoner" -> "deepseek-reasoner"
              }
            ]
          }
        ],
        Dynamic[
          Pane[
            Column[
              Flatten @ Map[
                {
                  Framed[
                    Style[#["User"], 14],
                    Background -> RGBColor[0.93, 0.97, 1.0],
                    FrameStyle -> RGBColor[0.70, 0.85, 0.95],
                    RoundingRadius -> 8,
                    ImageMargins -> List[List[80, 5], List[5, 5]],
                    FrameMargins -> 10
                  ],
                  Framed[
                    Style[AITextNormalize[#["Assistant"]], 14],
                    Background -> RGBColor[0.96, 0.96, 0.96],
                    FrameStyle -> RGBColor[0.85, 0.85, 0.85],
                    RoundingRadius -> 8,
                    ImageMargins -> List[List[5, 80], List[5, 12]],
                    FrameMargins -> 10
                  ]
                } &,
                msgs
              ],
              Spacings -> 0.8
            ],
            {520, 420},
            Scrollbars -> True
          ]
        ],
        Dynamic[If[busy, Style["正在发送...", Gray], ""]],
        Row[
          {
            InputField[
              Dynamic[input],
              String,
              FieldSize -> {45, 3},
              ContinuousAction -> False
            ],
            Button[
              "发送",
              If[StringTrim[input] =!= "",
                busy = True;
                Module[{q = input, ans},
                  input = "";
                  ans = DeepSeekChat[q, model];
                  AppendTo[msgs, <|"User" -> q, "Assistant" -> ans|>];
                ];
                busy = False;
              ],
              Method -> "Queued",
              ImageSize -> {70, 50}
            ]
          }
        ],
        Row[
          {
            Button["清空窗口", msgs = {};],
            Button[
              "清空上下文",
              DeepSeekClear[];
              msgs = {};
            ]
          }
        ]
      },
      Spacings -> 1
    ]
  ],
  WindowTitle -> "DeepSeek Local Chat",
  WindowSize -> {620, 620}
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
