---
name: stratigraphic-dictionary
description: 地层分层字典可视化编辑工具，提供地层结构的手动标定、编辑和数据导出功能。当用户需要处理地层分层数据、创建地层字典或进行地层可视化编辑时使用此技能。支持命令行预加载数据、CSV文件上传、地层边界拖拽调整、实时预览和数据导出。使用场景包括：(1) 地质勘探中的地层标定，(2) 科研教学中的地层可视化，(3) 地层数据标准化处理，(4) 建立企业地层知识库。
---

# 地层分层字典工具

## 概述

地层分层字典工具是一个基于Web的可视化编辑系统，帮助地质工作者快速创建和编辑地层分层数据。提供直观的拖拽界面来调整地层边界，支持实时预览和数据导出功能。

## 环境准备

### 步骤1：检查uv环境

检查系统是否已安装uv：
```bash
uv --version
```

如果提示"uv"不是内部或外部命令，说明未安装uv，请按以下步骤安装：

**安装uv（Windows）：**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**安装uv（Linux/macOS）：**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

安装完成后，重新打开终端并验证：
```bash
uv --version
```

### 步骤2：检查虚拟环境

在项目根目录下检查是否存在`.venv`虚拟环境：
```bash
ls .venv
```

如果不存在，创建虚拟环境：
```bash
uv venv --python 3.11 .venv
```

### 步骤3：检查依赖包

检查是否已安装所需的依赖包：
```bash
uv pip list
```

确认输出中包含以下包：
- flask
- pandas
- numpy

如果缺少依赖，安装所需包：
```bash
uv pip install flask pandas numpy
```

## 快速启动参考

### 完整功能测试
```bash
uv run ".windsurf\skills\stratigraphic-dictionary\scripts\start_server.py" -m "地层分层.csv" -d "stratigraphic_depth_statistics.csv"
```

### 仅预加载数据进行编辑
```bash
uv run ".windsurf\skills\stratigraphic-dictionary\scripts\start_server.py" -d "stratigraphic_depth_statistics.csv"
```

### 手动上传模式
```bash
uv run ".windsurf\skills\stratigraphic-dictionary\scripts\start_server.py" -m "地层分层.csv"
```
或
```bash
uv run ".windsurf\skills\stratigraphic-dictionary\scripts\start_server.py"
```


## 核心功能

### 1. 启动地层编辑服务

```bash
# 正常模式
uv run ".windsurf\skills\stratigraphic-dictionary\scripts\start_server.py"

# 加载地层分层参考文件
uv run ".windsurf\skills\stratigraphic-dictionary\scripts\start_server.py" -m "地层分层.csv"

# 预加载数据文件（网页打开后立即显示）
uv run ".windsurf\skills\stratigraphic-dictionary\scripts\start_server.py" -d "stratigraphic_depth_statistics.csv"

# 同时加载两个文件
uv run ".windsurf\skills\stratigraphic-dictionary\scripts\start_server.py" -m "地层分层.csv" -d "stratigraphic_depth_statistics.csv"

# 查看所有参数
uv run ".windsurf\skills\stratigraphic-dictionary\scripts\start_server.py" --help
```

**命令行参数说明：**
- `-m, --stratigraphy` : 地层分层参考CSV文件路径（包含地层信息列）
- `-d, --data` : 预加载的地层数据CSV文件路径（包含地层名称、所属层位等列）
- `--host` : 服务器地址（默认：127.0.0.1）
- `--port` : 服务器端口（默认：5000）
- `--debug` : 启用调试模式

服务启动后会自动打开浏览器访问 http://127.0.0.1:5000

### 2. 数据准备

#### 必需文件：地层深度统计数据
用户需要准备一个CSV文件，包含以下表头：
- `地层名称` - 地层的具体名称
- `所属层位` - 地层所属的大类层位
- `顶界所处位置（0~1）` - 地层顶部相对位置（0-1之间）
- `底界所处位置（0~1）` - 地层底部相对位置（0-1之间）

#### 可选文件：地层分层参考文件
可以提供一个 `地层分层.csv` 文件来定义地层的标准顺序，包含：
- `序号` - 地层序号
- `地层信息` - 地层名称

