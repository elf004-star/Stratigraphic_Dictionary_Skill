#!/usr/bin/env python3
"""
井分类置信度分析脚本
基于地层分层信息计算井分类的置信度
"""

import pandas as pd
import sys


class WellCategoryAnalyzer:
    """井分类置信度分析器"""
    
    def __init__(self, formation_file="地层分层.csv"):
        self.formation_file = formation_file
        self.categories = None
    
    def load_categories(self):
        """加载地层分类信息"""
        try:
            formation_df = pd.read_csv(self.formation_file, encoding='utf-8')
            
            # 按类别合并深度范围
            grouped_categories = {}
            for _, row in formation_df.iterrows():
                category = row['类别']
                start_depth = row['地层顶深']
                end_depth = row['地层底深']
                
                if category not in grouped_categories:
                    grouped_categories[category] = {'min_start': start_depth, 'max_end': end_depth}
                else:
                    grouped_categories[category]['min_start'] = min(grouped_categories[category]['min_start'], start_depth)
                    grouped_categories[category]['max_end'] = max(grouped_categories[category]['max_end'], end_depth)
            
            # 创建分类深度范围列表
            self.categories = []
            for category, depths in grouped_categories.items():
                category_info = {
                    'category': category,
                    'start_depth': depths['min_start'],
                    'end_depth': depths['max_end']
                }
                self.categories.append(category_info)
            
            return True
        except Exception as e:
            print(f"加载地层分类信息失败: {e}")
            return False
    
    def calculate_confidence(self, processed_data_file, output_file):
        """计算井分类置信度"""
        if not self.load_categories():
            return False
        
        try:
            # 读取处理后的井数据
            well_data_df = pd.read_csv(processed_data_file, encoding='utf-8')
            
            output_rows = []
            
            # 处理每行井数据
            for _, row in well_data_df.iterrows():
                idx = row['序号']
                adjusted_start_depth = float(row['调整后起始井深'])
                adjusted_end_depth = float(row['调整后结束井深'])
                
                # 井段总长度
                total_length = abs(adjusted_end_depth - adjusted_start_depth)
                
                # 检查每个类别的重叠
                for category_info in self.categories:
                    category = category_info['category']
                    cat_start = category_info['start_depth']
                    cat_end = category_info['end_depth']
                    
                    # 计算井段与类别的重叠
                    well_start = min(adjusted_start_depth, adjusted_end_depth)
                    well_end = max(adjusted_start_depth, adjusted_end_depth)
                    
                    overlap_start = max(well_start, cat_start)
                    overlap_end = min(well_end, cat_end)
                    
                    # 如果有重叠
                    if overlap_start <= overlap_end:
                        overlap_length = abs(overlap_end - overlap_start)
                        
                        # 计算置信度
                        if total_length == 0:
                            confidence = 1.0
                        else:
                            confidence = overlap_length / total_length
                        
                        # 添加到输出
                        output_rows.append({
                            '序号': idx,
                            '类别': category,
                            '置信度': round(confidence, 6)
                        })
            
            # 创建输出DataFrame
            output_df = pd.DataFrame(output_rows, columns=['序号', '类别', '置信度'])
            
            # 保存到CSV
            output_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            print(f"置信度分析完成！结果已保存至 {output_file}")
            print(f"输出总行数: {len(output_df)}")
            
            # 显示样本结果
            print("\n样本结果:")
            print(output_df.head(10))
            
            return True
            
        except Exception as e:
            print(f"计算置信度时出错: {e}")
            return False


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python analyze_confidence.py <处理后数据文件> <输出文件>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    analyzer = WellCategoryAnalyzer()
    success = analyzer.calculate_confidence(input_file, output_file)
    
    if success:
        print("置信度分析完成！")
    else:
        print("置信度分析失败！")
        sys.exit(1)
