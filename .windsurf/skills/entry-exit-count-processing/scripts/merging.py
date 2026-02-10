import pandas as pd
import numpy as np
import argparse
import sys

def process_drilling_data(input_file, output_file="CCQ_merged.csv"):
    # 读取CSV文件
    df = pd.read_csv(input_file, encoding='utf-8')
    
    # 如果没有序号列，添加临时序号列
    has_xuhao = '序号' in df.columns
    if not has_xuhao:
        df.insert(0, '序号', range(1, len(df) + 1))
    
    # 添加新的列用于存储进尺命中率
    df['进尺命中率'] = 1.0
    
    # 创建一个新的DataFrame副本以便于操作
    result_df = df.copy()
    
    print(f"原始数据共有 {len(result_df)} 行")
    
    # 创建一个列表来存储新增的行
    new_rows_to_add = []  # 存储(插入位置, 新行数据)元组
    rows_to_modify = []
    
    i = 0
    while i < len(result_df):
        current_row = result_df.iloc[i].copy()
        print(f"\n处理第 {i} 行: 序号={current_row['序号']}, 入井次数={current_row['入井次数']}")
        
        # 情况1: 如果入井次数为1，并且下一行也仍为1，则进尺命中率为1
        if current_row['入井次数'] == 1 and i + 1 < len(result_df) and result_df.iloc[i + 1]['入井次数'] == 1:
            print(f"  发现连续的入井次数1序列: 行{i}和行{i+1}")
            # 这种情况下，当前行和下一行的进尺命中率都设为1
            # 保留6位有效数字
            rows_to_modify.append((i, round(1.0, 6)))
            if result_df.iloc[i + 1]['入井次数'] == 1:
                rows_to_modify.append((i + 1, round(1.0, 6)))
            i += 2  # 跳过这两行
            continue
        
        # 情况2: 检查连续的入井次数序列（如1,2,3...）
        if current_row['入井次数'] >= 1:
            # 找到包含当前行的最长连续序列
            # 先向后查找
            sequence_end = i
            j = i + 1
            while j < len(result_df):
                if result_df.iloc[j]['入井次数'] == result_df.iloc[j-1]['入井次数'] + 1:
                    sequence_end = j
                    j += 1
                else:
                    break
            
            # 再向前查找
            sequence_start = i
            k = i - 1
            while k >= 0:
                if result_df.iloc[k]['入井次数'] == result_df.iloc[k+1]['入井次数'] - 1:
                    sequence_start = k
                    k -= 1
                else:
                    break
            
            print(f"  检测到潜在序列: 从行{sequence_start}到行{sequence_end} (入井次数 {result_df.iloc[sequence_start]['入井次数']} 到 {result_df.iloc[sequence_end]['入井次数']})")
            
            # 只有当序列长度大于1时才进行特殊处理
            if sequence_end > sequence_start:
                # 检查钻头型号、厂家是否一致，以及井深是否连续
                consistent_drill_info = True
                depth_continuous = True
                
                # 检查钻头型号和厂家是否一致 - 支持多种列名
                drill_type_col = '钻头型号' if '钻头型号' in result_df.columns else '型号'
                manufacturer_col = '生产厂家' if '生产厂家' in result_df.columns else '厂家'
                
                base_drill_type = result_df.iloc[sequence_start][drill_type_col]
                base_manufacturer = result_df.iloc[sequence_start][manufacturer_col]
                
                for k in range(sequence_start, sequence_end + 1):  # 包含sequence_end
                    current_drill_type = result_df.iloc[k][drill_type_col]
                    current_manufacturer = result_df.iloc[k][manufacturer_col]
                    if (current_drill_type != base_drill_type or 
                        current_manufacturer != base_manufacturer):
                        consistent_drill_info = False
                        break
                
                # 检查井深是否连续
                for k in range(sequence_start, sequence_end):
                    current_end_depth = result_df.iloc[k]['结束井深']
                    next_start_depth = result_df.iloc[k + 1]['起始井深']
                    if current_end_depth != next_start_depth:
                        depth_continuous = False
                        break
                
                print(f"    钻头型号和厂家一致性: {consistent_drill_info}, 井深连续性: {depth_continuous}")
                
                # 检查是否是井深连续、厂家一致但钻头型号不一致的情况
                if not consistent_drill_info and depth_continuous and result_df.iloc[sequence_start][manufacturer_col] == result_df.iloc[sequence_start+1][manufacturer_col]:
                    # 收集不一致的钻头型号信息
                    drill_types = []
                    for k in range(sequence_start, sequence_end + 1):
                        drill_type = result_df.iloc[k][drill_type_col]
                        if drill_type not in drill_types:
                            drill_types.append(drill_type)
                    
                    print(f"    警告: 检测到井深连续、厂家一致但钻头型号不一致的情况!")
                    print(f"    钻头型号差异: {drill_types}")
                    print(f"    请检查钻头型号是否填写错误，如果是，请修正后重新运行程序")
                
                # 如果满足所有条件，则进行特殊处理
                if consistent_drill_info and depth_continuous:
                    print(f"    满足所有条件，进行特殊处理")
                    # 计算总进尺、总纯钻时间等
                    total_depth = sum(result_df.iloc[k]['进尺'] for k in range(sequence_start, sequence_end + 1))
                    total_drill_time = sum(result_df.iloc[k]['纯钻时间'] for k in range(sequence_start, sequence_end + 1))
                    
                    print(f"    序列范围: 行{sequence_start}到{sequence_end}")
                    for k in range(sequence_start, sequence_end + 1):
                        print(f"      行{k}: 入井次数{result_df.iloc[k]['入井次数']}, 进尺{result_df.iloc[k]['进尺']}")
                    print(f"    总进尺: {total_depth}, 总纯钻时间: {total_drill_time}")
                    
                    # 计算钻井液密度的加权平均值
                    weighted_density = 0
                    total_weight = 0
                    for k in range(sequence_start, sequence_end + 1):
                        weight = result_df.iloc[k]['进尺']
                        weighted_density += result_df.iloc[k]['钻井液密度'] * weight
                        total_weight += weight
                    
                    if total_weight > 0:
                        weighted_density /= total_weight
                    else:
                        weighted_density = result_df.iloc[sequence_end]['钻井液密度']
                    
                    # 计算机械钻速的加权平均值
                    weighted_mechanical_speed = 0
                    for k in range(sequence_start, sequence_end + 1):
                        # 检查机械钻速是否为空值
                        mechanical_speed = result_df.iloc[k]['机械钻速']
                        if pd.notna(mechanical_speed):  # 只有非空值才参与计算
                            weight = result_df.iloc[k]['进尺']
                            weighted_mechanical_speed += mechanical_speed * weight
                        else:
                            # 如果某个值为空，暂时跳过，稍后再处理
                            pass
                    
                    # 重新计算，处理空值情况
                    total_weight_for_speed = 0
                    weighted_mechanical_speed = 0
                    for k in range(sequence_start, sequence_end + 1):
                        mechanical_speed = result_df.iloc[k]['机械钻速']
                        if pd.notna(mechanical_speed):
                            weight = result_df.iloc[k]['进尺']
                            weighted_mechanical_speed += mechanical_speed * weight
                            total_weight_for_speed += weight
                    
                    if total_weight_for_speed > 0:
                        weighted_mechanical_speed /= total_weight_for_speed
                    else:
                        # 如果所有机械钻速都是空值或无法计算，使用最后一行的值或默认值
                        last_valid_speed = result_df.iloc[sequence_end]['机械钻速']
                        if pd.isna(last_valid_speed):
                            weighted_mechanical_speed = 0.0
                        else:
                            weighted_mechanical_speed = last_valid_speed
                    
                    # 计算各参数的加权平均值
                    weighted_drill_press_a = 0
                    weighted_drill_press_b = 0
                    weighted_rpm_a = 0
                    weighted_rpm_b = 0
                    weighted_flow_a = 0
                    weighted_flow_b = 0
                    weighted_pump_press_a = 0
                    weighted_pump_press_b = 0
                    
                    for k in range(sequence_start, sequence_end + 1):
                        weight = result_df.iloc[k]['进尺']
                        weighted_drill_press_a += result_df.iloc[k]['钻压A'] * weight
                        weighted_drill_press_b += result_df.iloc[k]['钻压B'] * weight
                        weighted_rpm_a += result_df.iloc[k]['转速A'] * weight
                        weighted_rpm_b += result_df.iloc[k]['转速B'] * weight
                        weighted_flow_a += result_df.iloc[k]['排量A'] * weight
                        weighted_flow_b += result_df.iloc[k]['排量B'] * weight
                        weighted_pump_press_a += result_df.iloc[k]['泵压A'] * weight
                        weighted_pump_press_b += result_df.iloc[k]['泵压B'] * weight
                    
                    if total_weight > 0:
                        weighted_drill_press_a /= total_weight
                        weighted_drill_press_b /= total_weight
                        weighted_rpm_a /= total_weight
                        weighted_rpm_b /= total_weight
                        weighted_flow_a /= total_weight
                        weighted_flow_b /= total_weight
                        weighted_pump_press_a /= total_weight
                        weighted_pump_press_b /= total_weight
                    else:
                        # 如果权重为0，使用最后一行的值
                        weighted_drill_press_a = result_df.iloc[sequence_end]['钻压A']
                        weighted_drill_press_b = result_df.iloc[sequence_end]['钻压B']
                        weighted_rpm_a = result_df.iloc[sequence_end]['转速A']
                        weighted_rpm_b = result_df.iloc[sequence_end]['转速B']
                        weighted_flow_a = result_df.iloc[sequence_end]['排量A']
                        weighted_flow_b = result_df.iloc[sequence_end]['排量B']
                        weighted_pump_press_a = result_df.iloc[sequence_end]['泵压A']
                        weighted_pump_press_b = result_df.iloc[sequence_end]['泵压B']
                    
                    # 复制最后一行并修改特定列
                    last_row = result_df.iloc[sequence_end].copy()
                    
                    # 创建新行，序号改为a1, a2, ...
                    new_index = f"a{len(new_rows_to_add) + 1}"
                    last_row['序号'] = new_index
                    last_row['起始井深'] = result_df.iloc[sequence_start]['起始井深']
                    last_row['进尺'] = round(total_depth, 6)  # 保留6位小数
                    last_row['纯钻时间'] = round(total_drill_time, 6)  # 保留6位小数
                    last_row['钻井液密度'] = round(weighted_density, 6)  # 保留6位小数
                    last_row['机械钻速'] = round(weighted_mechanical_speed, 6)  # 保留6位小数，使用加权平均
                    last_row['起始地层'] = result_df.iloc[sequence_start]['起始地层']
                    last_row['钻压A'] = round(weighted_drill_press_a, 6)  # 保留6位小数
                    last_row['钻压B'] = round(weighted_drill_press_b, 6)  # 保留6位小数
                    last_row['转速A'] = round(weighted_rpm_a, 6)  # 保留6位小数
                    last_row['转速B'] = round(weighted_rpm_b, 6)  # 保留6位小数
                    last_row['排量A'] = round(weighted_flow_a, 6)  # 保留6位小数
                    last_row['排量B'] = round(weighted_flow_b, 6)  # 保留6位小数
                    last_row['泵压A'] = round(weighted_pump_press_a, 6)  # 保留6位小数
                    last_row['泵压B'] = round(weighted_pump_press_b, 6)  # 保留6位小数
                    # 进尺命中率为1，保留6位有效数字
                    last_row['进尺命中率'] = round(1.0, 6)
                    
                    # 将新行添加到待插入列表中，记录原始序列结束位置
                    new_rows_to_add.append((sequence_end, last_row))
                    
                    # 更新连续行的进尺和进尺命中率
                    for k in range(sequence_start, sequence_end + 1):
                        original_depth = result_df.iloc[k]['进尺']
                        # 修改原数据以便后续处理
                        rows_to_modify.append(('depth', k, round(total_depth, 6)))  # 临时记录，后面统一处理，保留6位小数
                        if total_depth != 0:
                            hit_rate = original_depth / total_depth
                        else:
                            hit_rate = 1.0
                        # 保留6位有效数字
                        rounded_hit_rate = round(hit_rate, 6)
                        rows_to_modify.append(('hit_rate', k, rounded_hit_rate))
                
                # 移动索引到序列结束后的下一行
                i = sequence_end + 1
                print(f"    处理完成，移动索引到 {i}")
            else:
                # 入井次数为1但下一行不是1的情况，保持默认值1.0
                print(f"  单独的入井次数，不做特殊处理")
                i += 1
        else:
            # 入井次数小于1的情况，直接跳到下一行
            print(f"  入井次数小于1，跳过")
            i += 1
    
    print(f"\n处理完成，开始应用修改...")
    print(f"待修改的行数: {len(rows_to_modify)}")
    print(f"待添加的行数: {len(new_rows_to_add)}")
    
    # 现在应用所有的修改
    # 先处理深度和命中率修改
    for mod in rows_to_modify:
        if mod[0] == 'depth':  # 修改进尺
            idx = mod[1]
            new_value = mod[2]
            result_df.iloc[idx, result_df.columns.get_loc('进尺')] = round(new_value, 6)
        elif mod[0] == 'hit_rate':  # 修改进尺命中率
            idx = mod[1]
            new_value = mod[2]
            # 确保进尺命中率保留6位小数
            result_df.iloc[idx, result_df.columns.get_loc('进尺命中率')] = round(new_value, 6)
        else:  # 只是进尺命中率的情况
            idx = mod[0]
            new_value = mod[1]
            # 确保进尺命中率保留6位小数
            result_df.iloc[idx, result_df.columns.get_loc('进尺命中率')] = round(new_value, 6)
    
    # 然后插入新行 - 按照原始位置的降序排列，确保后插入的不影响先插入的位置
    print(f"开始插入新行...")
    # 按原始结束位置降序排列，这样插入时后面的行不会影响前面的插入位置
    sorted_new_rows = sorted(new_rows_to_add, key=lambda x: x[0], reverse=True)
    
    for orig_end_pos, new_row in sorted_new_rows:
        # 计算实际插入位置：原始序列结束位置 + 1
        actual_insert_pos = orig_end_pos + 1
        print(f"  在位置 {actual_insert_pos} 插入新行: {new_row['序号']}")
        result_df = pd.concat([
            result_df.iloc[:actual_insert_pos],
            pd.DataFrame([new_row]),
            result_df.iloc[actual_insert_pos:]
        ]).reset_index(drop=True)
    
    # 保存结果到输出文件
    # 如果原始文件没有序号列，删除临时添加的序号列
    if not has_xuhao and '序号' in result_df.columns:
        result_df = result_df.drop(columns=['序号'])
    
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"处理完成，结果已保存到 {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='处理钻井数据')
    parser.add_argument('input_file', help='待处理的CSV文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径（默认为CCQ_merged.csv）', default='CCQ_merged.csv')
    
    args = parser.parse_args()
    
    process_drilling_data(args.input_file, args.output)