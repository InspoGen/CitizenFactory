#!/usr/bin/env python3
"""
批量导入地址工具
支持从文本文件导入住宅地址和学校地址
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Any, Tuple, Optional


class AddressImporter:
    """地址导入器"""
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化导入器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self.addresses_file = os.path.join(data_dir, "addresses", "US_addresses.json")
        self.schools_file = os.path.join(data_dir, "schools", "US_schools.json")
    
    def parse_address(self, address_line: str) -> Optional[Tuple[str, str, str, str]]:
        """
        解析地址字符串
        
        Args:
            address_line: 地址字符串
            
        Returns:
            (street, city, state, zip_code) 或 None
        """
        # 移除首尾空格
        address_line = address_line.strip()
        if not address_line:
            return None
        
        # 正则表达式匹配地址格式：Street, City, STATE ZIP 或 Street, City, STATE ZIP-XXXX
        pattern = r'^(.+?),\s*(.+?),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$'
        match = re.match(pattern, address_line)
        
        if match:
            street, city, state, zip_code = match.groups()
            return street.strip(), city.strip(), state.strip(), zip_code.strip()
        else:
            print(f"警告: 无法解析地址格式: {address_line}", file=sys.stderr)
            return None
    
    def parse_school_line(self, school_line: str) -> Optional[Dict[str, str]]:
        """
        解析学校信息字符串
        格式: School Name|Abbreviation|Type|Address
        其中 Type 为 high_school 或 college
        
        Args:
            school_line: 学校信息字符串
            
        Returns:
            学校信息字典或None
        """
        school_line = school_line.strip()
        if not school_line:
            return None
        
        parts = school_line.split('|')
        if len(parts) < 4:
            print(f"警告: 学校信息格式不正确: {school_line}", file=sys.stderr)
            print("正确格式: School Name|Abbreviation|Type|Address")
            print("其中 Type 应为 high_school 或 college")
            return None
        
        name = parts[0].strip()
        abbreviation = parts[1].strip()
        school_type = parts[2].strip().lower()
        address = parts[3].strip()
        
        if school_type not in ['high_school', 'college']:
            print(f"警告: 学校类型必须是 'high_school' 或 'college': {school_type}", file=sys.stderr)
            return None
        
        # 验证地址格式
        parsed_address = self.parse_address(address)
        if not parsed_address:
            return None
        
        return {
            "name": name,
            "abbreviation": abbreviation,
            "address": address,
            "type": school_type
        }
    
    def load_addresses_data(self) -> Dict[str, Any]:
        """加载现有地址数据"""
        if os.path.exists(self.addresses_file):
            with open(self.addresses_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {"US": {}}
    
    def load_schools_data(self) -> Dict[str, Any]:
        """加载现有学校数据"""
        if os.path.exists(self.schools_file):
            with open(self.schools_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {"US": {}}
    
    def save_addresses_data(self, data: Dict[str, Any]) -> None:
        """保存地址数据"""
        os.makedirs(os.path.dirname(self.addresses_file), exist_ok=True)
        with open(self.addresses_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_schools_data(self, data: Dict[str, Any]) -> None:
        """保存学校数据"""
        os.makedirs(os.path.dirname(self.schools_file), exist_ok=True)
        with open(self.schools_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def import_addresses_from_file(self, file_path: str, country: str = "US") -> int:
        """
        从文件导入住宅地址
        
        Args:
            file_path: 地址文件路径
            country: 国家代码
            
        Returns:
            成功导入的地址数量
        """
        if not os.path.exists(file_path):
            print(f"错误: 文件不存在: {file_path}", file=sys.stderr)
            return 0
        
        # 加载现有数据
        data = self.load_addresses_data()
        if country not in data:
            data[country] = {}
        
        imported_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    parsed = self.parse_address(line)
                    if parsed:
                        street, city, state, zip_code = parsed
                        full_address = f"{street}, {city}, {state} {zip_code}"
                        
                        # 按州分组
                        if state not in data[country]:
                            data[country][state] = []
                        
                        # 检查是否已存在
                        if full_address not in data[country][state]:
                            data[country][state].append(full_address)
                            imported_count += 1
                            print(f"导入地址: {full_address}")
                        else:
                            print(f"地址已存在，跳过: {full_address}")
                    else:
                        print(f"第 {line_num} 行解析失败: {line.strip()}")
        
        except Exception as e:
            print(f"读取文件时出错: {e}", file=sys.stderr)
            return 0
        
        # 保存数据
        self.save_addresses_data(data)
        print(f"成功导入 {imported_count} 个地址")
        return imported_count
    
    def import_schools_from_file(self, file_path: str, country: str = "US") -> int:
        """
        从文件导入学校信息
        
        Args:
            file_path: 学校信息文件路径
            country: 国家代码
            
        Returns:
            成功导入的学校数量
        """
        if not os.path.exists(file_path):
            print(f"错误: 文件不存在: {file_path}", file=sys.stderr)
            return 0
        
        # 加载现有数据
        data = self.load_schools_data()
        if country not in data:
            data[country] = {}
        
        imported_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    school_info = self.parse_school_line(line)
                    if school_info:
                        # 从地址中提取州信息
                        parsed_address = self.parse_address(school_info["address"])
                        if not parsed_address:
                            continue
                        
                        _, _, state, _ = parsed_address
                        
                        # 初始化州数据结构
                        if state not in data[country]:
                            data[country][state] = {
                                "high_schools": [],
                                "colleges": []
                            }
                        
                        # 确保有正确的学校类型列表
                        school_type = school_info["type"]
                        if school_type == "high_school":
                            schools_list = data[country][state]["high_schools"]
                        else:  # college
                            schools_list = data[country][state]["colleges"]
                        
                        # 创建学校条目
                        school_entry = {
                            "name": school_info["name"],
                            "abbreviation": school_info["abbreviation"],
                            "address": school_info["address"]
                        }
                        
                        # 检查是否已存在（基于名称）
                        existing_names = [s["name"] for s in schools_list]
                        if school_info["name"] not in existing_names:
                            schools_list.append(school_entry)
                            imported_count += 1
                            print(f"导入学校: {school_info['name']} ({school_type}) - {school_info['address']}")
                        else:
                            print(f"学校已存在，跳过: {school_info['name']}")
                    else:
                        print(f"第 {line_num} 行解析失败: {line.strip()}")
        
        except Exception as e:
            print(f"读取文件时出错: {e}", file=sys.stderr)
            return 0
        
        # 保存数据
        self.save_schools_data(data)
        print(f"成功导入 {imported_count} 个学校")
        return imported_count


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="批量导入地址工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 导入住宅地址
  python tools/import_addresses.py --type addresses --file addresses.txt
  
  # 导入学校信息
  python tools/import_addresses.py --type schools --file schools.txt
  
地址文件格式 (每行一个地址):
  1234 Lexington Ave, New York, NY 10022-1234
  5678 Main St, Buffalo, NY 14203-5678
  
学校文件格式 (每行一个学校，用|分隔):
  Harvard University|Harvard|college|Cambridge, MA 02138-3800
  Boston Latin School|BLS|high_school|78 Avenue Louis Pasteur, Boston, MA 02115-5794
        """
    )
    
    parser.add_argument(
        "--type",
        choices=["addresses", "schools"],
        required=True,
        help="导入类型：addresses (住宅地址) 或 schools (学校信息)"
    )
    
    parser.add_argument(
        "--file",
        required=True,
        help="要导入的文件路径"
    )
    
    parser.add_argument(
        "--country",
        default="US",
        help="国家代码，默认为US"
    )
    
    parser.add_argument(
        "--data-dir",
        default="data",
        help="数据目录路径，默认为data"
    )
    
    args = parser.parse_args()
    
    # 创建导入器
    importer = AddressImporter(args.data_dir)
    
    # 执行导入
    if args.type == "addresses":
        count = importer.import_addresses_from_file(args.file, args.country)
    else:  # schools
        count = importer.import_schools_from_file(args.file, args.country)
    
    if count > 0:
        print(f"\n导入完成！共处理 {count} 条记录。")
    else:
        print("\n未导入任何记录。")
        sys.exit(1)


if __name__ == "__main__":
    main() 