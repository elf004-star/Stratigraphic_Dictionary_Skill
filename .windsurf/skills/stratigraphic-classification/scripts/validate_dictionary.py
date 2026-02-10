#!/usr/bin/env python3
"""
字典验证脚本
验证地层字典的完整性和一致性
"""

import json
import csv
import sys


class DictionaryValidator:
    """地层字典验证器"""
    
    def __init__(self, dict_file="stratigraphic_depth_statistics.json", 
                 datatest_file="CCQ_merged.csv", 
                 stratigraphic_file="地层分层.csv"):
        self.dict_file = dict_file
        self.datatest_file = datatest_file
        self.stratigraphic_file = stratigraphic_file
    
    def load_json_file(self, file_path):
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"错误：文件 {file_path} 不存在")
            return None
        except json.JSONDecodeError as e:
            print(f"错误：JSON文件格式不正确 - {e}")
            return None
    
    def load_datatest_formations(self, file_path):
        """从datatest CSV文件加载地层信息"""
        formations = set()
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    formations.add(row['起始地层'].strip())
                    formations.add(row['结束地层'].strip())
            return formations
        except FileNotFoundError:
            print(f"错误：文件 {file_path} 不存在")
            return None
        except KeyError as e:
            print(f"错误：CSV文件缺少必要的列 - {e}")
            return None
    
    def load_stratigraphic_formations(self, file_path):
        """从地层分层CSV文件加载地层信息"""
        formations = set()
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    formations.add(row['地层信息'].strip())
            return formations
        except FileNotFoundError:
            print(f"错误：文件 {file_path} 不存在")
            return None
        except KeyError as e:
            print(f"错误：地层分层CSV文件缺少必要的列 - {e}")
            return None
    
    def validate_dictionary(self, json_data, datatest_formations, stratigraphic_formations):
        """验证字典的完整性、一致性和数值范围"""
        errors = []
        
        if not json_data:
            errors.append("字典数据为空或加载失败")
            return errors
        
        if not datatest_formations:
            errors.append("datatest.csv数据为空或加载失败")
            return errors
        
        if not stratigraphic_formations:
            errors.append("地层分层.csv数据为空或加载失败")
            return errors
        
        # 验证字典完整性
        missing_in_dict = datatest_formations - set(json_data.keys())
        if missing_in_dict:
            errors.append(f"字典中缺少以下地层项：{list(missing_in_dict)}")
        
        # 验证字典一致性
        for formation in datatest_formations:
            if formation not in json_data:
                continue
            
            details = json_data[formation]
            if '所属层位' not in details:
                errors.append(f"地层 '{formation}' 缺少 '所属层位' 字段")
                continue
            
            parent_formation = details['所属层位']
            if parent_formation not in stratigraphic_formations:
                errors.append(f"地层 '{formation}' 的所属层位 '{parent_formation}' 不在地层分层信息中")
        
        # 验证数值范围
        for formation in datatest_formations:
            if formation not in json_data:
                continue
                
            details = json_data[formation]
            for field in ['顶界所处位置（0~1）', '底界所处位置（0~1）']:
                if field not in details:
                    errors.append(f"地层 '{formation}' 缺少 '{field}' 字段")
                    continue
                
                try:
                    value = float(details[field])
                    if not 0 <= value <= 1:
                        errors.append(f"地层 '{formation}' 的 '{field}' 值 {value} 不在范围(0~1)内")
                except ValueError:
                    errors.append(f"地层 '{formation}' 的 '{field}' 值 '{details[field]}' 不是有效的数字")
        
        return errors
    
    def check_dictionary(self):
        """执行字典检查"""
        print("开始检查字典文件...")
        
        # 加载文件
        json_data = self.load_json_file(self.dict_file)
        if json_data is None:
            return False
        
        datatest_formations = self.load_datatest_formations(self.datatest_file)
        if datatest_formations is None:
            return False
        
        stratigraphic_formations = self.load_stratigraphic_formations(self.stratigraphic_file)
        if stratigraphic_formations is None:
            return False
        
        print(f"datatest.csv文件中包含的地层数量: {len(datatest_formations)}")
        print(f"地层分层.csv文件中包含的地层数量: {len(stratigraphic_formations)}")
        print(f"字典文件中包含的地层数量: {len(json_data)}")
        
        # 显示加载成功的提示
        print("成功加载所有文件:")
        print(f"- {self.dict_file}: {len(json_data)} 个条目")
        print(f"- {self.datatest_file}: {len(datatest_formations)} 个地层")
        print(f"- {self.stratigraphic_file}: {len(stratigraphic_formations)} 个层位")
        
        # 检查未匹配的地层
        unmatched_in_datatest = datatest_formations - set(json_data.keys())
        if unmatched_in_datatest:
            print(f"\ndatatest.csv中有但字典中缺少的地层: {list(unmatched_in_datatest)}")
        
        # 获取所有在字典中作为'所属层位'使用的层位
        used_as_parent = set()
        for formation, details in json_data.items():
            if '所属层位' in details:
                used_as_parent.add(details['所属层位'])
        
        unmatched_in_stratigraphic = stratigraphic_formations - used_as_parent
        if unmatched_in_stratigraphic:
            print(f"\n地层分层.csv中有但字典中没有作为所属层位的地层: {list(unmatched_in_stratigraphic)}")
        
        # 执行验证
        errors = self.validate_dictionary(json_data, datatest_formations, stratigraphic_formations)
        
        # 输出结果
        if errors:
            print("\n发现以下错误：")
            for i, error in enumerate(errors, 1):
                print(f"{i}. {error}")
            print(f"\n总共发现 {len(errors)} 个错误。")
            
            print("\n修复建议:")
            print("- 对于'所属层位不在地层分层信息中'的问题，您需要：")
            print("  a) 将缺失的层位添加到地层分层.csv文件中，或者")
            print("  b) 修改这些地层的所属层位为地层分层.csv中存在的层位")
            print("- 确保所有数值字段都在0到1之间")
            print("- 确保所有必需的字段都存在")
            return False
        else:
            print("\n字典检查通过，没有发现问题！")
            return True


if __name__ == "__main__":
    validator = DictionaryValidator()
    success = validator.check_dictionary()
    
    if not success:
        sys.exit(1)
