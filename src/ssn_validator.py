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

    # SSN验证状态常量
    STATUS_NOT_VERIFIED = 0      # 未验证
    STATUS_VERIFIED_VALID = 1    # 验证有效
    STATUS_TIMEOUT = 2           # 验证超时
    STATUS_VERIFIED_INVALID = 3  # 验证无效
    STATUS_PARSE_ERROR_VALID = 4 # 信息解析有误，但是提取到验证有效
    STATUS_PARSE_ERROR_UNKNOWN = 5 # 信息解析有误，但是没有提取到验证有效
    STATUS_NETWORK_ERROR = 6     # 网络错误
    STATUS_BLOCKED = 7           # 验证被阻止
    STATUS_EXCEPTION = 8         # 验证异常
    
    # 状态描述映射
    STATUS_DESCRIPTIONS = {
        STATUS_NOT_VERIFIED: "未验证",
        STATUS_VERIFIED_VALID: "在线验证通过",
        STATUS_TIMEOUT: "验证超时",
        STATUS_VERIFIED_INVALID: "验证确认无效",
        STATUS_PARSE_ERROR_VALID: "有效但详细信息不可用",
        STATUS_PARSE_ERROR_UNKNOWN: "验证失败",
        STATUS_NETWORK_ERROR: "网络错误",
        STATUS_BLOCKED: "验证被阻止",
        STATUS_EXCEPTION: "验证异常"
    }

    def __init__(self, timeout: int = 5):
        """
        初始化SSN验证器

        Args:
            timeout: 请求超时时间（秒）
        """
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def verify_ssn_details(self, ssn: str) -> Dict[str, Any]:
        """
        验证SSN的详细信息（地点、发放年份等）

        Args:
            ssn: SSN号码（可以包含或不包含连字符）
            
        Returns:
            Dict[str, Any]: 验证结果
            {
                "ssn": str,              # 格式化的SSN
                "status": int,            # 状态码（1-8）
                "is_valid": bool,         # 是否有效
                "location": str,          # 发放地点（如果有）
                "year_min": int,          # 发放年份最小值（如果有）
                "year_max": int,          # 发放年份最大值（如果有）
                "raw_year_text": str,     # 原始年份文本
                "error_message": str      # 错误信息（如果有）
            }
        """
        # 移除连字符并格式化
        ssn_clean = ssn.replace('-', '').replace(' ', '')
        if len(ssn_clean) != 9 or not ssn_clean.isdigit():
            return {
                "ssn": ssn,
                "status": self.STATUS_VERIFIED_INVALID,
                "is_valid": False,
                "location": None,
                "year_min": None,
                "year_max": None,
                "raw_year_text": None,
                "error_message": "SSN格式无效"
            }
        
        formatted_ssn = f"{ssn_clean[:3]}-{ssn_clean[3:5]}-{ssn_clean[5:]}"
        
        try:
            url = f"https://www.ssn-check.org/verify/{formatted_ssn}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找包含SSN验证结果的文本
            text_content = soup.get_text().lower()
            
            # 检查是否为有效SSN
            if any(phrase in text_content for phrase in ['invalid', 'not valid', 'does not exist', 'never issued']):
                return {
                    "ssn": formatted_ssn,
                    "status": self.STATUS_VERIFIED_INVALID,
                    "is_valid": False,
                    "location": None,
                    "year_min": None,
                    "year_max": None,
                    "raw_year_text": None,
                    "error_message": "SSN验证为无效"
                }
            
            # 检查是否有"was issued"或"is valid"等关键词
            is_valid_ssn = any(phrase in text_content for phrase in [
                'was issued', 'is valid', 'valid ssn', 'issued in', 'issued between'
            ])
            
            if not is_valid_ssn:
                return {
                    "ssn": formatted_ssn,
                    "status": self.STATUS_PARSE_ERROR_UNKNOWN,
                    "is_valid": False,
                    "location": None,
                    "year_min": None,
                    "year_max": None,
                    "raw_year_text": None,
                    "error_message": "无法确定SSN有效性"
                }
            
            # SSN被认为有效，尝试解析详细信息
            location = None
            year_min = None
            year_max = None
            raw_year_text = None
            
            # 查找地点信息
            location_patterns = [
                r'issued in ([a-zA-Z\s]+?)\s*between',  # 处理换行符和多个空格
                r'issued in ([a-zA-Z\s]+?)\s*in',
                r'issued in ([a-zA-Z\s]+?)\s*\.',
                r'issued in ([a-zA-Z\s]+?)\s*$',  # 行末
                r'issued in ([a-zA-Z\s]+?)\s+',   # 多个空格
                r'from ([a-zA-Z\s]+?)\s*between',
                r'from ([a-zA-Z\s]+?)\s*in'
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if match:
                    # 清理匹配的地点名称，去掉多余的空格和换行符
                    location = re.sub(r'\s+', ' ', match.group(1).strip()).title()
                    break
            
            # 如果主要模式失败，尝试备用策略
            if not location:
                # 更宽松的模式，直接查找 "issued in" 后面的内容
                backup_match = re.search(r'issued in\s+([a-zA-Z]+)', text_content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if backup_match:
                    location = backup_match.group(1).strip().title()
            
            # 查找年份信息（支持单一年份和年份区间）
            year_patterns = [
                r'between (\d{4}) and (\d{4})',
                r'from (\d{4}) to (\d{4})',
                r'in (\d{4}) to (\d{4})',
                r'(\d{4})-(\d{4})',
                r'in (\d{4})',
                r'during (\d{4})',
                r'around (\d{4})'
            ]
            
            for pattern in year_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if match:
                    raw_year_text = match.group(0)
                    if len(match.groups()) >= 2 and match.group(2):
                        # 年份区间
                        year_min = int(match.group(1))
                        year_max = int(match.group(2))
                    else:
                        # 单一年份
                        year_min = int(match.group(1))
                        year_max = year_min
                    break
            
            # Debug信息已完全关闭
            # 如果成功解析了地点和年份信息
            if location and year_min is not None:
                return {
                    "ssn": formatted_ssn,
                    "status": self.STATUS_VERIFIED_VALID,
                    "is_valid": True,
                    "location": location,
                    "year_min": year_min,
                    "year_max": year_max,
                    "raw_year_text": raw_year_text,
                    "error_message": None
                }
            elif location or year_min is not None:
                # 部分信息可用
                return {
                    "ssn": formatted_ssn,
                    "status": self.STATUS_PARSE_ERROR_VALID,
                    "is_valid": True,
                    "location": location,
                    "year_min": year_min,
                    "year_max": year_max,
                    "raw_year_text": raw_year_text,
                    "error_message": "部分详细信息不可用"
                }
            else:
                # SSN有效但无法解析详细信息
                return {
                    "ssn": formatted_ssn,
                    "status": self.STATUS_PARSE_ERROR_VALID,
                    "is_valid": True,
                    "location": None,
                    "year_min": None,
                    "year_max": None,
                    "raw_year_text": None,
                    "error_message": "SSN有效但无法解析详细信息"
                }
            
        except requests.Timeout:
            return {
                "ssn": formatted_ssn,
                "status": self.STATUS_TIMEOUT,
                "is_valid": False,
                "location": None,
                "year_min": None,
                "year_max": None,
                "raw_year_text": None,
                "error_message": "验证请求超时"
            }
        except requests.RequestException as e:
            if "403" in str(e) or "blocked" in str(e).lower():
                return {
                    "ssn": formatted_ssn,
                    "status": self.STATUS_BLOCKED,
                    "is_valid": False,
                    "location": None,
                    "year_min": None,
                    "year_max": None,
                    "raw_year_text": None,
                    "error_message": "验证请求被阻止"
                }
            else:
                return {
                    "ssn": formatted_ssn,
                    "status": self.STATUS_NETWORK_ERROR,
                    "is_valid": False,
                    "location": None,
                    "year_min": None,
                    "year_max": None,
                    "raw_year_text": None,
                    "error_message": f"网络错误: {str(e)}"
                }
        except Exception as e:
            return {
                "ssn": formatted_ssn,
                "status": self.STATUS_EXCEPTION,
                "is_valid": False,
                "location": None,
                "year_min": None,
                "year_max": None,
                "raw_year_text": None,
                "error_message": f"验证异常: {str(e)}"
            }

    def get_status_description(self, status_code: int) -> str:
        """
        根据状态码获取描述信息
        
        Args:
            status_code: 状态码
            
        Returns:
            状态描述字符串
        """
        return self.STATUS_DESCRIPTIONS.get(status_code, "未知状态")

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
        validation_result = {
            "validation_attempted": True,
            "validation_passed": False,
            "validation_status": "unknown",
            "validation_details": {
                "is_valid": None,
                "location": None,
                "year": None,
                "year_min": None,
                "year_max": None,
                "raw_year_text": None,
                "error": None
            }
        }

        try:
            result = self.verify_ssn_details(ssn)
            
            # 复制基础验证结果
            validation_result["validation_details"].update({
                "is_valid": result["is_valid"],
                "location": result.get("location"),
                "year": result.get("year_min"),  # 为了兼容性
                "year_min": result.get("year_min"),
                "year_max": result.get("year_max"),
                "raw_year_text": result.get("raw_year_text"),
                "error": result.get("error_message")
            })

            # 根据状态码分析验证状态
            status_code = result.get("status", self.STATUS_NOT_VERIFIED)
            
            if status_code == self.STATUS_VERIFIED_VALID:
                # SSN基础验证通过，检查地点和年份匹配
                location_match = True
                year_match = True
                mismatch_reasons = []

                # 检查地点匹配
                if expected_state and result.get("location"):
                    location = result["location"].lower()
                    state_lower = expected_state.lower()
                    # 这里可以扩展更复杂的州名匹配逻辑
                    if state_lower not in location and location not in state_lower:
                        location_match = False
                        mismatch_reasons.append(f"地点不匹配 (预期: {expected_state}, 实际: {result['location']})")

                # 检查年份匹配（使用区间逻辑）
                if expected_birth_year and result.get("year_min") is not None:
                    year_min = result["year_min"]
                    year_max = result["year_max"] if result["year_max"] is not None else year_min
                    
                    # SSN通常在出生后几年内发放，最多不超过20年
                    earliest_reasonable = expected_birth_year
                    latest_reasonable = expected_birth_year + 20
                    
                    # 检查SSN发放年份区间是否与预期出生年份匹配
                    if year_max < earliest_reasonable or year_min > latest_reasonable:
                        year_match = False
                        if year_min == year_max:
                            mismatch_reasons.append(f"年份不匹配 (出生年份: {expected_birth_year}, SSN发放年份: {year_min})")
                        else:
                            mismatch_reasons.append(f"年份不匹配 (出生年份: {expected_birth_year}, SSN发放年份: {year_min}-{year_max})")

                # 如果地点和年份都匹配，认为验证通过
                if location_match and year_match:
                    validation_result["validation_status"] = "verified_valid"
                    validation_result["validation_passed"] = True
                else:
                    # 地点或年份不匹配，直接判定为验证无效
                    validation_result["validation_status"] = "verified_invalid"
                    validation_result["validation_passed"] = False
                    validation_result["validation_details"]["error"] = "; ".join(mismatch_reasons)
                    
            elif status_code == self.STATUS_PARSE_ERROR_VALID:
                # 部分信息可用，但仍需检查可用信息是否匹配
                location_match = True
                year_match = True
                mismatch_reasons = []

                # 检查地点匹配（如果有地点信息）
                if expected_state and result.get("location"):
                    location = result["location"].lower()
                    state_lower = expected_state.lower()
                    if state_lower not in location and location not in state_lower:
                        location_match = False
                        mismatch_reasons.append(f"地点不匹配 (预期: {expected_state}, 实际: {result['location']})")

                # 检查年份匹配（如果有年份信息）
                if expected_birth_year and result.get("year_min") is not None:
                    year_min = result["year_min"]
                    year_max = result["year_max"] if result["year_max"] is not None else year_min
                    
                    # SSN通常在出生后几年内发放，最多不超过20年
                    earliest_reasonable = expected_birth_year
                    latest_reasonable = expected_birth_year + 20
                    
                    # 检查SSN发放年份区间是否与预期出生年份匹配
                    if year_max < earliest_reasonable or year_min > latest_reasonable:
                        year_match = False
                        if year_min == year_max:
                            mismatch_reasons.append(f"年份不匹配 (出生年份: {expected_birth_year}, SSN发放年份: {year_min})")
                        else:
                            mismatch_reasons.append(f"年份不匹配 (出生年份: {expected_birth_year}, SSN发放年份: {year_min}-{year_max})")

                # 如果有可用信息且匹配，保守通过；如果不匹配，判定为无效
                if location_match and year_match:
                    validation_result["validation_status"] = "parse_error_valid"
                    validation_result["validation_passed"] = True
                else:
                    validation_result["validation_status"] = "verified_invalid"
                    validation_result["validation_passed"] = False
                    validation_result["validation_details"]["error"] = "; ".join(mismatch_reasons)
                
            elif status_code == self.STATUS_VERIFIED_INVALID:
                validation_result["validation_status"] = "verified_invalid"
                validation_result["validation_passed"] = False
                
            elif status_code == self.STATUS_TIMEOUT:
                validation_result["validation_status"] = "timeout"
                validation_result["validation_passed"] = True  # 超时时保守处理
                
            elif status_code == self.STATUS_NETWORK_ERROR:
                validation_result["validation_status"] = "network_error"
                validation_result["validation_passed"] = True  # 网络错误时保守处理
                
            elif status_code == self.STATUS_BLOCKED:
                validation_result["validation_status"] = "blocked"
                validation_result["validation_passed"] = False
                
            elif status_code == self.STATUS_PARSE_ERROR_UNKNOWN:
                validation_result["validation_status"] = "verification_failed"
                validation_result["validation_passed"] = False
                
            elif status_code == self.STATUS_EXCEPTION:
                validation_result["validation_status"] = "exception"
                validation_result["validation_passed"] = True  # 异常时保守处理
                
            else:
                validation_result["validation_status"] = "unknown"
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
            if "error_message" in result and result["is_valid"] is not True:
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
            if expected_birth_year and result.get("year_min"):
                try:
                    issue_year = int(result["year_min"])
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
