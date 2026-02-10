import pandas as pd
import json
import numpy as np
import os
import sys
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP

# 程序版本信息
VERSION = "1.0.0"


def show_help():
    """
    显示帮助信息
    """
    help_text = f"""GoldData Perspective - CSV数据透视工具

用法:
  python main.py [选项] <文件路径或文件夹路径>

选项:
  -h, --help          显示此帮助信息
  -v, --version       显示程序版本
  -c, --config        指定配置文件路径

参数:
  <文件路径或文件夹路径>  要处理的CSV文件路径或包含CSV文件的文件夹路径

示例:
  python main.py data.csv                     # 处理单个CSV文件
  python main.py ./data_folder                # 处理文件夹中的所有CSV文件
  python main.py -c my_config.json data.csv   # 使用自定义配置文件处理CSV文件
  python main.py --help                       # 显示帮助信息
  python main.py --version                    # 显示版本信息
"""
    print(help_text)


def show_version():
    """
    显示程序版本信息
    """
    print(f"GoldData Perspective v{VERSION}")


def round_value(value, decimals=2):
    """
    保留指定位数的小数或有效数字
    """
    if pd.isna(value):
        return value
    # 转换为Decimal类型进行精确四舍五入
    d = Decimal(str(value))
    # 保留2位小数
    rounded = d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return float(rounded)


def weighted_average(group, value_col, weight_col):
    """
    计算加权平均值
    """
    # 过滤掉NaN值
    valid_data = group[[value_col, weight_col]].dropna()
    
    if len(valid_data) == 0:
        return np.nan
    
    values = valid_data[value_col]
    weights = valid_data[weight_col]
    
    # 避免除零错误
    if weights.sum() == 0 or len(weights) == 0:
        return np.nan
    
    # 检查是否有无穷大值
    if np.isinf(weights.sum()) or np.isinf((values * weights).sum()):
        # 尝试移除无穷大值
        mask = np.isfinite(values) & np.isfinite(weights)
        if mask.any():
            values = values[mask]
            weights = weights[mask]
        else:
            return np.nan
    
    result = (values * weights).sum() / weights.sum()
    return round_value(result)


def find_config_file(cmd_config=None):
    """
    按优先级查找配置文件
    优先级: 命令行指定 > 当前目录 > 用户目录
    """
    import os
    from pathlib import Path
    
    # 优先级1: 命令行指定的配置文件
    if cmd_config and os.path.exists(cmd_config):
        return cmd_config
    
    # 优先级2: 当前目录下的perspective.config.json
    current_dir_config = 'perspective.config.json'
    if os.path.exists(current_dir_config):
        return current_dir_config
    
    # 优先级3: 用户目录下的.CCQ.config/perspective.config.json
    user_home = Path.home()
    user_config = user_home / '.CCQ.config' / 'perspective.config.json'
    if user_config.exists():
        return str(user_config)
    
    # 如果都没有找到，返回None
    return None


