# Local-TTS-ASR 项目 — 使用文档

## 简介

Local-TTS-ASR 是一个基于 Qwen3-TTS/ASR 系列模型的本地语音处理服务，提供 OpenAI 兼容的 TTS（文本转语音）和 ASR（自动语音识别）API，以及一个 React WebUI 用于交互式测试。支持 Apple Silicon (MLX) 和 NVIDIA GPU (PyTorch/CUDA) 两种本地推理后端，也支持远程转发到 Ollama/vLLM。

## 项目结构

```
local-tts-asr/
├── server/                    # Python 后端服务
│   ├── src/                   # 源代码
│   │   ├── main.py            # FastAPI 入口
│   │   ├── api/               # TTS / ASR API 路由
│   │   ├── core/              # 配置、模型加载
│   │   ├── engines/           # 本地 & 远程推理引擎
│   │   ├── schemas/           # Pydantic 数据模型
│   │   └── utils/             # 工具函数（音频、标点等）
│   ├── tests/                 # pytest 单元测试
│   ├── run.py                 # 启动脚本
│   ├── test_api.sh            # API 冒烟测试
│   ├── pyproject.toml         # Python 依赖（uv）
│   └── uv.lock                # 锁定文件
├── web-client/
│   └── frontend/              # React + Vite 前端 WebUI
│       ├── src/               # 前端源码（React + TypeScript）
│       ├── package.json       # Node.js 依赖
│       └── vite.config.ts     # Vite 配置
├── .gitignore
└── README.md
```

## 系统要求

| 项目 | 要求 |
|------|------|
| Python | >= 3.10 |
| Node.js | >= 18 (前端开发) |
| FFmpeg | 必需（音频标准化） |
| macOS | MLX 后端 (Apple Silicon) |
| Linux | CUDA 后端 (NVIDIA GPU) |

## 快速开始

### 1. 安装后端依赖

```bash
cd server

# 基础依赖（FastAPI、Pydantic 等）
uv sync

# MLX 后端（macOS Apple Silicon）
uv sync --extra mlx

# CUDA 后端（Linux NVIDIA GPU）
uv sync --extra cuda

# 开发依赖（pytest、httpx）
uv sync --extra dev
```

### 2. 配置环境变量

```bash
# 创建 .env 文件（如需要自定义配置）
touch server/.env
```

主要配置项：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PORT` | 8000 | API 服务端口 |
| `HOST` | 127.0.0.1 | API 服务地址 |
| `ENGINE_MODE` | local | 推理模式：local（本地）或 remote（远程转发） |
| `REMOTE_ENGINE_URL` | http://localhost:11434 | 远程 API 地址（ENGINE_MODE=remote 时使用） |
| `MODEL_SOURCE` | modelscope | 模型来源：modelscope 或 huggingface |
| `MODEL_CACHE_DIR` | （空） | 模型缓存目录（可选，默认使用各自库的默认路径） |
| `TTS_MODEL_PATH` | （空） | TTS 模型本地路径（为空则自动下载） |
| `ASR_MODEL_PATH` | （空） | ASR 模型本地路径（为空则自动下载） |
| `ALIGNER_MODEL_PATH` | （空） | ForcedAligner 模型本地路径（为空则自动下载） |

### 3. 启动后端服务

```bash
# 开发模式（自动重载）
cd server
python run.py

# 或指定端口和地址
PORT=8000 HOST=0.0.0.0 python run.py
```

> 也可使用 uvicorn 模块方式启动：
> ```bash
> cd server
> python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
> ```

服务启动后访问 `http://localhost:8000/docs` 可查看 OpenAPI 文档。

### 4. 启动前端 WebUI

```bash
cd web-client/frontend

npm install
npm run dev
```

前端开发服务器运行在 `http://localhost:5173`，自动将 `/v1` 请求代理到后端 `http://localhost:8000`。

### 5. API 健康检查

```bash
# 查看服务状态和引擎模式
curl http://localhost:8000/health

# 查看可用模型列表
curl http://localhost:8000/v1/models
```

## API 接口文档

