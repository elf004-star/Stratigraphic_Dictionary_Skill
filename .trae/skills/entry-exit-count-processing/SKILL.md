---
name: entry-exit-count-processing
description: 处理钻井数据中包含入井次数(entry count)和进尺(footage)的CSV文件，识别连续入井次数序列，合并相同钻头型号、厂家且井深连续的数据，计算进尺命中率(footage hit rate)和加权平均参数。Use when processing drilling data with entry counts and footage, calculating hit rates, merging consecutive entry sequences, or analyzing well drilling parameters.
---

# Entry Exit Count Processing Skill

处理钻井数据CSV文件，识别和处理入井次数序列，合并相关数据并计算进尺命中率。

## 功能说明

- **输入**: 包含钻井数据的CSV文件，必须包含"入井次数"和"进尺"列
- **输出**: 处理后的CSV文件，包含新增"进尺命中率"列和合并后的数据行

## 核心处理逻辑

1. **识别连续序列**: 检测入井次数的连续序列（如1,2,3...）
2. **一致性检查**: 
   - 钻头型号一致
   - 生产厂家一致
   - 井深连续（结束井深 = 下一行起始井深）
3. **数据合并**: 对满足条件的序列，计算以下加权平均值:
   - 进尺、纯钻时间（求和）
   - 钻井液密度、机械钻速、钻压A/B、转速A/B、排量A/B、泵压A/B（加权平均）
4. **命中率计算**: 各行的进尺 / 总进尺

## 使用方法

### 命令行运行

```bash
python scripts/merging.py <input_csv_file> [-o <output_csv_file>]
```

### 参数说明

- `input_file`: 输入CSV文件路径（必需）
- `-o, --output`: 输出文件路径（默认为CCQ_merged.csv）

## 输入文件格式要求

CSV文件必须包含以下列:
- `序号`, `井号`, `钻头型号`, `钻头类别`, `钻头尺寸mm`
- `生产厂家`, `钻进方式`, `入井时间`, `入井次数`
- `地层信息`, `起始井深`, `结束井深`, `进尺`
- `纯钻时间`, `机械钻速`, `钻井液密度`, `钻压`, `转速`, `排量`, `泵压`
- `起始地层`, `结束地层`, `钻压A`, `钻压B`, `转速A`, `转速B`, `排量A`, `排量B`, `泵压A`, `泵压B`

## 输出文件说明

- 新增`进尺命中率`列，保留6位小数
- 对每个符合条件的连续序列，在序列末尾插入新行（序号为a1, a2...）
- 新行包含合并后的加权平均数据

## 注意事项

- 数据会按入井次数连续递增序列进行分组处理
- 如果井深连续但钻头型号不一致，会输出警告信息
- 所有数值计算结果保留6位小数
