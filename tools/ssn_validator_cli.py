#!/usr/bin/env python3
"""
SSN验证命令行工具
用于验证输入的SSN码是否有效，考虑生日和出生地区
"""

import argparse
import sys
import os
import re
from datetime import datetime
from typing import Tuple, Optional

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from high_group_loader import HighGroupLoader
from data_loader import DataLoader


class SSNValidator:
    """SSN验证器"""
    
    def __init__(self):
        self.high_group_loader = HighGroupLoader()
        self.data_loader = DataLoader("data")
        
    def parse_ssn(self, ssn: str) -> Tuple[int, int, int]:
        """解析SSN格式"""
        # 移除所有非数字字符
        ssn_digits = re.sub(r'[^0-9]', '', ssn)
        
        if len(ssn_digits) != 9:
            raise ValueError(f"SSN必须是9位数字，当前为 {len(ssn_digits)} 位")
        
        area = int(ssn_digits[:3])
        group = int(ssn_digits[3:5])
        serial = int(ssn_digits[5:])
        
        return area, group, serial
    
    def parse_birth_date(self, birth_date: str) -> Tuple[int, int, int]:
        """解析生日格式 (YYYY-MM-DD)"""
        try:
            parts = birth_date.split('-')
            if len(parts) != 3:
                raise ValueError("生日格式必须为 YYYY-MM-DD")
            
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            
            # 验证日期合理性
            if year < 1900 or year > 2030:
                raise ValueError("年份应在1900-2030之间")
            if month < 1 or month > 12:
                raise ValueError("月份应在1-12之间")
            if day < 1 or day > 31:
                raise ValueError("日期应在1-31之间")
                
            return year, month, day
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError("生日格式不正确，必须为 YYYY-MM-DD")
            else:
                raise e
    
    def get_state_for_area(self, area: int) -> Optional[str]:
        """根据区域号获取对应的州"""
        try:
            ssn_data = self.data_loader.load_ssn("US")
            state_ranges = ssn_data["US"]["structure"]["area_number"]["state_ranges"]
            
            for state, ranges in state_ranges.items():
                for range_str in ranges:
                    if "-" in range_str:
                        start, end = map(int, range_str.split("-"))
                        if start <= area <= end:
                            return state
                    else:
                        if area == int(range_str):
                            return state
            return None
        except Exception:
            return None
    
    def validate_ssn_comprehensive(self, ssn: str, birth_date: str, birth_state: str = None) -> dict:
        """
        综合验证SSN有效性
        
        Args:
            ssn: SSN字符串 (XXX-XX-XXXX 或 XXXXXXXXX)
            birth_date: 生日字符串 (YYYY-MM-DD)
            birth_state: 出生州（可选，用于交叉验证）
            
        Returns:
            验证结果字典
        """
        result = {
            "is_valid": False,
            "ssn": ssn,
            "birth_date": birth_date,
            "birth_state": birth_state,
            "errors": [],
            "warnings": [],
            "details": {
                "area": None,
                "group": None,
                "serial": None,
                "birth_year": None,
                "birth_month": None,
                "birth_day": None,
                "expected_state": None,
                "timing_valid": False,
                "basic_format_valid": False
            }
        }
        
        try:
            # 1. 解析SSN
            area, group, serial = self.parse_ssn(ssn)
            result["details"]["area"] = area
            result["details"]["group"] = group
            result["details"]["serial"] = serial
            result["details"]["basic_format_valid"] = True
            
        except ValueError as e:
            result["errors"].append(f"SSN格式错误: {e}")
            return result
        
        try:
            # 2. 解析生日
            birth_year, birth_month, birth_day = self.parse_birth_date(birth_date)
            result["details"]["birth_year"] = birth_year
            result["details"]["birth_month"] = birth_month
            result["details"]["birth_day"] = birth_day
            
        except ValueError as e:
            result["errors"].append(f"生日格式错误: {e}")
            return result
        
        # 3. 基础SSN格式验证
        if area == 0:
            result["errors"].append("区域号不能为000")
            
        if area == 666:
            result["errors"].append("区域号不能为666")
            
        if area >= 900:
            result["errors"].append("区域号不能在900-999范围内")
            
        if group == 0:
            result["errors"].append("组号不能为00")
            
        if serial == 0:
            result["errors"].append("序列号不能为0000")
        
        # 4. 根据区域号推断州
        expected_state = self.get_state_for_area(area)
        result["details"]["expected_state"] = expected_state
        
        if expected_state and birth_state:
            if birth_state.upper() != expected_state.upper():
                result["warnings"].append(f"SSN区域号{area}通常对应{expected_state}州，但您指定的是{birth_state}州")
        
        # 5. 时间合理性验证
        timing_valid = self.high_group_loader.validate_ssn_timing(
            area, group, serial, birth_year, birth_month
        )
        result["details"]["timing_valid"] = timing_valid
        
        if not timing_valid:
            result["errors"].append("SSN的发放时间与出生日期不匹配")
        
        # 6. 组号历史合理性检查
        assignment_date = self.high_group_loader.estimate_group_assignment_date(area, group)
        if assignment_date:
            assign_year, assign_month = assignment_date
            result["details"]["estimated_assignment"] = f"{assign_year}-{assign_month:02d}"
            
            # 检查分配时间是否在出生后
            if assign_year < birth_year or (assign_year == birth_year and assign_month < birth_month):
                result["errors"].append(f"组号{group}的估计分配时间({assign_year}-{assign_month:02d})早于出生日期")
        
        # 7. 综合判断
        result["is_valid"] = len(result["errors"]) == 0
        
        return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="SSN验证工具 - 验证SSN与生日、出生地区的匹配性",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python ssn_validator_cli.py --ssn 123-45-6789 --birth-date 1990-06-15 --birth-state CA
  python ssn_validator_cli.py --ssn 987654321 --birth-date 1985-12-25
  python ssn_validator_cli.py --batch validation_list.txt