### TTS — 文本转语音

**POST `/v1/audio/speech`**

生成语音音频。OpenAI 兼容接口，支持本地扩展（mode、voice、emotion）。

请求体 (JSON):

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `model` | string | 否 | `qwen3-tts` | 模型 ID |
| `input` | string | 是 | — | 要合成的文本 |
| `voice` | string | 条件 | — | 音色 ID（custom_voice 模式下必需） |
| `emotion` | string | 否 | — | 情绪/风格提示（custom_voice 模式） |
| `language` | string | 否 | `Auto` | 语言代码（Auto/Chinese/English/Japanese/Korean/German/French/Russian/Portuguese/Spanish/Italian） |
| `response_format` | string | 否 | `wav` | 输出格式：`wav` 或 `mp3` |
| `mode` | string | 否 | `custom_voice` | TTS 模式：`custom_voice`、`voice_clone`、`voice_design` |
| `ref_audio` | string | 条件 | — | 参考音频路径（voice_clone 模式下必需） |
| `ref_text` | string | 条件 | — | 参考音频文本（voice_clone 模式） |
| `instruct` | string | 条件 | — | 声音描述（voice_design 模式下必需） |

可用音色：`Vivian`, `Serena`, `Uncle_Fu`, `Dylan`, `Eric`, `Ryan`, `Aiden`, `Ono_Anna`, `Sohee`

响应：音频文件（WAV 或 MP3），Content-Type: `audio/wav` 或 `audio/mpeg`

**示例：**

```bash
# custom_voice 模式 — 使用内置音色
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "你好，世界！这是一个测试语音项目。", "voice": "Vivian", "mode": "custom_voice"}' \
  -o speech1.wav

# custom_voice 模式 — 英文，指定情绪
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello world, How Are you?", "voice": "Ryan", "emotion": "happy", "language": "English"}' \
  -o speech2.mp3

# voice_design 模式 — 根据描述生成声音
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "今天天气真好,适合出去走走看看。", "instruct": "温暖、温柔的年轻女性声音，语速偏慢"}' \
  -o speech3.wav

# voice_clone 模式 — 使用参考音频克隆声音
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "这是一段克隆的声音", "mode": "voice_clone", "ref_audio": "/path/to/ref.wav", "ref_text": "今天天气真好,适合出去走走看看。"}' \
  -o speech4.wav
```

### ASR — 语音识别

**POST `/v1/audio/transcriptions`**

将音频转录为文本。支持多种响应格式。

请求 (multipart/form-data):

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `file` | file | 是 | — | 音频文件（任意 FFmpeg 支持的格式） |
| `model` | string | 否 | `qwen3-asr` | 模型 ID |
| `response_format` | string | 否 | `text` | 响应格式：`text`、`json`、`verbose_json` |
| `language` | string | 否 | — | 指定语言（可选，帮助提高识别准确率） |

响应格式：

**text (默认):** 纯文本
```
你好，世界！
```

**json:**
```json
{"text": "你好，世界！"}
```

**verbose_json:**
```json
{
  "text": "你好，世界！",
  "language": "Chinese",
  "duration": 3.5,
  "segments": [
    {"start": 0.12, "end": 0.45, "word": "你好"},
    {"start": 0.56, "end": 1.23, "word": "世界"}
  ]
}
```

**示例：**

```bash
# 转录为纯文本（默认）
curl -X POST http://localhost:8000/v1/audio/transcriptions \
  -F "file=@audio.mp3" \
  -o transcription.txt

# 转录为 JSON（仅文本）
curl -X POST http://localhost:8000/v1/audio/transcriptions \
  -F "file=@audio.mp3" \
  -F "response_format=json"

# 转录为详细 JSON（含时间戳）
curl -X POST http://localhost:8000/v1/audio/transcriptions \
  -F "file=@audio.mp3" \
  -F "response_format=verbose_json" \
  | python3 -m json.tool

# 指定中文语言
curl -X POST http://localhost:8000/v1/audio/transcriptions \
  -F "file=@audio.mp3" \
  -F "language=Chinese" \
  -F "response_format=json"
```

