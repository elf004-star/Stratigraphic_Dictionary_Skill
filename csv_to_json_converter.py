import csv
import json
import argparse
import os
from collections import OrderedDict

def convert_csv_to_json(csv_file_path, config_file_path=None, update_strategy='u'):
    """
    将CSV文件转换为以地层名称为核心的JSON字典
    :param csv_file_path: 输入CSV文件路径
    :param config_file_path: 配置文件路径（可选）
    :param update_strategy: 更新策略 ('u' 以字典为准, 'r' 以CSV为准)
    """
    result_dict = {}
    
    # 如果提供了配置文件，先加载现有数据
    if config_file_path and os.path.exists(config_file_path):
        with open(config_file_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        result_dict.update(existing_data)
        print(f"已加载 {len(existing_data)} 条现有地层数据")
    else:
        existing_data = {}
        print("未找到配置文件或未指定配置文件，将全部从CSV读取")
    
    # 读取CSV文件 - 使用带有BOM的UTF-8编码
    with open(csv_file_path, 'r', encoding='utf-8-sig') as csvfile:
        # 使用csv.DictReader读取数据，将第一行作为列名
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            # 提取地层名称作为键
            stratigraphic_name = row['地层名称']
            
            # 创建包含其他三个属性的字典
            csv_attributes = {
                '所属层位': row['所属层位'],
                '顶界所处位置（0~1）': row['顶界所处位置（0~1）'],
                '底界所处位置（0~1）': row['底界所处位置（0~1）']
            }
            
            # 根据更新策略决定如何处理数据
            if update_strategy == 'u':  # 以字典数据为准 (默认)
                if stratigraphic_name in existing_data:
                    # 保留现有数据，不更新
                    continue
                else:
                    # 添加新数据
                    result_dict[stratigraphic_name] = csv_attributes
            elif update_strategy == 'r':  # 以CSV数据为准
                result_dict[stratigraphic_name] = csv_attributes
    
    return result_dict

def save_json_file(data, output_file_path):
    """
    将数据保存为JSON文件
    """
    with open(output_file_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, ensure_ascii=False, indent=2)

def parse_arguments():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='CSV到JSON转换工具')
    parser.add_argument('-d', '--data-file', type=str, required=True,
                        help='输入CSV文件路径')
    parser.add_argument('-c', '--config-file', type=str,
                        help='配置文件路径 (stratigraphic_data.json)')
    parser.add_argument('-u', '--update-new-only', action='store_true',
                        help='只增加字典中不存在的项 (以字典数据为准，这是默认行为)')
    parser.add_argument('-r', '--replace-all', action='store_true',
                        help='以CSV文件的数据为准 (替换所有数据)')
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    
    # 确定更新策略
    if args.replace_all:
        update_strategy = 'r'  # 以CSV数据为准
    else:
        update_strategy = 'u'  # 以字典数据为准（默认）
    
    # 转换CSV到JSON字典
    json_dict = convert_csv_to_json(args.data_file, args.config_file, update_strategy)
    
    # 打印结果
    print(json.dumps(json_dict, ensure_ascii=False, indent=2))
    
    # 根据是否使用配置文件和更新策略生成输出文件名
    base_name = os.path.splitext(os.path.basename(args.data_file))[0]
    if args.config_file:
        # 如果使用了配置文件，根据策略添加后缀
        if args.replace_all:
            output_filename = f"{base_name}_with_config_r.json"  # 使用配置文件，CSV数据为准
        else:
            output_filename = f"{base_name}_with_config_u.json"  # 使用配置文件，配置数据为准
    else:
        # 如果没有使用配置文件
        output_filename = f"{base_name}.json"
    
    save_json_file(json_dict, output_filename)
    print(f"\n数据已保存到 {output_filename} 文件中")