输入格式:
  SSN: XXX-XX-XXXX 或 XXXXXXXXX
  生日: YYYY-MM-DD
  州: 两字母代码 (如: CA, TX, NY)

批量验证文件格式 (每行):
  SSN,生日,州
  123-45-6789,1990-06-15,CA
  987-65-4321,1985-12-25,TX
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    
    group.add_argument(
        "--ssn",
        type=str,
        help="要验证的SSN (XXX-XX-XXXX 或 XXXXXXXXX 格式)"
    )
    
    parser.add_argument(
        "--birth-date",
        type=str,
        help="出生日期 (YYYY-MM-DD 格式)"
    )
    
    parser.add_argument(
        "--birth-state",
        type=str,
        help="出生州 (可选，用于交叉验证)"
    )
    
    group.add_argument(
        "--batch",
        type=str,
        help="批量验证文件路径 (CSV格式: SSN,生日,州)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细验证信息"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="以JSON格式输出结果"
    )
    
    args = parser.parse_args()
    
    validator = SSNValidator()
    
    if args.ssn:
        # 单个SSN验证
        if not args.birth_date:
            print("错误: 验证SSN时必须提供出生日期", file=sys.stderr)
            sys.exit(1)
        
        result = validator.validate_ssn_comprehensive(
            args.ssn, args.birth_date, args.birth_state
        )
        
        if args.json:
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print_validation_result(result, args.verbose)
    
    elif args.batch:
        # 批量验证
        try:
            with open(args.batch, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            results = []
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split(',')
                if len(parts) < 2:
                    print(f"警告: 第{i}行格式不正确，跳过: {line}", file=sys.stderr)
                    continue
                
                ssn = parts[0].strip()
                birth_date = parts[1].strip()
                birth_state = parts[2].strip() if len(parts) > 2 else None
                
                result = validator.validate_ssn_comprehensive(ssn, birth_date, birth_state)
                results.append(result)
                
                if not args.json:
                    print(f"\n--- 验证结果 #{i} ---")
                    print_validation_result(result, args.verbose)
            
            if args.json:
                import json
                print(json.dumps(results, indent=2, ensure_ascii=False))
            else:
                # 统计摘要
                valid_count = sum(1 for r in results if r["is_valid"])
                print(f"\n{'='*50}")
                print(f"批量验证完成: {len(results)} 条记录")
                print(f"有效: {valid_count} 条 ({valid_count/len(results)*100:.1f}%)")
                print(f"无效: {len(results)-valid_count} 条")
                
        except FileNotFoundError:
            print(f"错误: 找不到文件 {args.batch}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"错误: 读取文件时发生异常: {e}", file=sys.stderr)
            sys.exit(1)


def print_validation_result(result: dict, verbose: bool = False):
    """打印验证结果"""
    ssn = result["ssn"]
    birth_date = result["birth_date"]
    birth_state = result["birth_state"] or "未指定"
    is_valid = result["is_valid"]
    
    status = "✓ 有效" if is_valid else "✗ 无效"
    print(f"SSN: {ssn}")
    print(f"生日: {birth_date}")
    print(f"出生州: {birth_state}")
    print(f"验证状态: {status}")
    
    if verbose:
        details = result["details"]
        print(f"\n详细信息:")
        print(f"  区域号: {details['area']}")
        print(f"  组号: {details['group']}")
        print(f"  序列号: {details['serial']}")
        if details["expected_state"]:
            print(f"  对应州: {details['expected_state']}")
        if details.get("estimated_assignment"):
            print(f"  估计分配时间: {details['estimated_assignment']}")
        print(f"  格式有效: {'是' if details['basic_format_valid'] else '否'}")
        print(f"  时间合理: {'是' if details['timing_valid'] else '否'}")
    
    if result["errors"]:
        print(f"\n错误:")
        for error in result["errors"]:
            print(f"  • {error}")
    
    if result["warnings"]:
        print(f"\n警告:")
        for warning in result["warnings"]:
            print(f"  • {warning}")


if __name__ == "__main__":
    main() 