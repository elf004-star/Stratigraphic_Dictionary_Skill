#!/usr/bin/env python3
"""
地层分类分析核心处理脚本
基于置信度的地层分类分析系统的核心功能模块
"""

import json
import csv
import pandas as pd
from pathlib import Path
import sys
import os


class StratigraphicClassifier:
    """地层分类分析器"""
    
    def __init__(self, dict_file="stratigraphic_depth_statistics.json", 
                 formation_file="地层分层.csv"):
        self.dict_file = dict_file
        self.formation_file = formation_file
        self.stratigraphic_dict = None
        self.formation_depths = None
    
    def load_dictionary(self):
        """加载地层字典"""
        try:
            with open(self.dict_file, 'r', encoding='utf-8') as f:
                self.stratigraphic_dict = json.load(f)
            return True
        except FileNotFoundError:
            print(f"错误：字典文件 {self.dict_file} 不存在")
            return False
        except json.JSONDecodeError as e:
            print(f"错误：JSON文件格式不正确 - {e}")
            return False
    
    def load_formation_depths(self):
        """加载地层深度映射"""
        try:
            self.formation_depths = {}
            with open(self.formation_file, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    formation_name = row['地层信息']
                    top_depth = float(row['地层顶深'])
                    bottom_depth = float(row['地层底深'])
                    self.formation_depths[formation_name] = {
                        '顶深': top_depth, 
                        '底深': bottom_depth
                    }
            return True
        except FileNotFoundError:
            print(f"错误：地层分层文件 {self.formation_file} 不存在")
            return False
    
    def predict_formation_by_depth(self, depth):
        """根据深度预测所属地层"""
        if not self.formation_depths:
            return '未知'
        
        for formation_name, depths in self.formation_depths.items():
            top_depth = depths['顶深']
            bottom_depth = depths['底深']
            if top_depth <= depth < bottom_depth:
                return formation_name
        
        # 特殊情况：如果深度等于最大深度，则归入最深层位
        max_depth = max([depths['底深'] for depths in self.formation_depths.values()])
        if depth == max_depth:
            for formation_name, depths in self.formation_depths.items():
                if depths['底深'] == max_depth:
                    return formation_name
        return '未知'
    
    def calculate_mapped_depth(self, position_value, formation_name):
        """根据位置值和地层深度范围计算映射深度"""
        if not self.formation_depths:
            return None
            
        if formation_name in self.formation_depths:
            depth_info = self.formation_depths[formation_name]
            top_depth = depth_info['顶深']
            bottom_depth = depth_info['底深']
            mapped_depth = float(position_value) * (bottom_depth - top_depth) + top_depth
            return round(mapped_depth, 2)
        else:
            # 尝试寻找相似的地层名称
            similar_formations = []
            for key in self.formation_depths.keys():
                if formation_name.replace('段', '') in key or \
                   key.replace('亚段', '').replace('1', '').replace('2', '').replace('3', '') == formation_name.replace('段', ''):
                    similar_formations.append(key)
            
            if similar_formations:
                closest_formation = similar_formations[0]
                depth_info = self.formation_depths[closest_formation]
                top_depth = depth_info['顶深']
                bottom_depth = depth_info['底深']
                mapped_depth = float(position_value) * (bottom_depth - top_depth) + top_depth
                return round(mapped_depth, 2)
            
            return None
    
    def compare_predicted_and_actual(self, predicted, actual):
        """比较预测地层和实际地层是否一致"""
        if predicted == actual:
            return '是'
        elif predicted.replace('亚段', '').replace('1', '').replace('2', '').replace('3', '') == actual.replace('段', ''):
            return '是'
        elif actual.replace('亚段', '').replace('1', '').replace('2', '').replace('3', '') == predicted.replace('段', ''):
            return '是'
        else:
            return '否'
    
    def check_depth_range(self, actual_depth, mapped_depth_start, mapped_depth_end):
        """检查实际井深是否在映射深度范围内"""
        if mapped_depth_start is None or mapped_depth_end is None:
            return '无法判断'
        
        min_mapped_depth = min(mapped_depth_start, mapped_depth_end)
        max_mapped_depth = max(mapped_depth_start, mapped_depth_end)
        
        if min_mapped_depth <= actual_depth <= max_mapped_depth:
            return '是'
        elif actual_depth < min_mapped_depth:
            return '偏小'
        else:
            return '偏大'
    
    def adjust_depth_based_on_judgment(self, judgment, actual_depth, top_mapped_depth, bottom_mapped_depth):
        """根据判断结果调整深度映射"""
        if judgment == '是':
            return actual_depth
        elif judgment == '偏大':
            if top_mapped_depth is not None and bottom_mapped_depth is not None:
                return max(top_mapped_depth, bottom_mapped_depth)
            else:
                return actual_depth
        elif judgment == '偏小':
            if top_mapped_depth is not None and bottom_mapped_depth is not None:
                return min(top_mapped_depth, bottom_mapped_depth)
            else:
                return actual_depth
        else:
            return actual_depth
    
    def process_drilling_data(self, input_csv, output_csv):
        """处理钻井数据并补充地层信息及映射深度"""
        if not self.load_dictionary() or not self.load_formation_depths():
            return False
        
        processed_rows = []
        
        try:
            with open(input_csv, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    start_formation = row['起始地层']
                    end_formation = row['结束地层']
                    start_depth = float(row['起始井深'])
                    end_depth = float(row['结束井深'])
                    
                    # 预测地层
                    predicted_start_formation = self.predict_formation_by_depth(start_depth)
                    predicted_end_formation = self.predict_formation_by_depth(end_depth)
                    
                    # 查找地层信息
                    start_info = self.stratigraphic_dict.get(start_formation, {
                        "所属层位": "未知",
                        "顶界所处位置（0~1）": "0",
                        "底界所处位置（0~1）": "1"
                    })
                    
                    end_info = self.stratigraphic_dict.get(end_formation, {
                        "所属层位": "未知",
                        "顶界所处位置（0~1）": "0",
                        "底界所处位置（0~1）": "1"
                    })
                    
                    # 计算映射深度
                    start_formation_for_depth = start_info["所属层位"]
                    end_formation_for_depth = end_info["所属层位"]
                    
                    start_top_mapped_depth = self.calculate_mapped_depth(
                        start_info["顶界所处位置（0~1）"], 
                        start_formation_for_depth
                    )
                    start_bottom_mapped_depth = self.calculate_mapped_depth(
                        start_info["底界所处位置（0~1）"], 
                        start_formation_for_depth
                    )
                    end_top_mapped_depth = self.calculate_mapped_depth(
                        end_info["顶界所处位置（0~1）"], 
                        end_formation_for_depth
                    )
                    end_bottom_mapped_depth = self.calculate_mapped_depth(
                        end_info["底界所处位置（0~1）"], 
                        end_formation_for_depth
                    )
                    
                    # 一致性检查
                    start_consistency = self.compare_predicted_and_actual(
                        predicted_start_formation, start_formation_for_depth
                    )
                    end_consistency = self.compare_predicted_and_actual(
                        predicted_end_formation, end_formation_for_depth
                    )
                    
                    # 深度范围检查
                    start_depth_in_range = self.check_depth_range(
                        start_depth, start_top_mapped_depth, start_bottom_mapped_depth
                    )
                    end_depth_in_range = self.check_depth_range(
                        end_depth, end_top_mapped_depth, end_bottom_mapped_depth
                    )
                    
                    # 调整深度映射
                    adjusted_start_depth = self.adjust_depth_based_on_judgment(
                        start_depth_in_range, start_depth, start_top_mapped_depth, start_bottom_mapped_depth
                    )
                    adjusted_end_depth = self.adjust_depth_based_on_judgment(
                        end_depth_in_range, end_depth, end_top_mapped_depth, end_bottom_mapped_depth
                    )
                    
                    # 特殊处理规则
                    if start_depth_in_range == '偏大' and end_depth_in_range == '偏大':
                        if start_top_mapped_depth is not None and start_bottom_mapped_depth is not None:
                            adjusted_start_depth = round((start_top_mapped_depth + start_bottom_mapped_depth) / 2, 2)
                    
                    if start_depth_in_range == '偏小' and end_depth_in_range == '偏小':
                        if end_top_mapped_depth is not None and end_bottom_mapped_depth is not None:
                            adjusted_end_depth = round((end_top_mapped_depth + end_bottom_mapped_depth) / 2, 2)
                    
                    # 创建新行
                    new_row = {
                        '序号': row['序号'],
                        '起始井深': row['起始井深'],
                        '结束井深': row['结束井深'],
                        
                        '起始地层': row['起始地层'],
                        '起始地层_所属层位': start_info['所属层位'],
                        '起始地层_顶界所处位置（0~1）': start_info['顶界所处位置（0~1）'],
                        '起始地层_顶界映射深度': start_top_mapped_depth,
                        '起始地层_底界所处位置（0~1）': start_info['底界所处位置（0~1）'],
                        '起始地层_底界映射深度': start_bottom_mapped_depth,
                        
                        '结束地层': row['结束地层'],
                        '结束地层_所属层位': end_info['所属层位'],
                        '结束地层_顶界所处位置（0~1）': end_info['顶界所处位置（0~1）'],
                        '结束地层_顶界映射深度': end_top_mapped_depth,
                        '结束地层_底界所处位置（0~1）': end_info['底界所处位置（0~1）'],
                        '结束地层_底界映射深度': end_bottom_mapped_depth,
                        
                        '起始井深预测所属大层': predicted_start_formation,
                        '起始预测大层与所属层位一致性': start_consistency,
                        '起始井深是否在映射深度间': start_depth_in_range,
                        '结束井深预测所属大层': predicted_end_formation,
                        '结束预测大层与所属层位一致性': end_consistency,
                        '结束井深是否在映射深度间': end_depth_in_range,
                        
                        '调整后起始井深': adjusted_start_depth,
                        '调整后结束井深': adjusted_end_depth
                    }
                    
                    processed_rows.append(new_row)
        
        except Exception as e:
            print(f"处理数据时出错: {e}")
            return False
        
        # 保存结果
        fieldnames = [
            '序号', '起始井深', '结束井深',
            '起始地层', '起始地层_所属层位', '起始地层_顶界所处位置（0~1）', '起始地层_顶界映射深度',
            '起始地层_底界所处位置（0~1）', '起始地层_底界映射深度',
            '结束地层', '结束地层_所属层位', '结束地层_顶界所处位置（0~1）', '结束地层_顶界映射深度',
            '结束地层_底界所处位置（0~1）', '结束地层_底界映射深度',
            '起始井深预测所属大层', '起始预测大层与所属层位一致性', '起始井深是否在映射深度间',
            '结束井深预测所属大层', '结束预测大层与所属层位一致性', '结束井深是否在映射深度间',
            '调整后起始井深', '调整后结束井深'
        ]
        
        try:
            with open(output_csv, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(processed_rows)
            print(f"数据处理完成！共处理 {len(processed_rows)} 条记录")
            return True
        except Exception as e:
            print(f"保存结果时出错: {e}")
            return False


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python process_drilling_data.py <输入CSV文件> <输出CSV文件>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    classifier = StratigraphicClassifier()
    success = classifier.process_drilling_data(input_file, output_file)
    
    if success:
        print(f"处理完成！结果已保存至 {output_file}")
    else:
        print("处理失败！")
        sys.exit(1)
