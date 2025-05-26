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
                filename = f"{name['last_name']}{name['first_name']}-{birthday}.json"
                backup_file = os.path.join(backup_dir, filename)

                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(OutputFormatter.format_json(person))

            print(f"备份已保存到: {backup_dir}/ (共{len(people)}个文件)")

    except Exception as e:
        print(f"生成失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
