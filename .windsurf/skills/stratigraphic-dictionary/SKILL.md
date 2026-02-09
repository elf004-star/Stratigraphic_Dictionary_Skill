---
name: stratigraphic-dictionary
description: 地层分层字典可视化编辑工具，提供地层结构的手动标定、编辑和数据导出功能。当用户需要处理地层分层数据、创建地层字典或进行地层可视化编辑时使用此技能。支持命令行预加载数据、CSV文件上传、地层边界拖拽调整、实时预览和数据导出。使用场景包括：(1) 地质勘探中的地层标定，(2) 科研教学中的地层可视化，(3) 地层数据标准化处理，(4) 建立企业地层知识库。
---

# 地层分层字典工具

基于Web的可视化编辑系统，帮助地质工作者快速创建和编辑地层分层数据。

## 快速开始

### 启动服务

```bash
# 基础启动
python scripts/start_server.py

# 加载地层分层参考文件
python scripts/start_server.py -m "地层分层.csv"

# 预加载地层数据文件
python scripts/start_server.py -d "stratigraphic_depth_statistics.csv"

# 同时加载参考文件和数据文件
python scripts/start_server.py -m "地层分层.csv" -d "stratigraphic_depth_statistics.csv"
```

### 使用uv运行

```bash
uv run scripts/start_server.py [参数]
```

### 命令行参数

- `-m, --stratigraphy` : 地层分层参考CSV文件路径（包含地层信息列）
- `-d, --data` : 预加载的地层数据CSV文件路径（包含地层名称、所属层位等列）
- `--host` : 服务器地址（默认：127.0.0.1）
- `--port` : 服务器端口（默认：5000）
- `--debug` : 启用调试模式

服务启动后访问 http://127.0.0.1:5000

## 核心功能

### 1. 智能数据加载

- 通过 `-d` 参数预加载数据，打开网页自动显示
- 支持手动上传CSV文件
- 自动验证数据格式

### 2. 可视化编辑

- **拖拽调整**：拖拽地层条两端调整顶界/底界位置
- **双击编辑**：双击地层条修改属性
- **添加地层**：点击"添加小层"创建新条目
- **展开地层**：查看详细层级结构

### 3. 数据导出

编辑完成后点击"导出数据"，文件保存在 `uploads/{原文件名}_verification.csv`

## 数据格式

### 必需的数据文件格式

CSV文件需包含以下列：

| 列名 | 说明 | 示例 |
|------|------|------|
| 地层名称 | 地层具体名称 | 沙溪庙组底部 |
| 所属层位 | 地层所属大类 | 沙溪庙组 |
| 顶界所处位置（0~1） | 顶部相对位置 | 0.00 |
| 底界所处位置（0~1） | 底部相对位置 | 0.25 |

详细格式说明见 [references/data_format.md](references/data_format.md)

### 可选的地层分层参考文件

用于定义标准地层顺序：

| 列名 | 说明 | 示例 |
|------|------|------|
| 序号 | 地层序号 | 1 |
| 地层信息 | 地层名称 | 沙溪庙组 |

## 文件结构

```
stratigraphic-dictionary/
├── SKILL.md                          # 本文件
├── scripts/
│   └── start_server.py              # Flask服务器启动脚本
├── assets/
│   ├── stratigraphic_visualizer.html  # 前端HTML页面
│   ├── stratigraphic_styles.css       # 样式文件
│   └── stratigraphic_interactions.js  # 交互逻辑
└── references/
    ├── data_format.md                 # 数据格式详细说明
    └── sample_data.csv                # 示例数据文件
```

## 依赖要求

- Python 3.11+
- Flask >= 3.1.2
- pandas >= 2.3.3
- numpy >= 1.26.4

安装依赖：

```bash
uv pip install flask pandas numpy
```

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| 端口占用 | 使用 `--port 8080` 更换端口 |
| 文件编码 | 确保CSV使用UTF-8编码 |
| 数据格式错误 | 检查必需列是否完整 |
| 预加载失败 | 使用绝对路径或确认文件存在 |

## 参考资料

- **数据格式详细说明**：[references/data_format.md](references/data_format.md)
- **示例数据文件**：[references/sample_data.csv](references/sample_data.csv)