### Alignment — 字词级对齐

**POST `/v1/audio/alignment`**

返回音频的字词级时间戳信息。

请求 (multipart/form-data):

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | file | 是 | 音频文件 |
| `language` | string | 否 | 指定语言 |

响应：JSON，包含 `text`, `language`, `duration`, `words` 字段。

```json
{
  "text": "你好，世界！",
  "language": "Chinese",
  "duration": 3.5,
  "words": [
    {"word": "你好", "start": 0.12, "end": 0.45},
    {"word": "世界", "start": 0.56, "end": 1.23}
  ]
}
```

**示例：**

```bash
# 获取字词级时间戳
curl -X POST http://localhost:8000/v1/audio/alignment \
  -F "file=@audio.mp3" \
  | python3 -m json.tool

# 指定中文语言
curl -X POST http://localhost:8000/v1/audio/alignment \
  -F "file=@audio.mp3" \
  -F "language=Chinese" \
  | python3 -m json.tool
```

### 其他端点

**GET `/v1/models`** — 列出可用模型（OpenAI 兼容）

```bash
curl http://localhost:8000/v1/models | python3 -m json.tool
```

响应：
```json
{
  "data": [
    {"id": "qwen3-tts-1.7B", "object": "model"},
    {"id": "qwen3-asr-1.7B", "object": "model"}
  ],
  "object": "list"
}
```

**GET `/health`** — 健康检查

```bash
curl http://localhost:8000/health | python3 -m json.tool
```

响应：
```json
{"status": "ok", "engine_mode": "local"}
```

## 推理模式说明

### Local 模式（默认）

在本地运行 Qwen3-TTS 和 Qwen3-ASR 模型。根据平台自动选择后端：

| 平台 | 后端 | 依赖包 |
|------|------|--------|
| macOS (Apple Silicon) | MLX | `mlx-audio`, `mlx-lm` |
| Linux (NVIDIA GPU) | PyTorch/CUDA | `torch` |

模型首次使用时会自动从 ModelScope 或 HuggingFace 下载。支持的模型：

- **TTS**: Qwen3-TTS-12Hz-1.7B (custom_voice / voice_clone 两种模式)
- **ASR**: Qwen3-ASR-0.6B / 1.7B
- **Aligner**: Qwen3-ForcedAligner-0.6B

### Remote 模式

将请求转发到远程 OpenAI 兼容 API（如 Ollama、vLLM）。

设置 `ENGINE_MODE=remote` 和 `REMOTE_ENGINE_URL=http://your-api:port`。

## WebUI 使用

启动前端后访问 `http://localhost:5173`，包含三个 Tab：

### TTS 合成

- 输入文本
- 选择音色（9 种内置音色）
- 选择情绪风格
- 选择语言
- 点击"生成语音"，结果直接在页面播放

### ASR 转录

- 上传音频文件
- 点击"开始转录"
- 显示转录文本和字词级时间戳

### 设置

- 查看当前后端运行模式
- 配置远程 API URL（remote 模式下）
- 设置保存到本地存储，需要重启后端服务生效

## 故障排查

### 模型下载失败

```bash
# 切换到 HuggingFace（国内网络不稳定时）
MODEL_SOURCE=huggingface

# 指定缓存目录
MODEL_CACHE_DIR=/path/to/cache
```

### FFmpeg 未安装

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# 验证安装
ffmpeg -version
```

### MLX 后端不可用

确认使用的是 Apple Silicon Mac（M1/M2/M3/M4），Intel Mac 不支持 MLX。

### CUDA 后端不可用

确认 NVIDIA GPU 驱动和 CUDA Toolkit 已正确安装。

### 端口被占用

修改 `.env` 中的 `PORT`，或 kill 占用端口的进程：
```bash
lsof -ti:8000 | xargs kill
```

## 测试

```bash
cd server

# 运行所有单元测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_config.py -v

# 带覆盖率
pytest tests/ -v --cov=src --cov-report=term-missing

# API 冒烟测试（需先启动服务）
bash test_api.sh
```
