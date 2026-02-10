import pandas as pd
import json
import re
from typing import Dict, List, Union, Optional
import numpy as np
import os
import xml.etree.ElementTree as ET

# 版本信息
__version__ = "1.0.0"

# 研发团队信息
__author__ = "西南石油大学何世明、汤明团队"
__contact__ = "1873475824@qq.com（CCQ）"


def find_config_file(config_file: str) -> str:
    """
    查找配置文件，优先级：
    1. 当前目录下的配置文件
    2. 用户文件夹下的.CCQ.config/配置文件
    
    Args:
        config_file: 配置文件名
        
    Returns:
        找到的配置文件完整路径
        
    Raises:
        FileNotFoundError: 如果在任何位置都找不到配置文件
    """
    # 获取用户主目录
    import os.path
    user_dir = os.path.expanduser("~")
    user_config_dir = os.path.join(user_dir, ".CCQ.config")
    
    # 检查当前工作目录
    current_dir_path = os.path.join(os.getcwd(), config_file)
    if os.path.exists(current_dir_path):
        return current_dir_path
    
    # 检查用户配置目录
    user_config_path = os.path.join(user_config_dir, config_file)
    if os.path.exists(user_config_path):
        return user_config_path
    
    # 如果都没有找到，抛出异常
    raise FileNotFoundError(f"无法找到配置文件 '{config_file}'，已在以下位置查找：\n"
                          f"- 当前工作目录: {os.getcwd()}\n"
                          f"- 用户配置目录: {user_config_dir}")


