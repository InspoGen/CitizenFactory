"""
输出格式化模块
支持多种输出格式
"""

import json
from typing import Dict, Any
from datetime import datetime

# yaml是可选依赖
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class OutputFormatter:
    """输出格式化器"""

    @staticmethod
    def format_json(data: Dict[str, Any], indent: int = 2) -> str:
        """
        格式化为JSON

        Args:
            data: 要格式化的数据
            indent: 缩进级别

        Returns:
            JSON格式字符串
        """
        return json.dumps(data, ensure_ascii=False, indent=indent)

    @staticmethod
    def format_yaml(data: Dict[str, Any]) -> str:
        """
        格式化为YAML

        Args:
            data: 要格式化的数据

        Returns:
            YAML格式字符串
        """
        if not HAS_YAML:
            raise ImportError("yaml模块未安装，请运行: pip install pyyaml")
        return yaml.dump(
            data,
            allow_unicode=True,
            default_flow_style=False,
            indent=2)

    @staticmethod
    def format_text(data: Dict[str, Any]) -> str:
        """
        格式化为可读文本

        Args:
            data: 要格式化的数据

        Returns:
            文本格式字符串
        """
        lines = []
        lines.append("=" * 50)
        lines.append("虚拟公民信息")
        lines.append("=" * 50)

        # 基本信息
        name = data["name"]
        lines.append(f"姓名: {name['last_name']}, {name['first_name']}")
        lines.append(f"性别: {'男' if data['gender'] == 'male' else '女'}")
        lines.append(f"生日: {data['birthday']}")
        lines.append(f"国家: {data['country']}")
        lines.append(f"州/地区: {data['state']}")
        lines.append("")

        # 联系信息
        lines.append("联系信息:")
        lines.append(f"  电话: {data['phone']}")
        lines.append(f"  邮箱: {data['email']}")
        lines.append(f"  地址: {data['address']['full_address']}")
        lines.append("")

        # 身份信息
        lines.append("身份信息:")
        lines.append(f"  社会保障号: {data['ssn']['number']}")

        # SSN验证状态 - 简化显示
        if data['ssn']['verified']:
            lines.append("  SSN验证状态: ✓ 在线验证通过")
        else:
            lines.append("  SSN验证状态: ✗ 未验证或验证失败")

        lines.append("")

        # 教育信息
        education = data["education"]
        lines.append("教育信息:")
        lines.append(f"  教育水平: {education.get('education_level') or '无'}")

        if "high_school" in education:
            hs = education["high_school"]
            lines.append("  高中:")
            lines.append(f"    学校: {hs['name']} ({hs['abbreviation']})")
            lines.append(f"    地址: {hs['address']}")
            lines.append(f"    入学时间: {hs['start_date']}")
            lines.append(f"    毕业时间: {hs['graduation_date']}")

        if "college" in education:
            college = education["college"]
            lines.append("  大学:")
            lines.append(
                f"    学校: {college['name']} ({college['abbreviation']})")
            lines.append(f"    地址: {college['address']}")
            lines.append(f"    入学时间: {college['start_date']}")
            lines.append(f"    毕业时间: {college['graduation_date']}")

        lines.append("")

        # 添加父母信息
        if data.get("parents"):
            parents = data["parents"]
            lines.append("")
            
            if "father" in parents:
                lines.append(OutputFormatter._format_parent_text(parents["father"], "父亲"))
                lines.append("")
            
            if "mother" in parents:
                lines.append(OutputFormatter._format_parent_text(parents["mother"], "母亲"))
        
        return "\n".join(lines)

    @staticmethod
    def _format_parent_text(parent_data: Dict[str, Any], relationship: str) -> str:
        """格式化父母信息为文本"""
        lines = []
        lines.append(f"{relationship}信息：")
        lines.append(f"姓名：{parent_data['name']['last_name']} {parent_data['name']['first_name']}")
        
        # 计算年龄
        birthday = parent_data["birthday"]
        birth_year = int(birthday[:4])
        birth_month = int(birthday[4:6])
        birth_day = int(birthday[6:8])
        
        current_date = datetime.now()
        age = current_date.year - birth_year
        if current_date.month < birth_month or (current_date.month == birth_month and current_date.day < birth_day):
            age -= 1
        
        lines.append(f"生日：{birth_year}年{birth_month}月{birth_day}日")
        lines.append(f"年龄：{age}岁")
        lines.append(f"电话：{parent_data['phone']}")
        lines.append(f"邮箱：{parent_data['email']}")
        lines.append(f"地址：{parent_data['address']['full_address']}")
        
        # SSN信息
        ssn_info = parent_data.get('ssn', {})
        if isinstance(ssn_info, dict):
            ssn_number = ssn_info.get('number', 'N/A')
            ssn_verified = ssn_info.get('verified', False)
        else:
            ssn_number = ssn_info if ssn_info else 'N/A'
            ssn_verified = False
        
        lines.append(f"社保号：{ssn_number}")
        if ssn_verified:
            lines.append("  SSN验证状态: ✓ 在线验证通过")
        else:
            lines.append("  SSN验证状态: ✗ 未验证或验证失败")
        
        return "\n".join(lines)

    @staticmethod
    def format_csv_header() -> str:
        """
        生成CSV表头

        Returns:
            CSV表头字符串
        """
        headers = [
            "姓", "名", "性别", "生日", "国家", "州", "电话", "邮箱", "地址", "社会保障号",
            "SSN验证通过",
            "教育水平", "高中名称", "高中缩写", "高中地址", "高中入学", "高中毕业",
            "大学名称", "大学缩写", "大学地址", "大学入学", "大学毕业",
            "父亲姓名", "父亲生日", "父亲电话", "父亲邮箱", "父亲地址", "父亲SSN",
            "母亲姓名", "母亲生日", "母亲电话", "母亲邮箱", "母亲地址", "母亲SSN"
        ]
        return ",".join(headers)

    @staticmethod
    def format_csv_row(data: Dict[str, Any]) -> str:
        """
        格式化为CSV行

        Args:
            data: 要格式化的数据

        Returns:
            CSV行字符串
        """
        row = []

        # 基本信息
        name = data["name"]
        row.append(f'"{name["last_name"]}"')
        row.append(f'"{name["first_name"]}"')
        row.append(f'"{data["gender"]}"')
        row.append(f'"{data["birthday"]}"')
        row.append(f'"{data["country"]}"')
        row.append(f'"{data["state"]}"')
        row.append(f'"{data["phone"]}"')
        row.append(f'"{data["email"]}"')
        row.append(f'"{data["address"]["full_address"]}"')
        row.append(f'"{data["ssn"]["number"]}"')

        # SSN验证状态 - 简化显示
        row.append(f'"{"是" if data["ssn"]["verified"] else "否"}"')

        # 教育信息
        education = data["education"]
        row.append(f'"{education.get("education_level") or "无"}"')

        # 高中信息
        if "high_school" in education:
            hs = education["high_school"]
            row.append(f'"{hs["name"]}"')
            row.append(f'"{hs["abbreviation"]}"')
            row.append(f'"{hs["address"]}"')
            row.append(f'"{hs["start_date"]}"')
            row.append(f'"{hs["graduation_date"]}"')
        else:
            row.extend(['""'] * 5)

        # 大学信息
        if "college" in education:
            college = education["college"]
            row.append(f'"{college["name"]}"')
            row.append(f'"{college["abbreviation"]}"')
            row.append(f'"{college["address"]}"')
            row.append(f'"{college["start_date"]}"')
            row.append(f'"{college["graduation_date"]}"')
        else:
            row.extend(['""'] * 5)

        # 父母信息
        parents = data.get("parents", {})

        # 父亲信息
        if "father" in parents:
            father = parents["father"]
            father_name = father["name"]
            row.append(
                f'"{father_name["last_name"]}, {father_name["first_name"]}"')
            row.append(f'"{father["birthday"]}"')
            row.append(f'"{father["phone"]}"')
            row.append(f'"{father["email"]}"')
            row.append(f'"{father["address"]["full_address"]}"')
            row.append(f'"{father["ssn"]["number"]}"')
        else:
            row.extend(['""'] * 6)

        # 母亲信息
        if "mother" in parents:
            mother = parents["mother"]
            mother_name = mother["name"]
            row.append(
                f'"{mother_name["last_name"]}, {mother_name["first_name"]}"')
            row.append(f'"{mother["birthday"]}"')
            row.append(f'"{mother["phone"]}"')
            row.append(f'"{mother["email"]}"')
            row.append(f'"{mother["address"]["full_address"]}"')
            row.append(f'"{mother["ssn"]["number"]}"')
        else:
            row.extend(['""'] * 6)

        return ",".join(row)
