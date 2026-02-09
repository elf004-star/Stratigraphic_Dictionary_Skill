---
name: stratigraphic-dictionary
description: 地层分层字典可视化编辑工具，提供从钻井数据提取地层、可视化编辑到JSON字典生成的完整工作流。当用户需要处理地层分层数据、创建地层字典、分析钻井数据中的地层信息或进行地层可视化编辑时使用此技能。支持命令行预加载数据、CSV文件上传、地层边界拖拽调整、实时预览和数据导出。使用场景包括：(1) 从钻井数据提取地层信息，(2) 地质勘探中的地层标定，(3) 科研教学中的地层可视化，(4) 建立企业地层知识库。
---

# 地层分层字典工具

基于Web的可视化编辑系统，帮助地质工作者快速从钻井数据中提取、编辑和管理地层分层数据。

## 快速开始

### 完整工作流（推荐）

一键完成从钻井数据到JSON字典的完整流程：

```bash
# 完整工作流：提取 → 编辑 → 导出JSON
python scripts/workflow_manager.py -d "CCQ_merged.csv" -m "地层分层.csv"

# 使用现有配置更新字典
python scripts/workflow_manager.py -d "CCQ_merged.csv" -m "地层分层.csv" -c "stratigraphic_dictionary.json"
```

工作流会自动：
1. 从钻井数据提取地层深度统计
2. 启动可视化编辑器
3. 等待用户编辑完成（导出数据到uploads）
4. 自动转换为JSON字典保存到根目录

### 分步执行（高级）

如需单独执行某一步骤：

**仅提取地层数据：**
```bash
python scripts/workflow_manager.py extract -d "CCQ_merged.csv" -s "地层分层.csv"
```

**仅启动可视化编辑器：**
```bash
uv run scripts/start_server.py -m "地层分层.csv" -d "stratigraphic_depth_statistics.csv"
```

**仅转换CSV到JSON：**
```bash
python scripts/workflow_manager.py convert
# 或指定具体文件
python scripts/workflow_manager.py convert -f "uploads/stratigraphic_depth_statistics_verification.csv"
```

## 环境准备

**⚠️ 重要：启动服务前必须完成以下环境检查**

1. **检查uv环境**

   ```bash
   uv --version
   ```

   如果显示版本号，说明uv已安装。如果提示命令不存在，请先安装uv：

   **Windows安装uv：**
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   **Linux/macOS安装uv：**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **检查虚拟环境**

   在项目根目录检查是否存在`.venv`目录：
   
   ```bash
   # Windows
   dir .venv
   
   # Linux/macOS
   ls -la .venv
   ```

   如果不存在，创建虚拟环境：
   ```bash
   uv venv --python 3.11 .venv
   ```

3. **检查依赖包**

   ```bash
   uv pip list | findstr flask
   ```

   如果缺少依赖，安装所需包：
   ```bash
   uv pip install flask pandas numpy
   ```

## 数据文件格式

### 输入文件1：钻井数据（如CCQ_merged.csv）

| 列名 | 说明 | 示例 |
|------|------|------|
| 起始地层 | 起始地层名称 | 沙溪庙组 |
| 结束地层 | 结束地层名称 | 须家河组 |
| 起始井深 | 起始深度(m) | 1003.0 |
| 结束井深 | 结束深度(m) | 2333.5 |

### 输入文件2：地层分层参考（如地层分层.csv）

| 列名 | 说明 | 示例 |
|------|------|------|
| 序号 | 地层顺序 | 1 |
| 地层信息 | 地层名称 | 沙溪庙组 |
| 地层顶深 | 顶部深度(m) | 0 |
| 地层底深 | 底部深度(m) | 1668 |

### 输出JSON格式

```json
{
  "沙溪庙组底部": {
    "所属层位": "沙溪庙组",
    "顶界所处位置（0~1）": "0.00",
    "底界所处位置（0~1）": "0.25"
  }
}
```

## 核心功能

### 1. 智能地层提取

从钻井记录自动统计每个地层的深度范围：
- 计算最大/最小/平均深度
- 统计出现频次
- 根据地层分层参考确定所属层位
- 支持增量更新（保留已有配置）

### 2. 可视化编辑

浏览器中直观编辑地层数据：
- **拖拽调整**：拖拽地层条两端调整顶界/底界位置
- **双击编辑**：双击地层条修改属性
- **添加地层**：点击"添加小层"创建新条目
- **展开地层**：查看详细层级结构

### 3. 数据导出与转换

编辑完成后：
- 点击"导出数据"保存到 `uploads/{原文件名}_verification.csv`
- 自动/手动转换为JSON字典
- 支持合并到现有字典

## 命令行参考

### workflow_manager.py（完整工作流）

```
参数：
  -d, --data-file        钻井数据文件路径（必需）
  -m, --stratigraphy-file 地层分层参考文件路径（必需）
  -c, --config-file      现有JSON配置文件路径（可选）
  --analysis-output      分析输出CSV文件名
  --json-output          JSON输出文件名
  --host, --port         服务器地址和端口

子命令：
  extract   仅执行地层数据提取
  convert   仅执行CSV到JSON转换
```

### start_server.py（可视化编辑器）

```
参数：
  -m, --stratigraphy    地层分层参考CSV
  -d, --data           预加载的地层数据CSV
  --host               服务器地址（默认：127.0.0.1）
  --port               服务器端口（默认：5000）
  --debug              启用调试模式
```

## 典型使用场景

### 场景1：首次创建地层字典

```bash
# 1. 运行完整工作流
python scripts/workflow_manager.py -d "CCQ_merged.csv" -m "地层分层.csv"

# 2. 在浏览器中编辑地层数据
# 3. 点击导出，JSON自动生成
```

### 场景2：更新现有字典

```bash
# 使用现有JSON作为配置，只添加新地层
python scripts/workflow_manager.py -d "新数据.csv" -m "地层分层.csv" -c "stratigraphic_dictionary.json"
```

### 场景3：手动调整并导出

```bash
# 1. 启动编辑器
uv run scripts/start_server.py -m "地层分层.csv" -d "现有数据.csv"

# 2. 浏览器中编辑并导出

# 3. 转换为JSON
python scripts/workflow_manager.py convert -f "uploads/xxx_verification.csv" -o "output.json"
```

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| 端口占用 | 使用 `--port 8080` 更换端口 |
| 找不到uploads文件 | 确保先点击"导出数据"按钮 |
| 转换失败 | 检查CSV格式，确保包含必需列 |
| 地层提取错误 | 确认钻井数据包含起始/结束地层列 |
| 预加载失败 | 使用绝对路径或确认文件存在 |

## 文件结构

```
stratigraphic-dictionary/
├── SKILL.md                          # 本文件
├── scripts/
│   ├── start_server.py              # Flask服务器
│   └── workflow_manager.py          # 完整工作流管理器
├── assets/
│   ├── stratigraphic_visualizer.html
│   ├── stratigraphic_styles.css
│   └── stratigraphic_interactions.js
└── references/
    └── data_format.md               # 数据格式详细说明
```

## 依赖要求

- Python 3.11+
- Flask >= 3.1.2
- pandas >= 2.3.3
- numpy >= 1.26.4

安装：
```bash
uv pip install flask pandas numpy
```
