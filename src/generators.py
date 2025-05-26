"""
信息生成器模块
包含各种虚拟信息的生成逻辑
"""

import random
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from data_loader import DataLoader
from high_group_loader import HighGroupLoader
from ssn_validator import SSNValidator


class PersonGenerator:
    """虚拟公民信息生成器"""

    def __init__(
            self,
            data_loader: DataLoader,
            enable_ssn_validation: bool = False):
        """
        初始化生成器

        Args:
            data_loader: 数据加载器实例
            enable_ssn_validation: 是否启用SSN验证
        """
        self.data_loader = data_loader
        # 初始化高组清单加载器
        self.high_group_loader = HighGroupLoader()
        # 静默加载，不输出统计信息以保持JSON格式纯净

        # SSN验证器
        self.enable_ssn_validation = enable_ssn_validation
        if enable_ssn_validation:
            self.ssn_validator = SSNValidator(timeout=5)
        else:
            self.ssn_validator = None

    def generate_email(self, name: Dict[str, str], birthday: str) -> str:
        """
        生成邮箱地址

        Args:
            name: 姓名字典
            birthday: 生日字符串 (YYYYMMDD)

        Returns:
            邮箱地址字符串
        """
        # 清理名字中的特殊字符，只保留字母和数字
        first_name = re.sub(r'[^a-zA-Z0-9]', '', name["first_name"].lower())
        last_name = re.sub(r'[^a-zA-Z0-9]', '', name["last_name"].lower())
        birth_year = birthday[:4]
        birth_month = birthday[4:6]
        birth_day = birthday[6:8]

        # 美国最常用的邮箱域名
        email_domains = [
            "gmail.com",     # 17.74%
            "yahoo.com",     # 17.34%
            "hotmail.com",   # 15.53%
            "outlook.com",   # 0.38% 但现代很常用
            "aol.com",       # 3.2%
            "icloud.com",    # Apple用户常用
            "live.com",      # 0.56%
            "comcast.net",   # 0.76%
            "verizon.net",   # 0.22%
            "cox.net"        # 0.25%
        ]

        # 生成多种前缀格式，确保长度>6且以字母开头
        prefix_formats = []

        # 格式1: firstname.lastname
        prefix_formats.append(f"{first_name}.{last_name}")

        # 格式2: firstname + lastname
        prefix_formats.append(f"{first_name}{last_name}")

        # 格式3: firstname + 数字
        prefix_formats.append(f"{first_name}{birth_year}")
        prefix_formats.append(f"{first_name}{birth_year[-2:]}")
        prefix_formats.append(f"{first_name}{birth_month}{birth_day}")

        # 格式4: lastname + 数字
        prefix_formats.append(f"{last_name}{birth_year}")
        prefix_formats.append(f"{last_name}{birth_year[-2:]}")

        # 格式5: 名字缩写 + lastname
        if first_name:
            prefix_formats.append(f"{first_name[0]}{last_name}")
            prefix_formats.append(f"{first_name[0]}.{last_name}")

        # 格式6: firstname + lastname缩写
        if last_name:
            prefix_formats.append(f"{first_name}{last_name[0]}")
            prefix_formats.append(f"{first_name}.{last_name[0]}")

        # 格式7: 添加随机数字
        random_nums = [
            str(random.randint(10, 99)),
            str(random.randint(100, 999)),
            str(random.randint(1, 9)),
            birth_month + birth_day,
            birth_day + birth_month
        ]
        for num in random_nums[:2]:  # 只取前两个避免太多选项
            prefix_formats.append(f"{first_name}{num}")
            prefix_formats.append(f"{last_name}{num}")

        # 格式8: 添加常见字母组合
        common_letters = ['x', 'z', 'j', 'k', 'q']
        for letter in random.sample(common_letters, 2):
            prefix_formats.append(f"{first_name}{letter}")
            prefix_formats.append(f"{last_name}{letter}")

        # 过滤掉长度不够或不以字母开头的前缀
        valid_prefixes = []
        for prefix in prefix_formats:
            if len(prefix) >= 6 and prefix[0].isalpha():
                valid_prefixes.append(prefix)

        # 如果没有有效前缀，创建一个默认的
        if not valid_prefixes:
            valid_prefixes = [f"{first_name}{last_name}{birth_year[-2:]}"]

        # 随机选择前缀和域名
        prefix = random.choice(valid_prefixes)
        domain = random.choice(email_domains)

        return f"{prefix}@{domain}"

    def generate_name(self, country: str, gender: str) -> Dict[str, str]:
        """
        生成姓名

        Args:
            country: 国家代码
            gender: 性别 (male/female)

        Returns:
            包含first_name和last_name的字典
        """
        names_data = self.data_loader.load_names(country)

        # 选择合适的名字列表
        if gender == "male":
            first_names = names_data["first_names"]["male_names"]
        else:
            first_names = names_data["first_names"]["female_names"]

        last_names = names_data["last_names"]["last_names"]

        return {
            "first_name": random.choice(first_names),
            "last_name": random.choice(last_names)
        }

    def generate_birthday(self, age_range: str) -> str:
        """
        生成生日

        Args:
            age_range: 年龄范围，格式如 "20-25"

        Returns:
            生日字符串，格式为 YYYYMMDD
        """
        current_year = datetime.now().year

        if age_range:
            try:
                min_age, max_age = map(int, age_range.split('-'))
            except ValueError:
                min_age, max_age = 18, 30
        else:
            min_age, max_age = 18, 30

        # 根据年龄范围计算出生年份范围
        max_birth_year = current_year - min_age
        min_birth_year = current_year - max_age

        # 生成随机出生年份
        birth_year = random.randint(min_birth_year, max_birth_year)
        birth_month = random.randint(1, 12)

        # 根据月份确定天数
        if birth_month in [1, 3, 5, 7, 8, 10, 12]:
            max_day = 31
        elif birth_month in [4, 6, 9, 11]:
            max_day = 30
        else:  # 2月
            # 更准确的闰年判断
            if (birth_year %
                4 == 0 and birth_year %
                100 != 0) or (birth_year %
                              400 == 0):
                max_day = 29
            else:
                max_day = 28

        birth_day = random.randint(1, max_day)

        return f"{birth_year}{birth_month:02d}{birth_day:02d}"

    def generate_phone(self, country: str, state: str) -> str:
        """
        生成电话号码

        Args:
            country: 国家代码
            state: 州/地区代码

        Returns:
            电话号码字符串
        """
        phone_data = self.data_loader.load_phones(country)
        country_data = phone_data[country]

        # 获取该州的区号
        area_codes = country_data["area_codes"].get(state, [])
        if not area_codes:
            # 如果没有找到州的区号，随机选择一个有效的区号
            all_area_codes = []
            for codes in country_data["area_codes"].values():
                all_area_codes.extend(codes)
            area_code = random.choice(all_area_codes)
        else:
            area_code = random.choice(area_codes)

        # 生成exchange（中间三位）
        # 第一位必须是2-9，不能是N11格式
        while True:
            first_digit = random.randint(2, 9)
            second_digit = random.randint(0, 9)
            third_digit = random.randint(0, 9)

            # 检查是否为N11格式（例如：211, 311, 411等）
            if second_digit == 1 and third_digit == 1:
                continue

            exchange = f"{first_digit}{second_digit}{third_digit}"
            break

        # 生成line number（最后四位）
        # 0000-9999都可用，无特殊限制
        line = random.randint(0, 9999)

        # 格式化电话号码
        return f"({area_code}) {exchange}-{line:04d}"

    def generate_ssn(self, country: str, state: str = None,
                     birth_year: int = None) -> Tuple[str, bool]:
        """
        生成社会保障号（支持在线验证）

        Args:
            country: 国家代码
            state: 州/地区代码
            birth_year: 出生年份（用于确保SSN发放时间合理）

        Returns:
            Tuple[str, bool]: (SSN字符串, 是否验证通过)
        """
        if not self.enable_ssn_validation:
            # 如果没有启用验证，返回SSN和False
            ssn = self._generate_ssn_internal(country, state, birth_year)
            return ssn, False

        # 启用验证的情况下，尝试生成并验证SSN
        max_attempts = 10  # 最多尝试10次

        for attempt in range(max_attempts):
            ssn = self._generate_ssn_internal(country, state, birth_year)

            try:
                # 使用简化验证方法
                is_verified = self.ssn_validator.validate_ssn_simple(
                    ssn, state, birth_year)
                if is_verified:
                    return ssn, True
                # 验证失败，继续下一次尝试
            except Exception:
                # 验证过程中出现异常，返回当前SSN和False
                return ssn, False

        # 如果所有尝试都失败，返回最后一次生成的SSN和False
        return ssn, False

    def _generate_ssn_internal(
            self,
            country: str,
            state: str = None,
            birth_year: int = None) -> str:
        """
        生成社会保障号（基于真实高组清单数据）

        Args:
            country: 国家代码
            state: 州/地区代码
            birth_year: 出生年份（用于确保SSN发放时间合理）

        Returns:
            社会保障号字符串
        """
        ssn_data = self.data_loader.load_ssn(country)
        country_data = ssn_data[country]

        # 1. 根据州获取区域号范围
        if not state or state not in country_data["structure"]["area_number"]["state_ranges"]:
            # 如果没有指定州或州不存在，随机选择一个州
            state = random.choice(
                list(country_data["structure"]["area_number"]["state_ranges"].keys()))

        area_ranges = country_data["structure"]["area_number"]["state_ranges"][state]
        area_number = None

        # 从州的可用范围中随机选择一个区域号
        range_str = random.choice(area_ranges)
        if "-" in range_str:
            start, end = map(int, range_str.split("-"))
            area_number = random.randint(start, end)
        else:
            area_number = int(range_str)

        # 2. 根据出生年份确定合理的SSN发放时间
        current_year = datetime.now().year
        if birth_year:
            # 计算合理的SSN分配时间
            if birth_year < 1980:
                # 1980年前：通常在工作年龄(14-18岁)获得SSN
                estimated_issue_year = birth_year + random.randint(14, 18)
            elif birth_year < 1990:
                # 1980-1990：逐渐在更小年龄获得SSN
                estimated_issue_year = birth_year + random.randint(5, 14)
            elif birth_year < 2000:
                # 1990-2000：通常在1-5岁获得SSN
                estimated_issue_year = birth_year + random.randint(1, 5)
            else:
                # 2000年后：通常出生时或1岁内获得SSN
                estimated_issue_year = birth_year + random.randint(0, 1)

            # 确保不超过当前年份
            estimated_issue_year = min(estimated_issue_year, current_year)
        else:
            # 如果没有出生年份，假设是在过去30年内发放的
            estimated_issue_year = random.randint(
                current_year - 30, current_year)

        # 3. 使用高组清单数据获取合适的组号
        # 首先检查是否应该在我们的数据范围内分配SSN
        our_data_start_year = 2003
        our_data_end_year = 2011

        if estimated_issue_year < our_data_start_year:
            # 应该在我们数据范围之前分配的SSN，使用历史估算方法
            group_number = self._generate_historical_group(
                birth_year, estimated_issue_year)
        elif estimated_issue_year <= our_data_end_year and self.high_group_loader.high_group_data:
            # 在我们数据范围内，使用真实的高组清单数据
            group_number = self.high_group_loader.get_suitable_group_for_birth_date(
                area_number, birth_year or (estimated_issue_year - 16), 6)

            if group_number is None:
                # 如果没有对应的数据，回退到传统方法
                group_number = self._generate_fallback_group(
                    estimated_issue_year)
        else:
            # 2011年后或没有高组清单数据时：使用回退方法
            group_number = self._generate_fallback_group(estimated_issue_year)

        # 4. 生成序列号，考虑时间因素和真实性
        if estimated_issue_year <= 2011:
            # 2011年前：序列号按时间顺序分配，偏向较低值
            if estimated_issue_year <= 1990:
                # 早期：使用较低的序列号
                max_serial = random.randint(3000, 6000)
                serial_number = random.randint(1, max_serial // 2)
            elif estimated_issue_year <= 2000:
                # 中期：使用中等范围的序列号
                max_serial = random.randint(5000, 8000)
                serial_number = random.randint(1000, max_serial)
            else:
                # 后期：可以使用更高的序列号
                max_serial = random.randint(7000, 9999)
                serial_number = random.randint(2000, max_serial)
        else:
            # 2011年后：完全随机
            serial_number = random.randint(1, 9999)

        # 5. 验证生成的SSN时间合理性
        generated_ssn = f"{area_number:03d}-{group_number:02d}-{serial_number:04d}"

        if birth_year and self.high_group_loader.high_group_data:
            is_valid = self.high_group_loader.validate_ssn_timing(
                area_number, group_number, serial_number, birth_year, 6
            )
            if not is_valid:
                # 如果不合理，重新生成一个较早的组号
                group_number = max(1, group_number - random.randint(5, 15))
                group_number = min(group_number, 99)
                generated_ssn = f"{area_number:03d}-{group_number:02d}-{serial_number:04d}"

        return generated_ssn

    def _generate_historical_group(
            self,
            birth_year: int,
            estimated_issue_year: int) -> int:
        """
        为早期出生的人生成历史上合理的组号

        Args:
            birth_year: 出生年份
            estimated_issue_year: 估计的SSN分配年份

        Returns:
            组号
        """
        # 基于历史分配模式的估算
        # SSN组号按顺序分配：01,03,05,07,09 → 10,12,14...98 → 02,04,06,08 →
        # 11,13,15...99

        if estimated_issue_year <= 1960:
            # 1960年前：只有最早的组号
            return random.choice([1, 3, 5, 7, 9])
        elif estimated_issue_year <= 1970:
            # 1960-1970：扩展到前20个组号
            sequence = [1, 3, 5, 7, 9, 10, 12, 14, 16, 18,
                        20, 22, 24, 26, 28, 30, 32, 34, 36, 38]
            return random.choice(
                sequence[:min(len(sequence), (estimated_issue_year - 1950) * 2)])
        elif estimated_issue_year <= 1980:
            # 1970-1980：可能到达组号40-50范围
            max_group = min(50, (estimated_issue_year - 1950) * 1.5)
            # 按SSN分配顺序选择
            sequence = [1, 3, 5, 7, 9] + \
                list(range(10, 99, 2)) + [2, 4, 6, 8] + list(range(11, 100, 2))
            valid_groups = [g for g in sequence if g <= max_group]
            return random.choice(valid_groups)
        elif estimated_issue_year <= 1990:
            # 1980-1990：可能到达组号60-80范围
            max_group = min(80, (estimated_issue_year - 1950) * 1.2)
            sequence = [1, 3, 5, 7, 9] + \
                list(range(10, 99, 2)) + [2, 4, 6, 8] + list(range(11, 100, 2))
            valid_groups = [g for g in sequence if g <= max_group]
            return random.choice(valid_groups)
        else:
            # 1990-2003：可能到达更高的组号，但仍然有限制
            max_group = min(95, 30 + (estimated_issue_year - 1990) * 5)
            sequence = [1, 3, 5, 7, 9] + \
                list(range(10, 99, 2)) + [2, 4, 6, 8] + list(range(11, 100, 2))
            valid_groups = [g for g in sequence if g <= max_group]
            return random.choice(valid_groups)

    def _generate_fallback_group(self, estimated_issue_year: int) -> int:
        """
        当没有高组清单数据时的回退组号生成方法

        Args:
            estimated_issue_year: 估计的发放年份

        Returns:
            组号
        """
        if estimated_issue_year <= 1990:
            # 早期：使用较小的组号，偏向奇数
            if random.random() < 0.7:  # 70%概率选择奇数
                return random.choice([1, 3, 5, 7, 9, 11, 13, 15, 17, 19])
            else:
                return random.choice([10, 12, 14, 16, 18, 20])
        elif estimated_issue_year <= 2000:
            # 中期：扩展到更多组号
            return random.randint(1, 50)
        elif estimated_issue_year <= 2011:
            # 后期：可以使用更大的组号
            return random.randint(1, 98)
        else:
            # 2011年后：完全随机
            return random.randint(1, 99)

    def generate_address(self, country: str, state: str) -> Dict[str, str]:
        """
        生成地址

        Args:
            country: 国家代码
            state: 州/地区代码

        Returns:
            包含地址信息的字典
        """
        address_data = self.data_loader.load_addresses(country)
        country_addresses = address_data[country]

        # 如果没有该州的地址，随机选择一个州
        if state not in country_addresses:
            state = random.choice(list(country_addresses.keys()))

        # 随机选择一个地址
        full_address = random.choice(country_addresses[state])

        # 解析地址 - 支持5位和9位邮编
        parts = full_address.split(", ")
        street = parts[0]
        city = parts[1]
        state_zip = parts[2].split()
        state_code = state_zip[0]

        # 处理邮编：支持5位 (12345) 或9位 (12345-6789) 格式
        if len(state_zip) > 1:
            zip_code = state_zip[1]
        else:
            zip_code = "00000"

        # 确保邮编格式正确
        if not zip_code or len(zip_code) < 5:
            zip_code = "00000"

        return {
            "street": street,
            "city": city,
            "state": state_code,
            "zip_code": zip_code,
            "full_address": full_address
        }

    def generate_education(self,
                           country: str,
                           state: str,
                           education_level: str,
                           birth_year: int) -> Dict[str,
                                                    Any]:
        """
        生成教育信息

        Args:
            country: 国家代码
            state: 州/地区代码
            education_level: 教育水平 (none/high_school/college)
            birth_year: 出生年份

        Returns:
            教育信息字典
        """
        if education_level == "none":
            return {"education_level": "none"}

        school_data = self.data_loader.load_schools(country)
        country_schools = school_data[country]

        # 如果没有该州的学校，随机选择一个州
        if state not in country_schools:
            state = random.choice(list(country_schools.keys()))

        education_info = {"education_level": education_level}

        # 高中信息
        if education_level in ["high_school", "college"]:
            high_school = random.choice(country_schools[state]["high_schools"])
            hs_start_year = birth_year + 14  # 通常14岁开始高中
            hs_end_year = hs_start_year + 4

            education_info["high_school"] = {
                "name": high_school["name"],
                "abbreviation": high_school["abbreviation"],
                "address": high_school["address"],
                "start_date": f"{hs_start_year}09",
                "graduation_date": f"{hs_end_year}06"
            }

        # 大学信息
        if education_level == "college":
            college = random.choice(country_schools[state]["colleges"])
            college_start_year = hs_end_year  # 高中毕业后直接上大学
            college_end_year = college_start_year + 4

            education_info["college"] = {
                "name": college["name"],
                "abbreviation": college["abbreviation"],
                "address": college["address"],
                "start_date": f"{college_start_year}09",
                "graduation_date": f"{college_end_year}06"
            }

        return education_info

    def _generate_parent(self, gender: str, country: str, state: str,
                         child_birth_year: int, parent_address: Dict[str, str],
                         last_name: str) -> Dict[str, Any]:
        """
        生成父母信息

        Args:
            gender: 父母性别
            country: 国家代码
            state: 州/地区代码
            child_birth_year: 孩子出生年份
            parent_address: 父母地址
            last_name: 姓氏

        Returns:
            父母信息字典
        """
        # 父母年龄通常比孩子大20-40岁
        parent_age_offset = random.randint(20, 40)
        parent_birth_year = child_birth_year - parent_age_offset

        # 计算父母当前年龄来生成生日
        current_year = datetime.now().year
        parent_current_age = current_year - parent_birth_year
        parent_age_range = f"{parent_current_age-1}-{parent_current_age+1}"

        # 使用generate_birthday方法确保日期有效性
        parent_birthday = self.generate_birthday(parent_age_range)

        # 生成父母名字（使用相同的姓氏）
        names_data = self.data_loader.load_names(country)
        if gender == "male":
            first_names = names_data["first_names"]["male_names"]
        else:
            first_names = names_data["first_names"]["female_names"]

        parent_name = {
            "first_name": random.choice(first_names),
            "last_name": last_name
        }

        # 使用父母所在的州
        parent_phone = self.generate_phone(country, parent_address["state"])

        # 父母SSN - 使用父母的出生年份
        ssn, is_verified = self.generate_ssn(
            country, parent_address["state"], int(parent_birthday[:4]))

        # 父母教育信息
        parent_education = self.generate_education(country, parent_address["state"],
                                                   random.choice(["high_school", "college"]),
                                                   int(parent_birthday[:4]))

        # 生成父母邮箱
        parent_email = self.generate_email(parent_name, parent_birthday)

        return {
            "name": parent_name,
            "gender": gender,
            "birthday": parent_birthday,
            "phone": parent_phone,
            "email": parent_email,
            "ssn": {
                "number": ssn,
                "verified": is_verified
            },
            "address": parent_address,
            "education": parent_education
        }

    def generate_parents(self,
                         parents_option: str,
                         country: str = None,
                         state: str = None,
                         child_birth_year: int = None,
                         child_address: Dict[str,
                                             str] = None,
                         last_name: str = None) -> Optional[Dict[str,
                                                                 Any]]:
        """
        生成父母信息

        Args:
            parents_option: 父母选项 (none/father/mother/both)
            country: 国家代码
            state: 州/地区代码
            child_birth_year: 孩子出生年份
            child_address: 孩子地址
            last_name: 姓氏

        Returns:
            父母信息字典
        """
        if not parents_option or parents_option == "none":
            return None

        parents_info = {}

        if parents_option in ["father", "both"]:
            father_info = self._generate_parent(
                "male", country, state, child_birth_year, child_address, last_name)
            parents_info["father"] = father_info

        if parents_option in ["mother", "both"]:
            mother_info = self._generate_parent(
                "female", country, state, child_birth_year, child_address, last_name)
            parents_info["mother"] = mother_info

        return parents_info

    def generate_person(self,
                        country: str = None,
                        gender: str = None,
                        state: str = None,
                        age: str = None,
                        education: str = None,
                        parents: str = None) -> Dict[str,
                                                     Any]:
        """生成虚拟公民信息"""
        # 设置默认国家
        country = country or "US"

        # 先生成姓名和生日，因为其他信息可能依赖这些
        name = self.generate_name(country, gender)
        birthday = self.generate_birthday(age)
        birth_year = int(birthday[:4])

        # 设置默认国家和州
        country = country or "US"
        state = state or random.choice(
            list(self.data_loader.get_states_for_country(country).keys()))

        # 生成地址信息（父母可能会用到）
        address = self.generate_address(country, state)

        # 生成SSN信息（包含验证状态）
        ssn, is_verified = self.generate_ssn(country, state, birth_year)

        # 生成基本信息
        person = {
            "name": name,
            "gender": gender or random.choice(["male", "female"]),
            "birthday": birthday,
            "country": country,
            "state": state,
            "address": address,
            "phone": self.generate_phone(country, state),
            "email": self.generate_email(name, birthday),
            "education": self.generate_education(country, state, education, birth_year),
            "parents": self.generate_parents(parents, country, state, birth_year, address, name["last_name"]),
            "ssn": {
                "number": ssn,
                "verified": is_verified
            }
        }

        # 添加州信息
        person["state_info"] = self.data_loader.get_state_info(
            person["country"], person["state"])

        return person
