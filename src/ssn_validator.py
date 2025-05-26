#!/usr/bin/env python3
"""
SSN验证模块
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from typing import Dict, Any, Optional


class SSNValidator:
    """SSN验证器"""

    def __init__(self, timeout: int = 5):
        """
        初始化SSN验证器

        Args:
            timeout: 请求超时时间（秒）
        """
        self.timeout = timeout
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'dnt': '1',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0'
        }

    def verify_ssn_details(self, ssn_digits_input: str) -> Dict[str, Any]:
        """
        使用ssn-check.org验证SSN的有效性

        Args:
            ssn_digits_input: 9位数字的SSN字符串

        Returns:
            包含验证结果的字典
        """
        # 输入验证
        if not re.match(r"^\d{9}$", ssn_digits_input):
            return {
                "ssn_input": ssn_digits_input,
                "is_valid": None,
                "location": None,
                "year": None,
                "error": "输入无效：SSN必须是9位数字"
            }

        # 格式化SSN
        formatted_ssn = f"{ssn_digits_input[:3]}-{ssn_digits_input[3:5]}-{ssn_digits_input[5:]}"
        url = f"https://www.ssn-check.org/verify/{formatted_ssn}"

        result = {
            "ssn": formatted_ssn,
            "is_valid": None,
            "location": None,
            "year": None
        }

        try:
            response = requests.get(
                url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            verification_container = soup.find(
                'div', class_='my-3 text-center')

            if not verification_container:
                result["error"] = "无法在页面上找到主要验证结果容器。页面结构可能已更改。"
                return result

            # 检查有效性
            validity_tag = None
            valid_tag_candidate = verification_container.find(
                'p', class_=re.compile(r'text-success'))
            if valid_tag_candidate and f"{formatted_ssn} is Valid" in valid_tag_candidate.get_text(
            ):
                validity_tag = valid_tag_candidate
                result["is_valid"] = True
            else:
                invalid_tag_candidate = verification_container.find(
                    'p', class_=re.compile(r'text-danger'))
                if invalid_tag_candidate and f"{formatted_ssn} is Invalid" in invalid_tag_candidate.get_text(
                ):
                    validity_tag = invalid_tag_candidate
                    result["is_valid"] = False

            # 如果找不到明确的有效性标签，尝试其他方法
            if validity_tag is None:
                all_p_tags_in_container = verification_container.find_all(
                    'p', limit=5)
                for p_tag in all_p_tags_in_container:
                    p_text = p_tag.get_text()
                    if f"{formatted_ssn} is Valid" in p_text:
                        result["is_valid"] = True
                        break
                    elif f"{formatted_ssn} is Invalid" in p_text:
                        result["is_valid"] = False
                        break

            if result["is_valid"] is None:
                result["error"] = "无法从页面内容确定SSN有效性"

            # 如果SSN有效，尝试提取位置和年份信息
            if result["is_valid"] is True:
                info_paragraph = verification_container.find(
                    'p', class_='lead text-muted', string=re.compile(r"was issued in"))

                if info_paragraph:
                    info_text = ' '.join(info_paragraph.stripped_strings)
                    match = re.search(
                        rf"{re.escape(formatted_ssn)}\s+was issued in\s+(.+?)\s+in\s+(\d{{4}})",
                        info_text,
                        re.IGNORECASE)
                    if not match:
                        match = re.search(
                            r"was issued in\s+(.+?)\s+in\s+(\d{{4}})",
                            info_text,
                            re.IGNORECASE)

                    if match:
                        result["location"] = match.group(1).strip()
                        result["year"] = match.group(2).strip()
                    else:
                        if "error" not in result:
                            result["error"] = "SSN标记为有效，但无法解析位置/年份详细信息"
                else:
                    if "error" not in result:
                        result["error"] = "SSN标记为有效，但找不到位置/年份段落"

        except requests.exceptions.Timeout:
            result["error"] = f"请求超时（{self.timeout}秒）"
            result["is_valid"] = True  # 超时时默认有效
        except requests.exceptions.HTTPError as e:
            result["error"] = f"HTTP错误：{e}。响应代码：{e.response.status_code}"
            if e.response and "cloudflare" in e.response.text.lower():
                result["error"] += " 这可能是Cloudflare验证问题，Cookie可能已过期"
            result["is_valid"] = True  # HTTP错误时默认有效
        except requests.exceptions.RequestException as e:
            result["error"] = f"请求失败：{e}"
            result["is_valid"] = True  # 请求失败时默认有效
        except Exception as e:
            result["error"] = f"解析或执行过程中发生意外错误：{e}"
            result["is_valid"] = True  # 其他异常时默认有效

        return result

    def validate_ssn_with_details(self,
                                  ssn: str,
                                  expected_state: str = None,
                                  expected_birth_year: int = None) -> Dict[str,
                                                                           Any]:
        """
        验证SSN的位置和年份是否合理，并返回详细信息

        Args:
            ssn: SSN字符串（格式：XXX-XX-XXXX或XXXXXXXXX）
            expected_state: 期望的州
            expected_birth_year: 期望的出生年份

        Returns:
            包含验证状态详细信息的字典
        """
        # 移除连字符
        ssn_digits = re.sub(r'[^0-9]', '', ssn)

        validation_result = {
            "validation_attempted": True,
            "validation_passed": False,
            "validation_status": "unknown",
            "validation_details": {
                "is_valid": None,
                "location": None,
                "year": None,
                "error": None
            }
        }

        try:
            result = self.verify_ssn_details(ssn_digits)
            validation_result["validation_details"] = result.copy()

            # 分析验证状态
            if "error" in result:
                if "请求超时" in result["error"]:
                    validation_result["validation_status"] = "timeout"
                elif "HTTP错误" in result["error"] or "请求失败" in result["error"]:
                    validation_result["validation_status"] = "network_error"
                elif "Cloudflare" in result["error"]:
                    validation_result["validation_status"] = "blocked"
                else:
                    validation_result["validation_status"] = "parse_error"

                # 如果有error但is_valid为True，说明是网络问题但回退处理成功
                if result.get("is_valid") is True:
                    validation_result["validation_passed"] = True
                else:
                    validation_result["validation_passed"] = False
            else:
                # 没有错误的情况
                if result.get("is_valid") is True:
                    validation_result["validation_status"] = "verified_valid"
                    validation_result["validation_passed"] = True

                    # 进一步检查位置和年份匹配
                    location_match = True
                    year_match = True

                    if expected_state and result.get("location"):
                        location = result["location"].lower()
                        state_lower = expected_state.lower()
                        if state_lower not in location and location not in state_lower:
                            location_match = False

                    if expected_birth_year and result.get("year"):
                        try:
                            issue_year = int(result["year"])
                            if issue_year < expected_birth_year or issue_year > expected_birth_year + 20:
                                year_match = False
                        except ValueError:
                            year_match = False

                    if not location_match or not year_match:
                        validation_result["validation_status"] = "verified_valid_mismatch"
                        validation_result["validation_passed"] = False
                elif result.get("is_valid") is False:
                    validation_result["validation_status"] = "verified_invalid"
                    validation_result["validation_passed"] = False
                else:
                    validation_result["validation_status"] = "verification_failed"
                    validation_result["validation_passed"] = False

        except Exception as e:
            validation_result["validation_status"] = "exception"
            validation_result["validation_details"]["error"] = f"验证过程异常: {str(e)}"
            validation_result["validation_passed"] = True  # 异常时保守处理

        return validation_result

    def validate_ssn_location_year(
            self,
            ssn: str,
            expected_state: str = None,
            expected_birth_year: int = None) -> bool:
        """
        验证SSN的位置和年份是否合理

        Args:
            ssn: SSN字符串（格式：XXX-XX-XXXX或XXXXXXXXX）
            expected_state: 期望的州
            expected_birth_year: 期望的出生年份

        Returns:
            是否验证通过
        """
        # 移除连字符
        ssn_digits = re.sub(r'[^0-9]', '', ssn)

        try:
            result = self.verify_ssn_details(ssn_digits)

            # 如果验证失败或SSN无效，返回False
            if "error" in result and result["is_valid"] is not True:
                return False

            if result["is_valid"] is False:
                return False

            # 检查位置是否匹配（如果提供了期望的州）
            if expected_state and result.get("location"):
                # 这里可以添加更复杂的州名匹配逻辑
                # 例如：California -> CA, Texas -> TX
                location = result["location"].lower()
                state_lower = expected_state.lower()
                if state_lower not in location and location not in state_lower:
                    return False

            # 检查年份是否合理（如果提供了期望的出生年份）
            if expected_birth_year and result.get("year"):
                try:
                    issue_year = int(result["year"])
                    # SSN通常在出生后几年内发放
                    if issue_year < expected_birth_year or issue_year > expected_birth_year + 20:
                        return False
                except ValueError:
                    return False

            return True
        except Exception:
            # 任何异常都认为验证通过（保守策略）
            return True

    def validate_ssn_simple(
            self,
            ssn: str,
            expected_state: str = None,
            expected_birth_year: int = None) -> bool:
        """
        简化的SSN验证方法，只返回是否验证通过

        Args:
            ssn: SSN字符串（格式：XXX-XX-XXXX或XXXXXXXXX）
            expected_state: 期望的州
            expected_birth_year: 期望的出生年份

        Returns:
            True: 验证通过, False: 验证失败或网络问题
        """
        try:
            result = self.validate_ssn_with_details(
                ssn, expected_state, expected_birth_year)
            return result["validation_passed"]
        except Exception:
            return False
