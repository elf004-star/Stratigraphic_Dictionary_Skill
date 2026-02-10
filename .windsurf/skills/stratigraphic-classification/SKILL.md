---
name: stratigraphic-classification
description: Simplified geological stratigraphic classification system for drilling data analysis with automatic file detection and one-click confidence-based formation mapping. Use when processing drilling data that requires formation classification, confidence calculation, or integration of geological data sources.
---

# 地层分类分析系统

简化的地层分类分析系统，一键完成钻井数据的地层分类和置信度分析。

## 🚀 快速开始

### 一键分析（推荐）

自动检测文件并处理：

```bash
python scripts/simple_analysis.py
```

指定输入输出文件：

```bash
python scripts/simple_analysis.py CCQ_merged.csv result.csv
```

### 高级分析（完整功能）

```bash
python scripts/complete_analysis.py CCQ_merged.csv
```

## 📁 文件要求

系统自动检测以下文件：

- **钻井数据**: `CCQ_merged.csv` 或包含"CCQ"的CSV文件
- **地层字典**: `export_verification.json` 或包含"verification"/"stratigraphic"的JSON文件  
- **地层分层**: `地层分层.csv`

### 输入文件格式

**钻井数据CSV**必需列：
- `序号`, `起始井深`, `结束井深`, `起始地层`, `结束地层`

**地层字典JSON**格式：
```json
{
  "地层名": {
    "所属层位": "上级地层",
    "顶界所处位置（0~1）": "0.5",
    "底界所处位置（0~1）": "1.0"
  }
}
```

**地层分层CSV**必需列：
- `地层信息`, `地层顶深`, `地层底深`, `类别`

## 🎯 核心功能

### 简化版 (simple_analysis.py)
- ✅ 自动文件检测
- ✅ 一键式处理
- ✅ 置信度计算
- ✅ 结果统计显示

### 完整版 (complete_analysis.py)
- ✅ 深度映射算法
- ✅ 地层一致性检查
- ✅ 智能深度调整
- ✅ 详细验证报告

## 📊 输出结果

**CCQ_classification.csv** 包含：
- 原始钻井数据
- 地层分类结果
- 置信度评分 (0-1)
- 统计汇总信息

## 🔧 使用场景

- **石油钻井**: 钻井记录的地层分类
- **地质勘探**: 深度记录的地层划分
- **数据质量评估**: 通过置信度评估数据可靠性

## ⚡ 优化特性

- **零配置**: 自动检测所有输入文件
- **一键运行**: 单命令完成所有分析
- **智能处理**: 自动处理边界情况和异常数据
- **清晰输出**: 彩色日志和统计信息

## 📚 详细文档

- [数据格式规范](references/data_formats.md)
- [算法详解](references/algorithms.md)

## 🛠️ 故障排除

**常见问题：**
1. 找不到文件 → 检查文件名是否符合要求
2. 编码错误 → 确保CSV文件使用UTF-8编码
3. 列名错误 → 检查必需列是否存在

**验证命令：**
```bash
python scripts/validate_dictionary.py
```
