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
    def _remove_non_digits(text: str) -> str:
        """移除字符串中的非数字字符"""
        import re
        return re.sub(r'\D', '', text) if text else ''

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
    def _get_ssn_status_info(ssn_info: Dict[str, Any]) -> Dict[str, str]:
        """获取SSN状态信息"""
        if isinstance(ssn_info, dict):
            status = ssn_info.get('status', 'not_verified')
            verified = ssn_info.get('verified', False)
            error = ssn_info.get('error')
        else:
            # 兼容旧格式
            status = 'not_verified'
            verified = False
            error = None
        
        status_map = {
            'verified_valid': {'icon': '✓', 'desc': '在线验证通过', 'color': '#28a745'},
            'not_verified': {'icon': '', 'desc': '未验证', 'color': '#6c757d'},
            'timeout': {'icon': '⏱', 'desc': '验证超时', 'color': '#ffc107'},
            'network_error': {'icon': '⚠', 'desc': '网络错误', 'color': '#dc3545'},
            'blocked': {'icon': '🚫', 'desc': '验证被阻止', 'color': '#dc3545'},
            'verified_invalid': {'icon': '✗', 'desc': '验证确认无效', 'color': '#dc3545'},
            'verification_failed': {'icon': '?', 'desc': '验证失败', 'color': '#dc3545'},
            'exception': {'icon': '!', 'desc': '验证异常', 'color': '#dc3545'},
            'parse_error_valid': {'icon': '✓', 'desc': '有效但详细信息不可用', 'color': '#28a745'}
        }
        
        info = status_map.get(status, status_map['not_verified'])
        if error:
            # 简化长错误信息的显示
            error_text = error
            if 'SSN标记为有效，但无法解析位置/年份详细信息' in error:
                error_text = '有效但详细信息不可用'
            elif 'SSN标记为有效，但找不到位置/年份段落' in error:
                error_text = '有效但信息段落缺失'
            info['desc'] += f' ({error_text})'
        
        return info

    @staticmethod
    def format_text(person_data: Dict[str, Any]) -> str:
        """格式化为文本格式"""
        lines = []
        
        # 基本信息
        lines.append("=== 基本信息 ===")
        name = person_data.get("name", {})
        lines.append(f"姓名 (Firstname Lastname): {name.get('first_name', '')} {name.get('last_name', '')}")
        lines.append(f"性别: {'男' if person_data.get('gender') == 'male' else '女'}")
        
        # 生日和年龄
        birthday = person_data.get("birthday", "")
        if birthday and len(birthday) == 8:
            birth_year = int(birthday[:4])
            birth_month = int(birthday[4:6])
            birth_day = int(birthday[6:8])
            
            current_date = datetime.now()
            age = current_date.year - birth_year
            if current_date.month < birth_month or (current_date.month == birth_month and current_date.day < birth_day):
                age -= 1
            
            lines.append(f"生日 (yyyymmdd): {birthday} ({birth_year}年{birth_month}月{birth_day}日)")
            lines.append(f"年龄: {age}岁")
        
        lines.append(f"国家: {person_data.get('country', '')}")
        
        # 州信息
        state_info = person_data.get("state_info", {})
        if state_info:
            lines.append(f"州/地区: {person_data.get('state', '')} {state_info.get('name', '')} {state_info.get('chinese_name', '')}")
        else:
            lines.append(f"州/地区: {person_data.get('state', '')}")
        
        # 联系信息
        lines.append("\n=== 联系信息 ===")
        lines.append(f"电话: {person_data.get('phone', '')}")
        lines.append(f"电话（纯数字）: {OutputFormatter._remove_non_digits(person_data.get('phone', ''))}")
        lines.append(f"邮箱: {person_data.get('email', '')}")
        
        # 地址信息
        address = person_data.get("address", {})
        lines.append(f"地址: {address.get('full_address', '')}")
        
        # SSN信息
        lines.append("\n=== 身份信息 ===")
        ssn_info = person_data.get('ssn', {})
        if isinstance(ssn_info, dict):
            ssn_number = ssn_info.get('number', 'N/A')
        else:
            ssn_number = ssn_info if ssn_info else 'N/A'
        
        lines.append(f"社保号: {ssn_number}")
        lines.append(f"社保号（纯数字）: {OutputFormatter._remove_non_digits(ssn_number)}")
        
        # SSN验证状态
        status_info = OutputFormatter._get_ssn_status_info(ssn_info)
        lines.append(f"SSN验证状态: {status_info['icon']} {status_info['desc']}")
        
        # 教育信息
        education = person_data.get("education", {})
        education_level = education.get("education_level", "none")
        
        lines.append("\n=== 教育信息 ===")
        lines.append(f"教育水平: {OutputFormatter._get_education_level_chinese(education_level)}")
        
        if education_level == "high_school" or education_level == "college":
            high_school = education.get("high_school", {})
            if high_school:
                lines.append(f"\n高中信息:")
                lines.append(f"学校名称: {high_school.get('name', '')}")
                lines.append(f"学校简称: {high_school.get('abbreviation', '')}")
                lines.append(f"学校地址: {high_school.get('address', '')}")
                
                start_date = high_school.get("start_date", "")
                graduation_date = high_school.get("graduation_date", "")
                if start_date and len(start_date) == 6:
                    start_year = start_date[:4]
                    start_month = start_date[4:6]
                    lines.append(f"入学时间 (yyyymm): {start_date} ({start_year}年{start_month}月)")
                if graduation_date and len(graduation_date) == 6:
                    grad_year = graduation_date[:4]
                    grad_month = graduation_date[4:6]
                    lines.append(f"毕业时间 (yyyymm): {graduation_date} ({grad_year}年{grad_month}月)")
        
        if education_level == "college":
            college = education.get("college", {})
            if college:
                lines.append(f"\n大学信息:")
                lines.append(f"学校名称: {college.get('name', '')}")
                lines.append(f"学校简称: {college.get('abbreviation', '')}")
                lines.append(f"学校地址: {college.get('address', '')}")
                
                start_date = college.get("start_date", "")
                graduation_date = college.get("graduation_date", "")
                if start_date and len(start_date) == 6:
                    start_year = start_date[:4]
                    start_month = start_date[4:6]
                    lines.append(f"入学时间 (yyyymm): {start_date} ({start_year}年{start_month}月)")
                if graduation_date and len(graduation_date) == 6:
                    grad_year = graduation_date[:4]
                    grad_month = graduation_date[4:6]
                    lines.append(f"毕业时间 (yyyymm): {graduation_date} ({grad_year}年{grad_month}月)")
        
        # 父母信息
        parents = person_data.get("parents", {})
        if parents and parents.get("father"):
            lines.append(f"\n=== 父亲信息 ===")
            lines.append(OutputFormatter._format_parent_text(parents["father"], "父亲"))
        
        if parents and parents.get("mother"):
            lines.append(f"\n=== 母亲信息 ===")
            lines.append(OutputFormatter._format_parent_text(parents["mother"], "母亲"))
        
        # 备注信息
        note = person_data.get("note", "")
        if note:
            lines.append(f"\n=== 备注信息 ===")
            lines.append(note)
        
        return "\n".join(lines)

    @staticmethod
    def _get_education_level_chinese(level: str) -> str:
        """获取教育水平的中文显示"""
        level_map = {
            'none': '无',
            'high_school': '高中',
            'college': '大学'
        }
        return level_map.get(level, level)

    @staticmethod
    def _format_parent_text(parent_data: Dict[str, Any], relationship: str) -> str:
        """格式化父母信息为文本"""
        lines = []
        lines.append(f"姓名 (Firstname Lastname): {parent_data['name']['first_name']} {parent_data['name']['last_name']}")
        
        # 计算年龄
        birthday = parent_data["birthday"]
        birth_year = int(birthday[:4])
        birth_month = int(birthday[4:6])
        birth_day = int(birthday[6:8])
        
        current_date = datetime.now()
        age = current_date.year - birth_year
        if current_date.month < birth_month or (current_date.month == birth_month and current_date.day < birth_day):
            age -= 1
        
        lines.append(f"生日 (yyyymmdd): {birthday} ({birth_year}年{birth_month}月{birth_day}日)")
        lines.append(f"年龄: {age}岁")
        lines.append(f"电话: {parent_data['phone']}")
        lines.append(f"电话（纯数字）: {OutputFormatter._remove_non_digits(parent_data['phone'])}")
        lines.append(f"邮箱: {parent_data['email']}")
        lines.append(f"地址: {parent_data['address']['full_address']}")
        
        # SSN信息
        ssn_info = parent_data.get('ssn', {})
        if isinstance(ssn_info, dict):
            ssn_number = ssn_info.get('number', 'N/A')
        else:
            ssn_number = ssn_info if ssn_info else 'N/A'
        
        lines.append(f"社保号: {ssn_number}")
        lines.append(f"社保号（纯数字）: {OutputFormatter._remove_non_digits(ssn_number)}")
        
        # SSN验证状态
        status_info = OutputFormatter._get_ssn_status_info(ssn_info)
        lines.append(f"SSN验证状态: {status_info['icon']} {status_info['desc']}")
        
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
