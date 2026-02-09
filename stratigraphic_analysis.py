#!/usr/bin/env python3
"""
地层分析脚本
从钻井数据中提取地层统计信息
"""

import pandas as pd
import sys
import argparse
import os


def analyze_stratigraphy(data_file, stratigraphy_file, output_file):
    """
    从钻井数据中提取地层统计信息
    
    :param data_file: 钻井数据文件路径
    :param stratigraphy_file: 地层分层参考文件路径
    :param output_file: 输出文件路径
    """
    print(f"📊 分析钻井数据: {data_file}")
    print(f"🏔️ 使用地层参考: {stratigraphy_file}")
    
    # 读取钻井数据
    df_drilling = pd.read_csv(data_file, encoding='utf-8')
    
    # 读取地层分层参考
    df_stratigraphy = pd.read_csv(stratigraphy_file, encoding='utf-8')
    
    # 提取地层统计信息
    formations = set()
    if '起始地层' in df_drilling.columns:
        formations.update(df_drilling['起始地层'].dropna().unique())
    if '结束地层' in df_drilling.columns:
        formations.update(df_drilling['结束地层'].dropna().unique())
    
    # 为每个地层生成统计信息
    stats_list = []
    for formation in formations:
        if formation and formation != 'nan' and str(formation).strip() != '':
            # 找到包含此地层的所有记录
            mask = (
                (df_drilling['起始地层'].str.contains(formation, na=False)) |
                (df_drilling['结束地层'].str.contains(formation, na=False))
            )
            subset = df_drilling[mask]
            
            if not subset.empty:
                # 获取深度范围
                min_top_depth = subset['起始井深'].min()
                max_bottom_depth = subset['结束井深'].max()
                avg_depth = (min_top_depth + max_bottom_depth) / 2
                count = len(subset)
                
                # 确定所属层位
                category = '未知'
                for _, row in df_stratigraphy.iterrows():
                    if formation in row['地层信息']:
                        category = row['类别']
                        break
                
                stats_list.append({
                    '地层名称': formation,
                    '所属层位': category,
                    '顶界所处位置（0~1）': round(min_top_depth / max_bottom_depth if max_bottom_depth > 0 else 0, 6),
                    '底界所处位置（0~1）': round(max_bottom_depth / max_bottom_depth if max_bottom_depth > 0 else 1, 6),
                    '最小深度': min_top_depth,
                    '最大深度': max_bottom_depth,
                    '平均深度': avg_depth,
                    '出现次数': count
                })
    
    # 创建结果DataFrame
    df_result = pd.DataFrame(stats_list)
    
    # 如果结果为空，创建一个基本结构
    if df_result.empty:
        print("⚠️ 未在钻井数据中找到地层信息，使用参考地层创建基础模板")
        df_result = df_stratigraphy.copy()
        df_result.rename(columns={
            '地层信息': '地层名称',
        }, inplace=True)
        df_result['所属层位'] = df_result.get('类别', df_result.get('所属层位', '未知'))
        df_result['顶界所处位置（0~1）'] = 0.0
        df_result['底界所处位置（0~1）'] = 1.0
        df_result['最小深度'] = df_result['地层顶深']
        df_result['最大深度'] = df_result['地层底深']
        df_result['平均深度'] = (df_result['地层顶深'] + df_result['地层底深']) / 2
        df_result['出现次数'] = 1
    
    # 保存结果
    df_result.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ 地层统计信息已保存至: {output_file}")
    print(f"📈 共处理 {len(df_result)} 个地层")


def main():
    parser = argparse.ArgumentParser(description='地层分析脚本')
    parser.add_argument('-d', '--data-file', required=True, help='钻井数据文件路径')
    parser.add_argument('-s', '--stratigraphy-file', required=True, help='地层分层参考文件路径')
    parser.add_argument('-o', '--output-file', required=True, help='输出文件路径')
    parser.add_argument('-c', '--config-file', help='现有JSON配置文件路径（可选）')
    
    args = parser.parse_args()
    
    analyze_stratigraphy(args.data_file, args.stratigraphy_file, args.output_file)


if __name__ == "__main__":
    main()