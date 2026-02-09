#!/usr/bin/env python3
"""
完整的分类分析流程脚本
整合所有步骤的完整地层分类分析流程
"""

import sys
import os
from pathlib import Path

# 导入自定义模块
sys.path.append(str(Path(__file__).parent))

from process_drilling_data import StratigraphicClassifier
from analyze_confidence import WellCategoryAnalyzer
from validate_dictionary import DictionaryValidator
import pandas as pd


class StratigraphicAnalysisPipeline:
    """地层分类分析完整流程"""
    
    def __init__(self, dict_file="stratigraphic_depth_statistics.json", 
                 formation_file="地层分层.csv"):
        self.dict_file = dict_file
        self.formation_file = formation_file
        self.validator = DictionaryValidator(dict_file, datatest_file="CCQ_merged.csv", stratigraphic_file=formation_file)
        self.classifier = StratigraphicClassifier(dict_file, formation_file)
        self.analyzer = WellCategoryAnalyzer(formation_file)
    
    def merge_results(self, confidence_file, original_file, output_file):
        """合并置信度结果与原始数据"""
        try:
            # 读取两个CSV文件
            df_confidence = pd.read_csv(confidence_file)
            df_original = pd.read_csv(original_file)
            
            # 创建原始数据的映射字典
            original_dict = {}
            for _, row in df_original.iterrows():
                serial_num = row['序号']
                original_dict[serial_num] = row.drop('序号')
            
            # 为置信度数据的每一行添加原始数据
            new_rows = []
            for _, conf_row in df_confidence.iterrows():
                serial_num = conf_row['序号']
                new_row = conf_row.copy()
                
                if serial_num in original_dict:
                    for col_name, value in original_dict[serial_num].items():
                        new_row[col_name] = value
                
                new_rows.append(new_row)
            
            # 创建新的DataFrame并保存
            result_df = pd.DataFrame(new_rows)
            result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            print(f"合并完成！结果已保存至 {output_file}")
            print(f"原始置信度文件行数: {len(df_confidence)}")
            print(f"合并后结果行数: {len(result_df)}")
            
            return True
            
        except Exception as e:
            print(f"合并结果时出错: {e}")
            return False
    
    def run_complete_analysis(self, input_csv, output_csv="CCQ_classification.csv", 
                            save_intermediate=False):
        """运行完整的分析流程"""
        print("=" * 60)
        print("基于置信度的地层分类分析系统")
        print("=" * 60)
        
        # 更新文件路径
        self.validator.datatest_file = input_csv
        
        # 步骤1: 验证字典
        print("\n步骤 1: 验证字典完整性...")
        if not self.validator.check_dictionary():
            print("字典验证失败，程序终止。请修复字典后再运行。")
            return False
        
        # 步骤2: 处理钻井数据
        print("\n步骤 2: 处理钻井数据...")
        processed_file = "temp_processed_data.csv"
        if not self.classifier.process_drilling_data(input_csv, processed_file):
            print("钻井数据处理失败，程序终止。")
            return False
        
        # 步骤3: 分析置信度
        print("\n步骤 3: 分析井分类置信度...")
        confidence_file = "temp_confidence_data.csv"
        if not self.analyzer.calculate_confidence(processed_file, confidence_file):
            print("置信度分析失败，程序终止。")
            return False
        
        # 步骤4: 合并结果
        print("\n步骤 4: 合并最终结果...")
        if not self.merge_results(confidence_file, input_csv, output_csv):
            print("结果合并失败，程序终止。")
            return False
        
        # 清理中间文件
        if not save_intermediate:
            print("\n步骤 5: 清理中间文件...")
            intermediate_files = [processed_file, confidence_file]
            for file_path in intermediate_files:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"已删除中间文件: {file_path}")
                    except OSError as e:
                        print(f"删除文件 {file_path} 时出错: {e}")
        
        print("\n" + "=" * 60)
        print("所有处理步骤完成！")
        print(f"最终结果已保存至 {output_csv}")
        print("=" * 60)
        
        return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python complete_analysis.py <输入CSV文件> [输出CSV文件] [--save]")
        print("示例: python complete_analysis.py CCQ_merged.csv")
        print("示例: python complete_analysis.py CCQ_merged.csv result.csv --save")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else "CCQ_classification.csv"
    save_intermediate = '--save' in sys.argv
    
    pipeline = StratigraphicAnalysisPipeline()
    success = pipeline.run_complete_analysis(input_file, output_file, save_intermediate)
    
    if success:
        print("分析完成！")
    else:
        print("分析失败！")
        sys.exit(1)
