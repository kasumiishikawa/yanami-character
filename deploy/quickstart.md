# 快速上手

## 0. 先准备 AstrBot

本项目不负责安装 AstrBot 本体，也不负责创建 QQ/Telegram/飞书等平台机器人。

请先完成：

- 部署 AstrBot 官方程序：[通过源码部署 AstrBot](https://docs.astrbot.app/deploy/astrbot/cli.html)
- 打开 AstrBot 管理面板，通常是 `http://localhost:6185`
- 在快速引导中完成“配置 AI 模型”
- 在快速引导中完成“配置平台机器人”

这些完成后，再运行本项目的部署脚本。

## 1. 运行部署脚本

```bash
python deploy/deploy.py
```

脚本会检测 AstrBot 数据目录，并把 `deploy/system_prompt.md` 注入为“八奈见杏菜”人格。重复运行会更新已有人格。

脚本不会自动申请 API Key、不会自动接入 QQ，也不会自动上传知识库。

## 2. 配置 Embedding

在 AstrBot 仪表盘中新增一个 Embedding Provider：

- 类型：OpenAI Compatible
- API Base URL：`https://api.siliconflow.cn/v1`
- Model：`BAAI/bge-m3`
- API Key：使用你自己的 Key

## 3. 上传知识库

进入 AstrBot 知识库页面，新建知识库并选择刚配置的 Embedding Provider，然后上传：

```text
deploy/yanami_full_knowledge.md
```

如果想先快速测试，可以上传：

```text
deploy/yanami_rag.md
```

## 4. 重启 AstrBot

配置和知识库导入完成后，重启 AstrBot，再从 QQ 侧测试对话。