**注意：** 地层分层.csv文件应放在项目根目录下，不需要包含在skill中。

### 3. 智能数据加载

#### 步骤1：启动服务
运行 `uv run ".windsurf\skills\stratigraphic-dictionary\scripts\start_server.py" -d "数据文件.csv"`
等待服务启动并自动打开浏览器

#### 步骤2：自动检测和加载
1. **页面自动检测**：页面打开时自动检查预加载数据
2. **智能加载**：发现预加载数据后立即显示地层结构
3. **状态提示**：右上角显示"✅ 已自动加载预加载数据！"通知
4. **无需手动操作**：直接进入可视化编辑界面

#### 步骤3：编辑地层
1. **拖拽调整**：拖拽地层条的两端来调整顶界和底界位置
2. **双击编辑**：双击地层条打开编辑弹窗，修改地层属性
3. **添加地层**：点击"添加小层"按钮创建新的地层条目
4. **展开地层**：点击"展开地层"按钮查看详细层级结构

#### 步骤4：导出数据
1. 完成编辑后点击"导出数据"按钮
2. 系统会在项目根目录的 `uploads` 文件夹中生成 `{原文件名}_verification.csv` 文件
3. 导出文件包含编辑后的完整地层分层数据

## 技术特性

### 可视化编辑
- 基于D3.js的交互式地层可视化
- 支持拖拽调整地层边界
- 实时预览地层结构变化
- 颜色编码区分不同层位

### 数据处理
- 自动验证CSV文件格式
- 支持地层顺序标准化
- 数据完整性检查
- UTF-8编码支持

### 用户体验
- 响应式Web界面
- 直观的拖拽操作
- 实时状态提示
- 错误处理和用户反馈

## 文件结构

```
stratigraphic-dictionary/
├── scripts/
│   └── start_server.py          # Flask服务器启动脚本
├── assets/
│   ├── stratigraphic_visualizer.html  # 前端HTML页面
│   ├── stratigraphic_styles.css       # 样式文件
│   └── stratigraphic_interactions.js  # 交互逻辑
└── SKILL.md                       # 技能说明文档
```

## 使用场景

### 地质勘探
- 创建标准化的地层分层字典
- 标定钻井地层的精确位置
- 建立区域地层对比标准

### 科研教学
- 地层结构可视化演示
- 地质数据教学工具
- 学生实践操作平台

### 数据管理
- 地层数据标准化处理
- 建立企业地层知识库
- 地层数据质量控制

## 依赖要求

确保系统已安装以下Python包：
- Flask >= 3.1.2
- pandas >= 2.3.3
- numpy >= 1.26.4

## 故障排除

### 常见问题

1. **端口占用**：如果5000端口被占用，修改启动参数 `--port 8080`
2. **文件编码**：确保CSV文件使用UTF-8编码保存
3. **数据格式**：检查CSV文件是否包含必需的表头列
4. **浏览器兼容**：建议使用现代浏览器（Chrome、Firefox、Safari）
5. **预加载失败**：使用绝对路径确保文件能被找到
6. **导出404错误**：检查uploads目录权限和路径配置

### 错误处理
- 文件上传失败：检查文件格式和大小限制
- 数据解析错误：验证CSV文件格式和必需列
- 服务启动失败：检查Python环境和依赖包
- 预加载数据不显示：检查控制台日志和文件路径

## 最佳实践

### 数据准备
1. **数据准备**：确保CSV文件数据准确，位置值在0-1范围内
2. **分层参考**：使用标准的地层分层文件确保一致性
3. **绝对路径**：使用绝对路径避免相对路径问题
4. **文件编码**：统一使用UTF-8编码

### 工作流程
1. **预加载模式**：使用 `-d` 参数预加载数据提高效率
2. **参考文件**：使用 `-m` 参数加载地层分层参考文件
3. **定期备份**：重要地层数据建议定期备份
4. **版本控制**：对导出的数据进行版本管理

### 性能优化
1. **批量处理**：一次性加载多个文件进行批量编辑
2. **内存管理**：大型数据集建议分批处理
3. **浏览器优化**：关闭不必要的标签页释放内存