class CSVProcessor:
    """
    处理具有双表头的CSV文件
    支持通过配置文件指定表头位置和处理规则
    """
    
    def __init__(self, config_file: str):
        """
        初始化处理器
        
        Args:
            config_file: 配置文件路径
        """
        # 使用增强的配置文件查找逻辑
        config_path = find_config_file(config_file)
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.header_definition = self.config.get('header_definition', {})
        self.data_start_row = self.config.get('data_start_row', 3)
        self.processing_options = self.config.get('processing_options', {})
        self.output_headers_mapping = self.config.get('output_headers_mapping', {})
    
    def _get_header_from_row(self, df: pd.DataFrame, row_index: int) -> List[str]:
        """
        从指定行获取表头
        
        Args:
            df: DataFrame对象
            row_index: 行索引（从0开始）
            
        Returns:
            表头列表
        """
        if row_index >= len(df):
            raise ValueError(f"Row index {row_index} exceeds DataFrame length {len(df)}")
        
        header = df.iloc[row_index].astype(str).fillna('').tolist()
        # 处理换行符
        header = [str(h).replace('\\n', '\n').replace('\n', '_') for h in header]
        return header
    
    def _parse_excel_xml(self, file_path: str) -> pd.DataFrame:
        """
        解析Excel 2003 XML格式文件
        
        Args:
            file_path: XML格式的Excel文件路径
            
        Returns:
            DataFrame对象
        """
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # 定义命名空间
        namespaces = {
            'ss': 'urn:schemas-microsoft-com:office:spreadsheet',
            'x': 'urn:schemas-microsoft-com:office:excel',
            'o': 'urn:schemas-microsoft-com:office:office'
        }
        
        rows_data = []
        
        # 查找所有的Worksheet
        worksheets = root.findall('.//ss:Worksheet', namespaces)
        
        # 取第一个worksheet进行处理
        if worksheets:
            worksheet = worksheets[0]
            # 查找所有行
            rows = worksheet.findall('.//ss:Row', namespaces)
            
            for row in rows:
                row_data = []
                cells = row.findall('.//ss:Cell', namespaces)
                
                for cell in cells:
                    # 获取单元格的值
                    data_elem = cell.find('ss:Data', namespaces)
                    if data_elem is not None:
                        row_data.append(data_elem.text if data_elem.text else '')
                    else:
                        # 如果没有找到ss:Data，尝试直接获取文本
                        if cell.text:
                            row_data.append(cell.text)
                        else:
                            row_data.append('')
                
                rows_data.append(row_data)
        
        # 创建DataFrame
        if rows_data:
            # 计算最大列数以确保所有行长度一致
            max_cols = max(len(row) for row in rows_data) if rows_data else 0
            # 补齐每行到相同的长度
            for row in rows_data:
                while len(row) < max_cols:
                    row.append('')
            df = pd.DataFrame(rows_data, dtype=str)
        else:
            df = pd.DataFrame()
        
        return df
    
    def _get_header_from_letters(self, letters_str: str) -> List[str]:
        """
        从字母字符串获取表头（如 A,B,C）
        
        Args:
            letters_str: 字母字符串
            
        Returns:
            表头列表
        """
        letters = [letter.strip().upper() for letter in letters_str.split(',')]
        headers = []
        for letter in letters:
            # 将字母转换为列索引
            col_idx = 0
            for char in letter:
                col_idx = col_idx * 26 + (ord(char) - ord('A') + 1)
            headers.append(f"Column_{col_idx}")
        return headers
    

    
    def load_and_process_csv(self, csv_file: str) -> pd.DataFrame:
        """
        加载并处理CSV或Excel文件
        
        Args:
            csv_file: CSV或Excel文件路径
            
        Returns:
            处理后的DataFrame
        """
        # 根据文件扩展名和实际内容选择适当的读取方法
        file_ext = os.path.splitext(csv_file)[1].lower()
        
        # 检测文件是否为XML格式（即使扩展名为.xls）
        with open(csv_file, 'rb') as f:
            first_bytes = f.read(100)
            is_xml_format = b'<?xml' in first_bytes or b'<Workbook' in first_bytes or b'<table' in first_bytes
        
        if is_xml_format:
            # 专门处理Excel 2003 XML格式文件
            df = self._parse_excel_xml(csv_file)
        elif file_ext in ['.xlsx', '.xls']:
            # 使用pandas读取Excel文件，根据文件扩展名指定引擎
            try:
                if file_ext == '.xls':
                    # 尝试使用xlrd引擎读取.xls文件
                    df = pd.read_excel(csv_file, header=None, engine='xlrd')
                elif file_ext == '.xlsx':
                    # 使用openpyxl引擎读取.xlsx文件
                    df = pd.read_excel(csv_file, header=None, engine='openpyxl')
            except Exception:
                # 如果指定引擎失败，尝试不指定引擎，让pandas自动检测
                df = pd.read_excel(csv_file, header=None)
        elif file_ext == '.xml':
            # 对于.xml文件，直接作为CSV读取（因为可能是XML格式的表格数据）
            df = pd.read_csv(csv_file, header=None)
        else:
            # 读取整个CSV文件，允许多行单元格
            df = pd.read_csv(csv_file, header=None, quoting=1)  # quoting=1 means QUOTE_ALL
        
        # 获取第一表头
        if self.header_definition['method'] == 'row':
            row_idx = self.header_definition['value'] - 1  # 转换为0基索引
            primary_header = self._get_header_from_row(df, row_idx)
        elif self.header_definition['method'] == 'letter':
            primary_header = self._get_header_from_letters(self.header_definition['value'])
        else:
            raise ValueError(f"Unsupported header method: {self.header_definition['method']}")
        
        # 直接使用第一表头作为最终表头
        combined_header = primary_header
        
        # 提取数据部分
        # 无论第二表头如何定义，data_start_row 都指向真实数据的起始行
        data_df = df.iloc[self.data_start_row-1:].copy()
        
        data_df.columns = combined_header
        
        # 应用列提取（如果启用）
        if 'columns_to_extract' in self.config and self.config['columns_to_extract']['enabled']:
            extraction_config = self.config['columns_to_extract']
            if extraction_config['method'] == 'letter':
                # 将字母转换为数字索引
                col_indices = []
                for letter in extraction_config['columns']:
                    # 检查是否使用$符号包围的列引用格式
                    if letter.startswith('$') and letter.endswith('$'):
                        # 移除$符号，只保留字母部分
                        clean_letter = letter[1:-1]
                    else:
                        clean_letter = letter
                    
                    col_idx = 0
                    for char in clean_letter.upper():
                        col_idx = col_idx * 26 + (ord(char) - ord('A') + 1)
                    col_indices.append(col_idx - 1)  # 转换为0基索引
                
                # 提取指定列
                selected_data = []
                for idx in col_indices:
                    if idx < len(combined_header):
                        selected_data.append(data_df.iloc[:, idx])
                    else:
                        # 如果索引超出范围，添加一个空列
                        selected_data.append(pd.Series([None] * len(data_df), name=f"Col_{idx}"))
                
                # 创建新的DataFrame
                extracted_df = pd.concat(selected_data, axis=1)
                
                # 设置新的列名，如果 new_headers 中有空字符串，则使用原来的列名
                new_column_names = []
                for i, col in enumerate(extracted_df.columns):
                    if i < len(extraction_config['new_headers']) and extraction_config['new_headers'][i] != "":
                        new_column_names.append(extraction_config['new_headers'][i])
                    else:
                        # 如果 new_headers[i] 是空字符串或者索引超出了范围，使用原来的列名
                        if i < len(combined_header):
                            # 如果原始表头名不为空，则使用原始表头名；否则使用字母（去除$符号）
                            original_header = combined_header[i]
                            if original_header and str(original_header).strip() != '':
                                new_column_names.append(original_header)
                            else:
                                # 如果原始表头名为空，使用字母（从配置中获取并去除$符号）
                                if i < len(extraction_config['columns']):
                                    letter = extraction_config['columns'][i]
                                    if letter.startswith('$') and letter.endswith('$'):
                                        # 去除$符号，只保留字母部分
                                        clean_letter = letter[1:-1]
                                        new_column_names.append(clean_letter)
                                    else:
                                        new_column_names.append(letter)
                                else:
                                    new_column_names.append(col)
                        else:
                            new_column_names.append(col)
                
                extracted_df.columns = new_column_names
                data_df = extracted_df
            elif extraction_config['method'] == 'name':
                # 按列名提取，处理重复列名
                selected_data = []
                used_headers = []  # 用于跟踪已使用的列名，以处理重复情况
                
                for i, col_name in enumerate(extraction_config['columns']):
                    if col_name in data_df.columns:
                        col_data = data_df[col_name]
                        
                        # 检查是否是 Series（单列）还是 DataFrame（多列，因为有重复列名）
                        if isinstance(col_data, pd.DataFrame):
                            # 如果是 DataFrame，说明有多个同名列
                            for j, series in enumerate(col_data.items()):
                                col_idx, series_data = series
                                # 确定对应的新列名
                                if 'new_headers' in extraction_config and i+j < len(extraction_config['new_headers']) and extraction_config['new_headers'][i] != "":
                                    if j == 0:
                                        new_header = extraction_config['new_headers'][i]
                                    else:
                                        new_header = f"{extraction_config['new_headers'][i]}{j}"
                                else:
                                    new_header = f"{col_name}{j}" if j > 0 else col_name
                                
                                # 确保新列名唯一
                                while new_header in used_headers:
                                    new_header += "_dup"
                                
                                series_data.name = new_header
                                selected_data.append(series_data)
                                used_headers.append(new_header)
                        else:
                            # 如果是 Series（单列），正常处理
                            if 'new_headers' in extraction_config and i < len(extraction_config['new_headers']) and extraction_config['new_headers'][i] != "":
                                new_header = extraction_config['new_headers'][i]
                            else:
                                new_header = col_name
                            
                            # 确保新列名唯一
                            original_header = new_header
                            counter = 0
                            while new_header in used_headers:
                                counter += 1
                                new_header = f"{original_header}{counter}"
                            
                            col_data.name = new_header
                            selected_data.append(col_data)
                            used_headers.append(new_header)
                    else:
                        # 如果列不存在，添加一个空列
                        if 'new_headers' in extraction_config and i < len(extraction_config['new_headers']) and extraction_config['new_headers'][i] != "":
                            new_header = extraction_config['new_headers'][i]
                        else:
                            new_header = col_name
                        
                        # 确保新列名唯一
                        original_header = new_header
                        counter = 0
                        while new_header in used_headers:
                            counter += 1
                            new_header = f"{original_header}{counter}"
                        
                        empty_series = pd.Series([None] * len(data_df), name=new_header)
                        selected_data.append(empty_series)
                        used_headers.append(new_header)
                
                # 创建新的DataFrame
                extracted_df = pd.concat(selected_data, axis=1)
                data_df = extracted_df
            elif extraction_config['method'] == 'auto':
                # 自动模式：通过$符号识别是字母还是名称
                selected_data = []
                used_headers = []  # 用于跟踪已使用的列名，以处理重复情况
                
                for i, col_identifier in enumerate(extraction_config['columns']):
                    # 检查是否是用$符号包围的字母格式（如$C$, $E$）
                    if isinstance(col_identifier, str) and col_identifier.startswith('$') and col_identifier.endswith('$'):
                        # 这是字母模式，转换为索引
                        clean_letter = col_identifier[1:-1]
                        col_idx = 0
                        for char in clean_letter.upper():
                            col_idx = col_idx * 26 + (ord(char) - ord('A') + 1)
                        actual_idx = col_idx - 1  # 转换为0基索引
                        
                        if actual_idx < len(combined_header):
                            col_data = data_df.iloc[:, actual_idx]
                        else:
                            # 如果索引超出范围，使用空列
                            col_data = pd.Series([None] * len(data_df))
                    else:
                        # 这是名称模式，直接按列名提取
                        if col_identifier in data_df.columns:
                            col_data = data_df[col_identifier]
                        else:
                            # 如果列不存在，使用空列
                            col_data = pd.Series([None] * len(data_df))
                    
                    # 处理单列或多列的情况
                    if isinstance(col_data, pd.DataFrame):
                        # 如果是 DataFrame，说明有多个同名列
                        for j, (col_name_in_df, series_data) in enumerate(col_data.items()):
                            if 'new_headers' in extraction_config and i+j < len(extraction_config['new_headers']) and extraction_config['new_headers'][i] != "":
                                if j == 0:
                                    new_header = extraction_config['new_headers'][i]
                                else:
                                    new_header = f"{extraction_config['new_headers'][i]}{j}"
                            else:
                                # 如果 new_headers 为空字符串或超出范围，需要根据标识符类型决定使用什么名称
                                if isinstance(col_identifier, str) and col_identifier.startswith('$') and col_identifier.endswith('$'):
                                    # 这是字母格式（如 $D$），尝试使用原始表头名
                                    clean_letter = col_identifier[1:-1]
                                    col_idx = 0
                                    for char in clean_letter.upper():
                                        col_idx = col_idx * 26 + (ord(char) - ord('A') + 1)
                                    actual_idx = col_idx - 1  # 转换为0基索引
                                    
                                    if actual_idx < len(combined_header):
                                        original_header = combined_header[actual_idx]
                                        if original_header and str(original_header).strip() != '':
                                            new_header = original_header
                                        else:
                                            # 如果原始表头名为空，使用字母（去除$符号）
                                            new_header = clean_letter
                                    else:
                                        new_header = f"{col_identifier}{j}" if j > 0 else str(col_identifier)
                                else:
                                    # 这是名称格式，直接使用原标识符
                                    new_header = f"{col_identifier}{j}" if j > 0 else str(col_identifier)
                            
                            # 确保新列名唯一
                            original_header_for_uniqueness = new_header
                            counter = 0
                            while new_header in used_headers:
                                counter += 1
                                new_header = f"{original_header_for_uniqueness}{counter}"
                            
                            series_data.name = new_header
                            selected_data.append(series_data)
                            used_headers.append(new_header)
                    else:
                        # 如果是 Series（单列），正常处理
                        if 'new_headers' in extraction_config and i < len(extraction_config['new_headers']) and extraction_config['new_headers'][i] != "":
                            new_header = extraction_config['new_headers'][i]
                        else:
                            # 如果 new_headers 为空字符串或超出范围，需要根据标识符类型决定使用什么名称
                            if isinstance(col_identifier, str) and col_identifier.startswith('$') and col_identifier.endswith('$'):
                                # 这是字母格式（如 $D$），尝试使用原始表头名
                                clean_letter = col_identifier[1:-1]
                                col_idx = 0
                                for char in clean_letter.upper():
                                    col_idx = col_idx * 26 + (ord(char) - ord('A') + 1)
                                actual_idx = col_idx - 1  # 转换为0基索引
                                
                                if actual_idx < len(combined_header):
                                    original_header = combined_header[actual_idx]
                                    if original_header and str(original_header).strip() != '':
                                        new_header = original_header
                                    else:
                                        # 如果原始表头名为空，使用字母（去除$符号）
                                        new_header = clean_letter
                                else:
                                    new_header = str(col_identifier)
                            else:
                                # 这是名称格式，直接使用原标识符
                                new_header = str(col_identifier)
                        
                        # 确保新列名唯一
                        original_header_for_uniqueness = new_header
                        counter = 0
                        while new_header in used_headers:
                            counter += 1
                            new_header = f"{original_header_for_uniqueness}{counter}"
                        
                        col_data.name = new_header
                        selected_data.append(col_data)
                        used_headers.append(new_header)
                
                # 创建新的DataFrame
                extracted_df = pd.concat(selected_data, axis=1)
                data_df = extracted_df
            else:
                raise ValueError(f"Unsupported column extraction method: {extraction_config['method']}")
        
        # 应用处理选项
        processed_df = self._apply_processing_options(data_df)
        
        # 重命名列（如果在映射中有定义）
        rename_dict = {}
        for old_col in processed_df.columns:
            if old_col in self.output_headers_mapping:
                rename_dict[old_col] = self.output_headers_mapping[old_col]
        
        processed_df.rename(columns=rename_dict, inplace=True)
        
        return processed_df
    
    def _apply_processing_options(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        应用处理选项
        
        Args:
            df: 输入DataFrame
            
        Returns:
            处理后的DataFrame
        """
        result_df = df.copy()
        
        # 移除空行 - 支持按列设置
        remove_empty_rows_config = self.processing_options.get('remove_empty_rows', {})
        if isinstance(remove_empty_rows_config, dict) and remove_empty_rows_config.get('enabled', False):
            # 按列设置移除空行
            target_cols = remove_empty_rows_config.get('columns', [])
            if target_cols:
                # 只检查指定列是否为空
                mask = pd.Series([False] * len(result_df), index=result_df.index)
                for col in target_cols:
                    if col in result_df.columns:
                        mask |= result_df[col].isna() | (result_df[col] == '') | (result_df[col].astype(str).str.strip() == '')
                # 保留不全是空值的行
                result_df = result_df[~mask]
            else:
                # 如果没有指定列，则对整个行进行检查
                result_df = result_df.dropna(how='all')
        elif remove_empty_rows_config is True or (isinstance(remove_empty_rows_config, bool) and remove_empty_rows_config):
            # 保持向后兼容：如果配置是布尔值True，则移除所有空行
            result_df = result_df.dropna(how='all')
        
        # 移除无效数值行 - 支持按列设置
        remove_invalid_number_rows_config = self.processing_options.get('remove_invalid_number_rows', {})
        if isinstance(remove_invalid_number_rows_config, dict) and remove_invalid_number_rows_config.get('enabled', False):
            # 按列设置移除无效数值行
            target_cols = remove_invalid_number_rows_config.get('columns', [])
            for col in target_cols:
                if col in result_df.columns:
                    # 检查列是否包含有效数值
                    numeric_mask = pd.to_numeric(result_df[col], errors='coerce').notna()
                    result_df = result_df[numeric_mask]
        elif remove_invalid_number_rows_config is True or (isinstance(remove_invalid_number_rows_config, bool) and remove_invalid_number_rows_config):
            # 保持向后兼容：如果配置是布尔值True，则对所有数值列移除无效数值
            numeric_cols = []
            for col in result_df.columns:
                try:
                    pd.to_numeric(result_df[col])
                    numeric_cols.append(col)
                except (ValueError, TypeError):
                    continue
            
            for col in numeric_cols:
                result_df = result_df[pd.to_numeric(result_df[col], errors='coerce').notna()]
        
        # 列拆分
        if 'column_splitting' in self.processing_options:
            for split_config in self.processing_options['column_splitting']:
                source_col = split_config['source_column']
                delimiter = split_config['delimiter']
                new_cols = split_config['new_columns']
                
                if source_col in result_df.columns:
                    # 拆分列
                    split_data = result_df[source_col].astype(str).str.split(delimiter, expand=True)
                    
                    # 确保有足够的新列来存储拆分结果
                    if len(new_cols) <= split_data.shape[1]:
                        # 如果新列数少于拆分结果列数，只取前几个
                        split_data = split_data.iloc[:, :len(new_cols)]
                        for i, new_col in enumerate(new_cols):
                            result_df[new_col] = split_data.iloc[:, i] if i < split_data.shape[1] else None
                    else:
                        # 如果新列数多于拆分结果列数，填充None
                        for i, new_col in enumerate(new_cols):
                            if i < split_data.shape[1]:
                                result_df[new_col] = split_data.iloc[:, i]
                            else:
                                result_df[new_col] = None

        # 数值范围过滤 - 新的filters数组配置（在列拆分之后执行）
        if 'numeric_range_filter' in self.processing_options:
            filter_config = self.processing_options['numeric_range_filter']
            if filter_config.get('enabled', False):
                # 检查是否有filters数组（新配置格式）
                if 'filters' in filter_config:
                    # 使用新的filters数组配置
                    for filter_item in filter_config['filters']:
                        min_val = filter_item.get('min_value', float('-inf'))
                        max_val = filter_item.get('max_value', float('inf'))
                        target_cols = filter_item.get('columns', [])  # 获取目标列列表
                        
                        # 对指定的列进行过滤
                        for col in target_cols:
                            if col in result_df.columns:
                                # 转换为数值型，保留NaN值，这样我们可以区分无效值和有效值（包括0）
                                numeric_series = pd.to_numeric(result_df[col], errors='coerce')
                                
                                # 创建掩码：NaN值保留（不被过滤），数值值检查范围
                                # 这里特别注意：NaN值不会通过 >= 或 <= 比较，因此我们需要单独处理
                                is_valid_number = numeric_series.notna()  # 有效的数值（包括0）
                                is_in_range = (numeric_series >= min_val) & (numeric_series <= max_val)  # 在范围内的值
                                
                                # 同时满足：是有效数值 且 在范围内
                                mask = is_valid_number & is_in_range
                                
                                result_df = result_df[mask]
                else:
                    # 使用旧的配置格式（向后兼容）
                    min_val = filter_config.get('min_value', float('-inf'))
                    max_val = filter_config.get('max_value', float('inf'))
                    target_cols = filter_config.get('columns', [])  # 获取目标列列表
                    
                    # 如果没有指定特定列，则对所有数值列进行过滤
                    if not target_cols:
                        # 找到所有数值列
                        numeric_cols = []
                        for col in result_df.columns:
                            try:
                                pd.to_numeric(result_df[col])
                                numeric_cols.append(col)
                            except (ValueError, TypeError):
                                continue
                        
                        # 过滤数值列
                        for col in numeric_cols:
                            numeric_series = pd.to_numeric(result_df[col], errors='coerce')
                            
                            # 创建掩码：NaN值保留（不被过滤），数值值检查范围
                            is_valid_number = numeric_series.notna()  # 有效的数值（包括0）
                            is_in_range = (numeric_series >= min_val) & (numeric_series <= max_val)  # 在范围内的值
                            
                            # 同时满足：是有效数值 且 在范围内
                            mask = is_valid_number & is_in_range
                            
                            result_df = result_df[mask]
                    else:
                        # 如果指定了特定列，则对这些列进行过滤
                        # 只对指定的列进行过滤
                        for col in target_cols:
                            if col in result_df.columns:
                                numeric_series = pd.to_numeric(result_df[col], errors='coerce')
                                
                                # 创建掩码：NaN值保留（不被过滤），数值值检查范围
                                is_valid_number = numeric_series.notna()  # 有效的数值（包括0）
                                is_in_range = (numeric_series >= min_val) & (numeric_series <= max_val)  # 在范围内的值
                                
                                # 同时满足：是有效数值 且 在范围内
                                mask = is_valid_number & is_in_range
                                
                                result_df = result_df[mask]
        
        # 排序功能
        if 'sorting' in self.processing_options:
            sorting_config = self.processing_options['sorting']
            if sorting_config.get('enabled', False):
                sort_columns = sorting_config.get('columns', [])
                if sort_columns:
                    # 准备排序参数
                    sort_params = []  # 存储 (列名, 排序方向) 对
                    
                    for sort_item in sort_columns:
                        if isinstance(sort_item, dict):
                            col_name = sort_item.get('column')
                            ascending = sort_item.get('ascending', True)
                        else:
                            # 兼容简单字符串格式
                            col_name = sort_item
                            ascending = True
                        
                        if col_name and col_name in result_df.columns:
                            sort_params.append((col_name, ascending))
                    
                    if sort_params:
                        # 执行排序
                        result_df.sort_values(
                            by=[col for col, _ in sort_params],
                            ascending=[asc for _, asc in sort_params],
                            inplace=True
                        )
        
        return result_df


def main():
    """
    命令行入口点
    """
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='CSV/Excel处理器')
    parser.add_argument('input_file', help='输入文件路径（CSV/XLS/XLSX）')
    parser.add_argument('-c', '--config', default='processor.config.json', 
                        help='配置文件路径（默认：processor.config.json）')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-f', '--format', choices=['csv', 'excel', 'json'], default='csv',
                        help='输出格式（默认：csv）')
    
    args = parser.parse_args()
    
    # 创建处理器
    processor = CSVProcessor(args.config)
    
    # 处理文件
    result_df = processor.load_and_process_csv(args.input_file)
    
    # 添加序号列（如果还没有的话）
    if '序号' not in result_df.columns:
        result_df.insert(0, '序号', range(1, len(result_df) + 1))
    
    # 确定输出文件路径
    if args.output:
        output_file = args.output
    else:
        base_name = os.path.splitext(args.input_file)[0]
        if args.format == 'csv':
            output_file = f"{base_name}_processed.csv"
        elif args.format == 'excel':
            output_file = f"{base_name}_processed.xlsx"
        else:
            output_file = f"{base_name}_processed.json"
    
    # 保存结果
    if args.format == 'csv':
        result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    elif args.format == 'excel':
        result_df.to_excel(output_file, index=False, engine='openpyxl')
    else:
        result_df.to_json(output_file, orient='records', force_ascii=False, indent=2)
    
    print(f"处理完成！输出文件：{output_file}")
    print(f"共处理 {len(result_df)} 行数据")


if __name__ == "__main__":
    main()
