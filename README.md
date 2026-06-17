# 角色构建与 AstrBot 部署管线

从轻小说文本构建可部署的角色人格：候选场景提取、LLM 分析批次、角色圣经、RAG 知识库、AstrBot 人格注入。

当前内置角色：

- `yanami` — 八奈见杏菜，《敗北女角太多了！》

## 项目结构

```text
character/
├── character.py                    # 角色构建入口：init/build/package/status/list
├── characters/
│   └── yanami/
│       ├── character.json           # 角色配置
│       ├── system_prompt.md         # AstrBot 人格 prompt
│       ├── full_knowledge.md        # 完整 RAG 知识库
│       ├── rag.md                   # 精简 RAG 知识库
│       ├── ooc_checklist.md
│       └── ooc_eval_report.md
├── data/
│   ├── novels/                      # 用户放小说文本；不会提交到仓库
│   └── extracted/<character_id>/     # 每个角色的构建产物
├── prompts/
│   ├── extract_character_scene.md    # 通用场景抽取 prompt 模板
│   └── build_character_profile.md    # 通用角色汇总 prompt 模板
├── deploy/
│   └── deploy.py                     # AstrBot 部署入口
└── scripts/                          # 历史/辅助脚本
```

## 前置条件

- AstrBot 4.x 已部署并完成基础配置。
- AstrBot 已配置 AI 对话模型和平台机器人，例如 QQ。
- Python 3.10+。
- 一个支持 OpenAI 兼容 Embedding API 的服务，用于知识库向量化。

如果还没有部署 AstrBot，请先看官方文档：

```text
https://docs.astrbot.app/deploy/astrbot/cli.html
```

## 使用已有角色

列出角色：

```bash
python character.py list
```

部署默认角色。如果只有一个角色，会直接部署；多个角色时会提示选择：

```bash
python deploy/deploy.py
```

部署指定角色：

```bash
python deploy/deploy.py --character yanami
```

模拟部署，不写数据库：

```bash
python deploy/deploy.py --character yanami --dry-run
```

部署脚本会做：

- 检测 AstrBot 数据目录
- 注入或更新角色人格
- 设置默认人格
- 提示上传对应知识库

部署脚本不会做：

- 安装 AstrBot
- 创建 QQ 机器人
- 申请 API Key
- 自动上传知识库文档
- 自动配置 Embedding Provider

## 创建新角色

目标是让用户只做两件事：

1. 把小说文本放到 `data/novels/`
2. 提供角色 ID、显示名、作品名、别名

其余候选场景、批次、prompt、部署文件都由代码生成。

### 方式一：交互式向导

```bash
python character.py wizard
```

向导会询问：

- 角色 ID，例如 `lemon`
- 显示名，例如 `烧盐柠檬`
- 作品名
- 角色可能出现的名字/别名，例如 `烧盐,烧盐柠檬,柠檬,Lemon`
- 小说文件路径

### 方式二：命令行初始化

```bash
python character.py init ^
  --character lemon ^
  --display-name 烧盐柠檬 ^
  --work-name 敗北女角太多了！ ^
  --aliases 烧盐,烧盐柠檬,柠檬,Lemon ^
  --source-files data/novels/your_novel.txt
```

初始化会生成：

```text
characters/lemon/character.json
```

### 构建候选场景和批次

```bash
python character.py build --character lemon
```

这一步会自动生成：

```text
data/extracted/lemon/candidate_scenes.jsonl
data/extracted/lemon/candidate_preview.md
data/extracted/lemon/batches/
data/extracted/lemon/prompts/extract_scene.md
data/extracted/lemon/prompts/build_profile.md
```

> ⚠️ **这一步是必须的，不可跳过。** 候选场景只是原始文本片段，必须经过 LLM 分析才能变成结构化角色数据。仓库没有内置自动调 LLM 的功能，你需要：
>
> 1. 找一个支持批量对话的 LLM 客户端（Claude Code、OpenAI API、或其他）
> 2. 把 `prompts/extract_scene.md` 和 `batches/` 下的每个批次喂给 LLM
> 3. 收集输出合并成 `scene_analysis.jsonl`
> 4. 把 `prompts/build_profile.md` 和 `scene_analysis.jsonl` 喂给 LLM，得到 `profile.md`

你也可以跳过整个管线，自己手写 `system_prompt.md` 和 `full_knowledge.md` 放到 `characters/lemon/` 下，直接执行部署步骤。

期望产物：

```text
data/extracted/lemon/scene_analysis.jsonl
data/extracted/lemon/profile.md
```

### 打包部署文件

当 `scene_analysis.jsonl` 和 `profile.md` 准备好后：

```bash
python character.py package --character lemon
```

这一步会生成：

```text
characters/lemon/system_prompt.md
characters/lemon/full_knowledge.md
characters/lemon/rag.md
characters/lemon/ooc_checklist.md
characters/lemon/ooc_eval_report.md
```

然后部署：

```bash
python deploy/deploy.py --character lemon
```

## 部署后的手工步骤

部署脚本执行完成后，还需要完成以下步骤：

### 1. 配置 Embedding Provider

进 AstrBot 仪表盘 → **模型提供商** → **嵌入** → **新增模型提供商**，选 **OpenAI Compatible**：

| 配置项 | 值 |
|--------|-----|
| API Base URL | `https://api.siliconflow.cn/v1` |
| Model | `BAAI/bge-m3` |
| API Key | 去 [SiliconFlow](https://siliconflow.cn) 注册获取（免费额度够用） |

### 2. 上传知识库文档

仪表盘 → **知识库** → **新建**

- 名称建议使用 `character.json` 里的 `knowledge_base_name`
- 选刚配好的 Embedding 模型 → 保存
- 进入知识库详情 → **上传文档**
- 选 `characters/<角色ID>/full_knowledge.md`（完整版）
- 或先用 `characters/<角色ID>/rag.md`（精简版）测试

### 3. 重启 AstrBot

## 构建状态

查看某个角色的构建状态：

```bash
python character.py status --character lemon
```

## 当前边界

- 多角色部署已配置化。
- 角色候选场景提取和批次生成已配置化。
- LLM 批量分析仍需要外部执行器或人工批处理；仓库会生成所需 prompt 和 batch 文件。
- 历史脚本中仍有部分 `yanami_*` 文件名，用于八奈见既有数据，不建议作为新角色入口；新角色请使用 `character.py`。

## 许可证

MIT License

## 免责声明

所有角色分析数据基于用户提供文本的结构化提取。角色版权归原作者及出版社。本项目仅用于技术研究和学习。
