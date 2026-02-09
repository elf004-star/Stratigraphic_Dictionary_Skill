# 地层分类算法详解

## 核心算法原理

### 1. 深度预测算法

根据实际井深预测所属地层：

```python
def predict_formation_by_depth(depth):
    for formation_name, depths in formation_depths.items():
        top_depth = depths['顶深']
        bottom_depth = depths['底深']
        if top_depth <= depth < bottom_depth:
            return formation_name
    return '未知'
```

**逻辑:**
- 遍历所有地层深度范围
- 找到包含目标深度的地层
- 特殊处理最大深度边界情况

### 2. 映射深度计算

基于位置值计算实际映射深度：

```
映射深度 = 位置值 × (底深 - 顶深) + 顶深
```

**示例:**
- 地层范围: 1000m - 1500m
- 位置值: 0.5
- 映射深度: 0.5 × (1500-1000) + 1000 = 1250m

### 3. 一致性检查算法

比较预测地层与实际地层：

```python
def compare_predicted_and_actual(predicted, actual):
    if predicted == actual:
        return '是'
    # 模糊匹配处理
    elif predicted.replace('亚段', '').replace('1', '').replace('2', '').replace('3', '') == actual.replace('段', ''):
        return '是'
    else:
        return '否'
```

**匹配规则:**
- 完全匹配: 直接返回"是"
- 模糊匹配: 去除"亚段"、"段"、数字后缀后比较
- 不匹配: 返回"否"

### 4. 深度范围验证

检查实际井深是否在映射深度范围内：

```python
def check_depth_range(actual_depth, mapped_start, mapped_end):
    min_depth = min(mapped_start, mapped_end)
    max_depth = max(mapped_start, mapped_end)
    
    if min_depth <= actual_depth <= max_depth:
        return '是'
    elif actual_depth < min_depth:
        return '偏小'
    else:
        return '偏大'
```

**结果类型:**
- '是': 在范围内
- '偏小': 小于范围最小值
- '偏大': 大于范围最大值
- '无法判断': 映射深度无效

### 5. 深度调整算法

根据深度范围检查结果调整映射深度：

```python
def adjust_depth_based_on_judgment(judgment, actual_depth, top_mapped, bottom_mapped):
    if judgment == '是':
        return actual_depth  # 使用实际深度
    elif judgment == '偏大':
        return max(top_mapped, bottom_mapped)  # 使用底界
    elif judgment == '偏小':
        return min(top_mapped, bottom_mapped)  # 使用顶界
    else:
        return actual_depth  # 默认使用实际深度
```

### 6. 特殊处理规则

**双偏大情况:**
```
if start_depth_in_range == '偏大' and end_depth_in_range == '偏大':
    adjusted_start_depth = (start_top_mapped + start_bottom_mapped) / 2
```

**双偏小情况:**
```
if start_depth_in_range == '偏小' and end_depth_in_range == '偏小':
    adjusted_end_depth = (end_top_mapped + end_bottom_mapped) / 2
```

## 置信度计算算法

### 重叠度计算

```python
# 计算井段与类别的重叠
overlap_start = max(well_start, category_start)
overlap_end = min(well_end, category_end)

if overlap_start <= overlap_end:
    overlap_length = overlap_end - overlap_start
    confidence = overlap_length / total_well_length
```

**置信度公式:**
```
置信度 = 井段与地层类别的重叠长度 / 井段总长度
```

**特殊情况:**
- 井段长度为0: 置信度设为1.0
- 无重叠: 不生成置信度记录

## 相似地层匹配

当精确匹配失败时，使用相似性算法：

```python
# 寻找相似地层名称
for key in formation_depths.keys():
    if formation_name.replace('段', '') in key or \
       key.replace('亚段', '').replace('1', '').replace('2', '').replace('3', '') == formation_name.replace('段', ''):
        similar_formations.append(key)
```

**匹配策略:**
1. 包含关系检查
2. 去除后缀比较
3. 使用第一个匹配结果

## 错误处理机制

### 数据验证
- 文件存在性检查
- 列名验证
- 数据类型验证
- 数值范围验证

### 异常处理
- 文件读取异常
- 数据格式异常
- 计算过程异常
- 输出写入异常

### 容错机制
- 缺失字段默认值
- 无效数据跳过
- 相似名称回退
- 详细错误日志
