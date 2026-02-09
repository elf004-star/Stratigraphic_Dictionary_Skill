#!/usr/bin/env python3
"""
地层分类分析 - 简化版一键式处理
一键完成钻井数据的地层分类和置信度分析
"""

import sys
import os
import json
import pandas as pd
from pathlib import Path


class SimpleStratigraphicAnalyzer:
    """简化的地层分类分析器"""
    
    def __init__(self):
        self.setup_files()
    
    def setup_files(self):
        """自动设置文件路径"""
        self.drilling_data = None
        self.dict_file = None
        self.formation_file = None
        
        # 自动查找文件
        for file in os.listdir('.'):
            if file.endswith('.csv') and 'CCQ' in file:
                self.drilling_data = file
            elif file.endswith('.json') and ('verification' in file or 'stratigraphic' in file):
                self.dict_file = file
            elif '地层' in file and file.endswith('.csv'):
                self.formation_file = file
        
        # 如果找不到标准文件，使用默认名称
        if not self.dict_file and os.path.exists('export_verification.json'):
            self.dict_file = 'export_verification.json'
        if not self.formation_file:
            self.formation_file = '地层分层.csv'
    
    def load_data(self):
        """加载所有必需数据"""
        try:
            # 加载钻井数据
            if not self.drilling_data:
                print("❌ 未找到钻井数据文件 (如 CCQ_merged.csv)")
                return False
            
            print(f"📊 加载钻井数据: {self.drilling_data}")
            self.df_drilling = pd.read_csv(self.drilling_data, encoding='utf-8')
            
            # 加载地层字典
            if not os.path.exists(self.dict_file):
                print(f"❌ 未找到地层字典文件: {self.dict_file}")
                return False
                
            print(f"📚 加载地层字典: {self.dict_file}")
            with open(self.dict_file, 'r', encoding='utf-8') as f:
                self.stratigraphic_dict = json.load(f)
            
            # 加载地层分层
            if not os.path.exists(self.formation_file):
                print(f"❌ 未找到地层分层文件: {self.formation_file}")
                return False
                
            print(f"🏔️ 加载地层分层: {self.formation_file}")
            self.df_formations = pd.read_csv(self.formation_file, encoding='utf-8')
            
            return True
            
        except Exception as e:
            print(f"❌ 加载数据失败: {e}")
            return False
    
    def predict_formation(self, depth):
        """根据深度预测地层"""
        for _, row in self.df_formations.iterrows():
            if row['地层顶深'] <= depth < row['地层底深']:
                return row['地层信息']
        
        # 边界情况处理
        max_depth = self.df_formations['地层底深'].max()
        if depth == max_depth:
            for _, row in self.df_formations.iterrows():
                if row['地层底深'] == max_depth:
                    return row['地层信息']
        return '未知'
    
    def calculate_confidence(self, start_depth, end_depth, category):
        """计算置信度"""
        # 获取该类别的深度范围
        category_rows = self.df_formations[self.df_formations['类别'] == category]
        if category_rows.empty:
            return 0.0
        
        min_start = category_rows['地层顶深'].min()
        max_end = category_rows['地层底深'].max()
        
        # 计算重叠
        well_start = min(start_depth, end_depth)
        well_end = max(start_depth, end_depth)
        
        overlap_start = max(well_start, min_start)
        overlap_end = min(well_end, max_end)
        
        if overlap_start <= overlap_end:
            overlap_length = overlap_end - overlap_start
            total_length = abs(end_depth - start_depth)
            return overlap_length / total_length if total_length > 0 else 1.0
        
        return 0.0
    
    def process_data(self):
        """处理数据并生成结果"""
        print("🔄 开始处理数据...")
        
        results = []
        
        for _, row in self.df_drilling.iterrows():
            idx = row['序号']
            start_depth = float(row['起始井深'])
            end_depth = float(row['结束井深'])
            
            # 获取所有类别
            categories = self.df_formations['类别'].unique()
            
            for category in categories:
                confidence = self.calculate_confidence(start_depth, end_depth, category)
                
                # 只保留有意义的置信度
                if confidence > 0.001:
                    result_row = row.copy()
                    result_row['类别'] = category
                    result_row['置信度'] = round(confidence, 6)
                    results.append(result_row)
        
        # 创建结果DataFrame
        self.df_result = pd.DataFrame(results)
        
        # 重新排列列顺序
        cols = ['序号', '类别', '置信度'] + [col for col in self.df_drilling.columns if col != '序号']
        self.df_result = self.df_result[cols]
        
        print(f"✅ 处理完成，生成 {len(self.df_result)} 条记录")
        return True
    
    def save_results(self, output_file="CCQ_classification.csv"):
        """保存结果"""
        try:
            self.df_result.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"💾 结果已保存至: {output_file}")
            
            # 显示统计信息
            print("\n📈 结果统计:")
            category_stats = self.df_result.groupby('类别').agg({
                '置信度': ['count', 'mean'],
                '序号': 'nunique'
            }).round(3)
            category_stats.columns = ['记录数', '平均置信度', '井段数']
            print(category_stats)
            
            return True
            
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")
            return False
    
    def run_analysis(self, input_file=None, output_file="CCQ_classification.csv"):
        """运行完整分析"""
        print("=" * 50)
        print("🏔️ 地层分类分析 - 简化版")
        print("=" * 50)
        
        # 如果指定了输入文件，使用它
        if input_file:
            self.drilling_data = input_file
        
        # 显示找到的文件
        print(f"📁 使用文件:")
        print(f"   钻井数据: {self.drilling_data}")
        print(f"   地层字典: {self.dict_file}")
        print(f"   地层分层: {self.formation_file}")
        
        # 执行分析
        if not self.load_data():
            return False
        
        if not self.process_data():
            return False
        
        if not self.save_results(output_file):
            return False
        
        print("\n🎉 分析完成！")
        return True


def main():
    """主函数"""
    input_file = sys.argv[1] if len(sys.argv) > 1 else None
    output_file = sys.argv[2] if len(sys.argv) > 2 else "CCQ_classification.csv"
    
    analyzer = SimpleStratigraphicAnalyzer()
    
    if input_file:
        success = analyzer.run_analysis(input_file, output_file)
    else:
        success = analyzer.run_analysis(output_file=output_file)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
