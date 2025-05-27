#!/usr/bin/env python3
"""
虚拟公民信息生成器主程序
"""

import argparse
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_loader import DataLoader
from generators import PersonGenerator
from formatters import OutputFormatter


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="虚拟公民信息生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py --country US --gender male --state CA --age 20-25 --education college --parents both --format json
  python main.py --country US --state TX --format text
  python main.py --format yaml --output output/person.yaml
  python main.py --config config/development.json
  python main.py --show-high-group-info  # 显示SSN数据范围信息

数据范围:
  本系统使用扩展的High Group数据(1985-2011)，包含：
  • 推测数据: 1985-2002年（基于PNAS 2009论文方法）
  • 原始数据: 2003-2011年（SSA官方数据）
  
  可为1985年以后出生的人生成历史准确的SSN，显著提升早期出生人员的数据质量。
        """
    )

    parser.add_argument(
        "--config",
        type=str,
        help="配置文件路径"
    )

    parser.add_argument(
        "--country",
        type=str,
        help="国家代码（如：US），不指定则随机选择"
    )

    parser.add_argument(
        "--gender",
        choices=["male", "female"],
        help="性别，不指定则随机选择"
    )

    parser.add_argument(
        "--state",
        type=str,
        help="州/地区代码，不指定则随机选择"
    )

    parser.add_argument(
        "--age",
        type=str,
        help="年龄范围（如：18-25），不指定则随机选择"
    )

    parser.add_argument(
        "--education",
        choices=["none", "high_school", "college"],
        help="教育水平，不指定则随机选择"
    )

    parser.add_argument(
        "--parents",
        choices=["none", "father", "mother", "both"],
        default=None,
        help="父母信息，默认为none"
    )

    parser.add_argument(
        "--format",
        choices=["json", "text", "yaml", "csv"],
        default="json",
        help="输出格式，默认为json"
    )

    parser.add_argument(
        "--output",
        type=str,
        help="输出文件路径，不指定则输出到标准输出"
    )

    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="生成的人数，默认为1"
    )

    parser.add_argument(
        "--list-countries",
        action="store_true",
        help="列出支持的国家"
    )

    parser.add_argument(
        "--list-states",
        type=str,
        help="列出指定国家的州/地区"
    )

    parser.add_argument(
        "--backup",
        action="store_true",
        help="备份生成的数据到output文件夹"
    )

    parser.add_argument(
        "--enable-ssn-validation",
        action="store_true",
        help="启用SSN在线验证功能，确保生成的SSN有效（可能较慢）"
    )

    parser.add_argument(
        "--show-high-group-info",
        action="store_true",
        help="显示当前High Group数据统计信息（包括推测数据范围）"
    )

    parser.add_argument(
        "--validate-ssn",
        type=str,
        help="验证指定SSN的有效性 (格式: XXX-XX-XXXX 或 XXXXXXXXX)"
    )

    parser.add_argument(
        "--validate-birth-date",
        type=str,
        help="验证SSN时的出生日期 (格式: YYYY-MM-DD)"
    )

    parser.add_argument(
        "--validate-birth-state",
        type=str,
        help="验证SSN时的出生州 (可选，用于交叉验证)"
    )

    return parser.parse_args()


def load_config(config_path: str) -> Dict[str, Any]:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"错误: 找不到配置文件 '{config_path}'", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"错误: 配置文件格式错误 '{config_path}'", file=sys.stderr)
        sys.exit(1)


def main():
    """主函数"""
    args = parse_arguments()

    # 加载配置文件（如果指定）
    config = {}
    if args.config:
        config = load_config(args.config)

    # 初始化数据加载器和生成器
    try:
        data_loader = DataLoader(config.get("data_dir", "data"))
        # 从配置文件或命令行参数获取SSN验证设置
        enable_ssn_validation = getattr(
            args, 'enable_ssn_validation', False) or config.get(
            "enable_ssn_validation", False)
        generator = PersonGenerator(
            data_loader, enable_ssn_validation=enable_ssn_validation)
    except Exception as e:
        print(f"初始化失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 处理High Group信息显示选项
    if args.show_high_group_info:
        try:
            from src.high_group_loader import HighGroupLoader
            high_group_loader = HighGroupLoader()
            stats = high_group_loader.get_statistics()
            available_years = high_group_loader.get_available_years()
            
            print("=" * 60)
            print("High Group 数据统计信息")
            print("=" * 60)
            print(f"数据来源目录: High Group/")
            print(f"总文件数量: {stats['total_files']}")
            print(f"覆盖区域数量: {stats['total_areas']}")
            print(f"时间范围: {stats['date_range']}")
            print(f"年份跨度: {min(available_years)} - {max(available_years)} ({max(available_years) - min(available_years) + 1} 年)")
            
            # 区分原始数据和推测数据
            original_years = [year for year in available_years if year >= 2003]
            predicted_years = [year for year in available_years if year < 2003]
            
            print()
            print("数据构成:")
            if predicted_years:
                print(f"  • 推测数据: {min(predicted_years)} - {max(predicted_years)} ({len(predicted_years)} 年)")
                print(f"    基于PNAS 2009论文方法推测，使用线性回归外推")
            if original_years:
                print(f"  • 原始数据: {min(original_years)} - {max(original_years)} ({len(original_years)} 年)")
                print(f"    来自SSA官方发布的High Group清单")
            
            print()
            print("系统能力:")
            print(f"  • 可为 1985-2011 年出生的人生成历史准确的SSN")
            print(f"  • 支持精确的SSN时间合理性验证")
            print(f"  • 覆盖 {stats['total_areas']} 个SSN区域号")
            print(f"  • 总计 {stats['total_files']} 个月度数据文件")
            print("=" * 60)
            
        except Exception as e:
            print(f"获取High Group信息失败: {e}", file=sys.stderr)
        return

    # 处理SSN验证选项
    if args.validate_ssn:
        if not args.validate_birth_date:
            print("错误：验证SSN时必须提供出生日期 (--validate-birth-date)", file=sys.stderr)
            sys.exit(1)
        
        try:
            # 创建简化的验证器（避免重复初始化）
            import re
            from src.high_group_loader import HighGroupLoader
            
            # 解析SSN
            ssn_digits = re.sub(r'[^0-9]', '', args.validate_ssn)
            if len(ssn_digits) != 9:
                print(f"错误：SSN必须是9位数字，当前为 {len(ssn_digits)} 位", file=sys.stderr)
                sys.exit(1)
            
            area = int(ssn_digits[:3])
            group = int(ssn_digits[3:5])
            serial = int(ssn_digits[5:])
            
            # 解析生日
            try:
                parts = args.validate_birth_date.split('-')
                if len(parts) != 3:
                    raise ValueError("生日格式必须为 YYYY-MM-DD")
                birth_year = int(parts[0])
                birth_month = int(parts[1])
                birth_day = int(parts[2])
            except ValueError as e:
                print(f"错误：生日格式不正确: {e}", file=sys.stderr)
                sys.exit(1)
            
            # 基础格式验证
            errors = []
            if area == 0 or area == 666 or area >= 900:
                errors.append("区域号无效")
            if group == 0:
                errors.append("组号不能为00")
            if serial == 0:
                errors.append("序列号不能为0000")
            
            # 使用High Group数据验证
            high_group_loader = HighGroupLoader()
            timing_valid = high_group_loader.validate_ssn_timing(
                area, group, serial, birth_year, birth_month
            )
            
            if not timing_valid:
                errors.append("SSN发放时间与出生日期不匹配")
            
            # 获取预期州
            expected_state = None
            try:
                # 默认使用US数据进行验证
                ssn_data = data_loader.load_ssn("US")
                state_ranges = ssn_data["US"]["structure"]["area_number"]["state_ranges"]
                for state, ranges in state_ranges.items():
                    for range_str in ranges:
                        if "-" in range_str:
                            start, end = map(int, range_str.split("-"))
                            if start <= area <= end:
                                expected_state = state
                                break
                        else:
                            if area == int(range_str):
                                expected_state = state
                                break
                    if expected_state:
                        break
            except Exception:
                pass
            
            # 显示验证结果
            print("=" * 50)
            print("SSN验证结果")
            print("=" * 50)
            print(f"SSN: {args.validate_ssn}")
            print(f"生日: {args.validate_birth_date}")
            if args.validate_birth_state:
                print(f"出生州: {args.validate_birth_state}")
            print(f"区域号: {area}")
            print(f"组号: {group}")
            print(f"序列号: {serial}")
            if expected_state:
                print(f"对应州: {expected_state}")
            
            # 验证状态
            is_valid = len(errors) == 0
            status = "✓ 有效" if is_valid else "✗ 无效"
            print(f"验证状态: {status}")
            
            if errors:
                print("\n错误:")
                for error in errors:
                    print(f"  • {error}")
            
            # 州验证警告
            if expected_state and args.validate_birth_state:
                if args.validate_birth_state.upper() != expected_state.upper():
                    print(f"\n警告:")
                    print(f"  • SSN区域号{area}通常对应{expected_state}州，但您指定的是{args.validate_birth_state}州")
            
            # 估计分配时间
            assignment_date = high_group_loader.estimate_group_assignment_date(area, group)
            if assignment_date:
                assign_year, assign_month = assignment_date
                print(f"\n估计分配时间: {int(assign_year)}-{int(assign_month):02d}")
            
            print("=" * 50)
            
        except Exception as e:
            print(f"验证过程中发生错误: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # 处理列表选项
    if args.list_countries:
        countries = data_loader.get_supported_countries()
        print("支持的国家:")
        for country in countries:
            print(f"  {country}")
        return

    if args.list_states:
        try:
            states = data_loader.get_states_for_country(args.list_states)
            print(f"国家 {args.list_states} 的州/地区:")
            for state in states:
                print(f"  {state}")
        except ValueError as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # 从配置文件或命令行参数获取生成参数
    country = args.country if args.country is not None else config.get(
        "country")
    state = args.state if args.state is not None else config.get("state")
    age_range = args.age if args.age is not None else config.get("age_range")
    education_level = args.education if args.education is not None else config.get(
        "education")
    parents_option = args.parents if args.parents is not None else config.get(
        "parents", "none")
    gender = args.gender if args.gender is not None else config.get("gender")
    count = config.get("count", args.count)
    output_format = args.format if args.format != "json" else config.get(
        "output_format", "json")
    backup = args.backup or config.get("backup", False)

    # 验证参数
    if country:
        supported_countries = data_loader.get_supported_countries()
        if country not in supported_countries:
            print(f"错误: 不支持的国家 '{country}'", file=sys.stderr)
            print(f"支持的国家: {', '.join(supported_countries)}")
            sys.exit(1)

    if state and country:
        try:
            states = data_loader.get_states_for_country(country)
            if state not in states:
                print(f"错误: 国家 '{country}' 不支持州/地区 '{state}'", file=sys.stderr)
                print(f"支持的州/地区: {', '.join(states)}")
                sys.exit(1)
        except ValueError as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)

    # 生成虚拟公民信息
    try:
        # 显示系统状态（简短版本）
        if not any([args.list_countries, args.list_states, args.show_high_group_info]):
            try:
                available_years = generator.high_group_loader.get_available_years()
                if available_years:
                    min_year = min(available_years)
                    max_year = max(available_years)
                    total_years = max_year - min_year + 1
                    predicted_years = len([y for y in available_years if y < 2003])
                    # if predicted_years > 0:
                    #     print(f"ℹ️  系统使用扩展High Group数据: {min_year}-{max_year} ({total_years}年, 含{predicted_years}年推测数据)")
                    # else:
                    #     print(f"ℹ️  系统使用High Group数据: {min_year}-{max_year} ({total_years}年)")
            except:
                pass  # 静默失败，不影响主要功能
        
        people = []
        for i in range(count):
            person_data = generator.generate_person(
                country=country,
                gender=gender,
                state=state,
                age=age_range,
                education=education_level,
                parents=parents_option
            )
            people.append(person_data)

        # 格式化输出
        if output_format == "json":
            if count == 1:
                output = OutputFormatter.format_json(people[0])
            else:
                output = OutputFormatter.format_json(people)
        elif output_format == "yaml":
            if count == 1:
                output = OutputFormatter.format_yaml(people[0])
            else:
                output = OutputFormatter.format_yaml(people)
        elif output_format == "text":
            output_lines = []
            for i, person in enumerate(people):
                if count > 1:
                    output_lines.append(f"\n第 {i+1} 个虚拟公民:")
                    output_lines.append("-" * 30)
                output_lines.append(OutputFormatter.format_text(person))
            output = "\n".join(output_lines)
        elif output_format == "csv":
            output_lines = [OutputFormatter.format_csv_header()]
            for person in people:
                output_lines.append(OutputFormatter.format_csv_row(person))
            output = "\n".join(output_lines)

        # 输出结果
        if args.output:
            # 确保输出目录存在
            output_dir = os.path.dirname(args.output)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"输出已保存到: {args.output}")
        else:
            print(output)

        # 备份逻辑
        if backup:
            # 创建今天日期的文件夹
            today = datetime.now().strftime('%y%m%d')
            backup_dir = os.path.join("output", today)
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            # 为每个人创建单独的json文件
            for person in people:
                name = person["name"]
                birthday = person["birthday"]
                # 文件名格式：姓名-yymmdd(生日).json
                filename = f"{name['first_name']}{name['last_name']}-{birthday}.json"
                backup_file = os.path.join(backup_dir, filename)

                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(OutputFormatter.format_json(person))

            print(f"备份已保存到: {backup_dir}/ (共{len(people)}个文件)")

    except Exception as e:
        print(f"生成失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