def load_config(config_file=None):
    """
    加载配置文件，如果config_file为None，则自动按优先级查找
    """
    if config_file:
        # 如果直接传入了配置文件路径
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        else:
            raise FileNotFoundError(f"配置文件不存在: {config_file}")
    else:
        # 自动按优先级查找配置文件
        found_config = find_config_file()
        if found_config:
            with open(found_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        else:
            raise FileNotFoundError("无法找到配置文件！请确保配置文件存在于以下任一位置：\n"
                                  "1. 使用-c参数指定的路径\n"
                                  "2. 当前目录下的perspective.config.json\n"
                                  "3. 用户目录下的.CCQ.config/perspective.config.json")


def validate_headers(df, required_columns):
    """
    验证DataFrame是否包含所需的列
    """
    df_columns = set(df.columns)
    required_columns_set = set(required_columns)
    missing_columns = required_columns_set - df_columns
    if missing_columns:
        print(f"警告: 缺少以下必要列: {list(missing_columns)}")
        return False
    return True


def process_single_file(file_path, config):
    """
    处理单个CSV文件
    """
    try:
        print(f"正在处理: {file_path}")
        
        # 读取CSV文件
        df = pd.read_csv(file_path, encoding='utf-8')
        print(f"  - 成功读取文件，共有 {len(df)} 行数据")
        
        # 验证表头是否符合要求
        selected_columns = config['selected_columns']
        if not validate_headers(df, selected_columns):
            print(f"跳过文件 {file_path}: 缺少必要的列")
            return False
        
        # 选择指定的列
        df_selected = df[selected_columns].copy()
        print(f"  - 已选择 {len(selected_columns)} 列进行处理")
        
        # 重命名列
        rename_dict = config.get('rename_columns', {})
        df_selected.rename(columns=rename_dict, inplace=True)
        if rename_dict:
            print(f"  - 已重命名列: {rename_dict}")
        
        # 验证重命名后的数据列是否存在
        pivot_settings = config['pivot_settings']
        group_by_col = pivot_settings['group_by']
        aggregations = pivot_settings['aggregations']
        
        # 检查分组列是否存在
        if group_by_col not in df_selected.columns:
            print(f"跳过文件 {file_path}: 分组列 '{group_by_col}' 不存在")
            return False
        
        # 检查聚合列是否存在
        for col in aggregations.keys():
            if col not in df_selected.columns:
                print(f"跳过文件 {file_path}: 聚合列 '{col}' 不存在")
                return False
        
        # 创建权重列
        weight_expr = pivot_settings['weight_column']  # 例如："置信度*进尺命中率"
        if '*' in weight_expr:
            cols = weight_expr.split('*')
            col1 = cols[0].strip()
            col2 = cols[1].strip()
            
            # 检查权重计算所需的列是否存在
            if col1 not in df_selected.columns or col2 not in df_selected.columns:
                print(f"跳过文件 {file_path}: 权重计算所需列不存在 ({col1} 或 {col2})")
                return False
            
            # 确保权重计算列是数值型
            df_selected[col1] = pd.to_numeric(df_selected[col1], errors='coerce')
            df_selected[col2] = pd.to_numeric(df_selected[col2], errors='coerce')
            df_selected['权重'] = df_selected[col1] * df_selected[col2]
            print(f"  - 已创建权重列，使用表达式: {col1} * {col2}")
        else:
            if weight_expr not in df_selected.columns:
                print(f"跳过文件 {file_path}: 权重列 '{weight_expr}' 不存在")
                return False
            df_selected['权重'] = pd.to_numeric(df_selected[weight_expr], errors='coerce')
            print(f"  - 已使用列 '{weight_expr}' 作为权重列")
        
        # 确保需要聚合的列是数值型（对于加权平均）
        for col, method in aggregations.items():
            if method == 'weighted_average' and col in df_selected.columns:
                df_selected[col] = pd.to_numeric(df_selected[col], errors='coerce')
        
        # 执行数据透视
        # 准备聚合函数字典
        agg_funcs = {}
        for col, method in aggregations.items():
            if method == 'weighted_average':
                # 对于加权平均，我们需要特殊处理
                continue
            elif method == 'max':
                agg_funcs[col] = 'max'
            elif method == 'mean':
                agg_funcs[col] = 'mean'
            elif method == 'sum':
                agg_funcs[col] = 'sum'
            elif method == 'min':
                agg_funcs[col] = 'min'
            elif method == 'count':
                agg_funcs[col] = 'count'
        
        # 分组聚合
        if agg_funcs:
            result_df = df_selected.groupby(group_by_col).agg(agg_funcs).reset_index()
            print(f"  - 完成基本聚合操作")
        else:
            result_df = df_selected.groupby(group_by_col).first().reset_index()
            print(f"  - 完成分组操作")
        
        # 处理加权平均的列
        for col, method in aggregations.items():
            if method == 'weighted_average':
                # 重新计算加权平均值
                weighted_avg_values = []
                for label in result_df[group_by_col]:
                    group_data = df_selected[df_selected[group_by_col] == label]
                    w_avg = weighted_average(group_data, col, '权重')
                    weighted_avg_values.append(w_avg)
                result_df[col] = weighted_avg_values
        
        # 对数值列进行四舍五入处理（保留2位小数）
        numeric_columns = result_df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if col != group_by_col:  # 不对分组列进行处理
                result_df[col] = result_df[col].apply(lambda x: round_value(x))
        
        # 去除不需要的列
        columns_to_remove = config.get('columns_to_remove', [])
        for col in columns_to_remove:
            if col in result_df.columns:
                result_df.drop(columns=[col], inplace=True)
        
        # 按照指定顺序排列列
        final_columns = config.get('final_columns', list(result_df.columns))
        result_df = result_df[final_columns]
        
        # 按序号从小到大排序
        if '序号' in result_df.columns:
            result_df = result_df.sort_values(by=['序号']).reset_index(drop=True)
        
        # 生成输出文件名
        input_file_name = Path(file_path).stem
        output_dir = Path(file_path).parent
        output_file = output_dir / f"{input_file_name}_透视结果.csv"
        
        # 保存结果，使用UTF-8 with BOM编码避免中文乱码
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            result_df.to_csv(f, index=False, encoding='utf-8-sig')
        
        print(f"文件 {file_path} 的数据透视完成！结果已保存至 {output_file}")
        return True
        
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {str(e)}")
        return False


def scan_directory_for_csv(directory, max_depth=3, current_depth=0):
    """
    递归扫描目录中的CSV文件（最多3层），排除已生成的透视结果文件
    """
    csv_files = []
    if current_depth >= max_depth:
        return csv_files
    
    for item in Path(directory).iterdir():
        if item.is_file() and item.suffix.lower() == '.csv':
            # 排除已经带有"_透视结果"后缀的文件
            if "_透视结果" not in item.stem:
                csv_files.append(str(item))
        elif item.is_dir() and current_depth < max_depth - 1:
            csv_files.extend(scan_directory_for_csv(item, max_depth, current_depth + 1))
    
    return csv_files


def main():
    # 获取命令行参数
    if len(sys.argv) < 2:
        show_help()
        return
    
    # 初始化参数
    config_file = None
    input_path = None
    
    # 解析命令行参数
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ['-h', '--help']:
            show_help()
            return
        elif arg in ['-v', '--version']:
            show_version()
            return
        elif arg in ['-c', '--config']:
            # 下一个参数应该是配置文件路径
            if i + 1 < len(sys.argv):
                config_file = sys.argv[i + 1]
                i += 2  # 跳过配置文件参数
            else:
                print("错误: -c/--config 参数后需要指定配置文件路径")
                return
        elif arg.startswith('-'):  # 其他未知参数
            print(f"错误: 未知参数 {arg}")
            show_help()
            return
        else:
            # 输入路径参数
            if input_path is None:
                input_path = arg
            else:
                print("错误: 只能指定一个输入路径")
                return
            i += 1
    
    # 检查是否提供了输入路径
    if input_path is None:
        print("错误: 必须提供输入文件路径或文件夹路径")
        show_help()
        return
    
    # 加载配置
    try:
        config = load_config(config_file)
    except FileNotFoundError as e:
        print(f"错误: {e}")
        return
    
    if os.path.isfile(input_path) and input_path.lower().endswith('.csv'):
        # 处理单个文件
        print(f"正在处理单个文件: {input_path}")
        process_single_file(input_path, config)
        
    elif os.path.isdir(input_path):
        # 处理文件夹
        print(f"正在处理文件夹: {input_path}，最多扫描3层")
        csv_files = scan_directory_for_csv(input_path)
        
        if not csv_files:
            print(f"在目录 {input_path} 中未找到任何CSV文件")
            return
        
        print(f"找到 {len(csv_files)} 个CSV文件，开始处理...")
        
        processed_count = 0
        skipped_count = 0
        
        for csv_file in csv_files:
            print(f"正在处理: {csv_file}")
            if process_single_file(csv_file, config):
                processed_count += 1
            else:
                skipped_count += 1
        
        print(f"\n处理完成！共处理 {processed_count} 个文件，跳过 {skipped_count} 个文件")
        



if __name__ == "__main__":
    main()