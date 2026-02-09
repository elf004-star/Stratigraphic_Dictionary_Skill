# 地层分层字典可视化编辑工具 - 使用说明

## 🚀 快速开始

### 完整功能测试（推荐）
```bash
python ".windsurf\skills\stratigraphic-dictionary\scripts\start_server.py" -m "地层分层.csv" -d "stratigraphic_depth_statistics.csv"
```

### 仅预加载数据编辑
```bash
python ".windsurf\skills\stratigraphic-dictionary\scripts\start_server.py" -d "stratigraphic_depth_statistics.csv"
```

### 手动上传模式
```bash
python ".windsurf\skills\stratigraphic-dictionary\scripts\start_server.py"
```

**重要提示**：请在项目根目录下运行以上命令，确保相对路径正确。

## 📋 功能特性

### ✨ 智能数据加载
- 页面打开时自动检测预加载数据
- 无需手动上传，直接显示地层结构
- 右上角显示加载状态通知

### 🎨 可视化编辑
- **拖拽调整**：拖拽地层边界调整位置
- **双击编辑**：修改地层属性信息
- **展开模式**：查看详细层级结构
- **添加小层**：创建新的地层条目

### 📤 数据导出
- 一键导出编辑后的数据
- 自动生成验证文件
- 保持原始数据格式

## 🔧 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `-m, --stratigraphy` | 地层分层参考文件 | `-m "地层分层.csv"` |
| `-d, --data` | 预加载数据文件 | `-d "数据文件.csv"` |
| `--host` | 服务器地址 | `--host 127.0.0.1` |
| `--port` | 服务器端口 | `--port 5000` |
| `--debug` | 调试模式 | `--debug` |

## 📁 文件格式

### 地层数据文件（必需）
```csv
地层名称,所属层位,顶界所处位置（0~1）,底界所处位置（0~1）
沙溪庙组,沙溪庙组,0,1
沙二段,沙溪庙组,0,0.5
```

### 地层分层参考文件（可选）
```csv
序号,地层信息
1,沙溪庙组
2,凉高山组
3,自流井组
```

## 🛠️ 故障排除

### 常见问题
1. **预加载失败** → 使用绝对路径
2. **端口占用** → 使用 `--port 8080`
3. **文件编码** → 确保UTF-8编码
4. **导出404** → 检查uploads目录权限

### 调试方法
1. 打开浏览器开发者工具（F12）
2. 查看控制台日志
3. 检查网络请求状态

## 💡 最佳实践

1. **使用绝对路径**避免文件找不到
2. **预加载数据**提高工作效率
3. **定期备份**重要地层数据
4. **使用参考文件**确保地层顺序一致

## 📞 技术支持

- 依赖包：Flask, pandas, numpy
- 浏览器：Chrome, Firefox, Safari
- 系统：Windows, macOS, Linux

---
**版本**: v1.0.0  
**更新**: 2026-02-03
