import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import re
import random
import logging

# 配置日志记录
logger = logging.getLogger(__name__)


class HighGroupLoader:
    """加载和管理SSN高组清单历史数据"""

    def __init__(self, high_group_dir: str = "High Group"):
        self.high_group_dir = high_group_dir
        self.high_group_data = {}
        self.group_sequence = self._get_group_sequence()
        self.load_all_data()

    def _get_group_sequence(self) -> List[int]:
        """获取SSN组号分配顺序"""
        sequence = []
        # 奇数 01-09
        sequence.extend([1, 3, 5, 7, 9])
        # 偶数 10-98
        sequence.extend(range(10, 99, 2))
        # 偶数 02-08
        sequence.extend([2, 4, 6, 8])
        # 奇数 11-99
        sequence.extend(range(11, 100, 2))
        return sequence

    def load_all_data(self):
        """加载所有年份的高组清单数据"""
        if not os.path.exists(self.high_group_dir):
            logger.warning(f"警告：高组清单目录 {self.high_group_dir} 不存在")
            return

        for year_dir in os.listdir(self.high_group_dir):
            year_path = os.path.join(self.high_group_dir, year_dir)
            if os.path.isdir(year_path) and year_dir.isdigit():
                year = int(year_dir)
                self.high_group_data[year] = {}

                for month_file in os.listdir(year_path):
                    if month_file.endswith(
                            '.txt') and month_file[:-4].isdigit():
                        month = int(month_file[:-4])
                        file_path = os.path.join(year_path, month_file)
                        try:
                            data = self._parse_high_group_file(file_path)
                            self.high_group_data[year][month] = data
                        except Exception as e:
                            logger.error(f"解析文件失败 {file_path}: {e}")

    def _parse_high_group_file(self, file_path: str) -> Dict[int, int]:
        """解析单个高组清单文件"""
        data = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 使用正则表达式提取区域号和组号
        pattern = r'(\d{3})\s+(\d{2})'
        matches = re.findall(pattern, content)

        for area_str, group_str in matches:
            area = int(area_str)
            group = int(group_str)
            data[area] = group

        return data

    def get_highest_group(
            self,
            area: int,
            year: int,
            month: int) -> Optional[int]:
        """获取指定时间的最高组号"""
        if year in self.high_group_data and month in self.high_group_data[year]:
            return self.high_group_data[year][month].get(area)
        return None

    def get_valid_groups_for_date(
            self,
            area: int,
            year: int,
            month: int) -> List[int]:
        """获取指定日期前所有有效的组号"""
        highest_group = self.get_highest_group(area, year, month)
        if highest_group is None:
            return []

        valid_groups = []
        for group in self.group_sequence:
            if group <= highest_group:
                valid_groups.append(group)
            else:
                break

        return valid_groups

    def estimate_group_assignment_date(
            self, area: int, group: int) -> Optional[Tuple[int, int]]:
        """估算指定组号的分配时间（年，月）"""
        for year in sorted(self.high_group_data.keys()):
            for month in sorted(self.high_group_data[year].keys()):
                highest_group = self.get_highest_group(area, year, month)
                if highest_group is not None and group <= highest_group:
                    return (year, month)
        return None

    def get_group_sequence_position(self, group: int) -> int:
        """获取组号在分配序列中的位置"""
        try:
            return self.group_sequence.index(group)
        except ValueError:
            return -1

    def get_suitable_group_for_birth_date(
            self,
            area: int,
            birth_year: int,
            birth_month: int) -> Optional[int]:
        """根据出生日期获取合适的组号"""
        # SSN通常在出生后几个月到几年内分配
        # 对于1980年代以前：通常在工作年龄(14-18岁)获得
        # 对于1980年代后：逐渐在更小年龄获得，现在基本出生时就有

        if birth_year < 1980:
            # 假设在14-18岁获得SSN
            assignment_year = birth_year + 16
        elif birth_year < 1990:
            # 假设在5-14岁获得SSN
            assignment_year = birth_year + 8
        elif birth_year < 2000:
            # 假设在1-5岁获得SSN
            assignment_year = birth_year + 2
        else:
            # 假设出生时或1岁内获得SSN
            assignment_year = birth_year + 1

        # 获取该时期的有效组号
        valid_groups = self.get_valid_groups_for_date(area, assignment_year, 6)

        if not valid_groups:
            # 如果没有数据，使用改进的备用估计
            # 现在我们有1985年开始的数据，可以做更好的估计
            available_years = self.get_available_years()
            if available_years and assignment_year < min(available_years):
                # 对于早于数据范围的年份，使用保守估计
                if birth_year < 1960:
                    return min(10, max(1, (birth_year - 1940) // 2))  # 非常早期，组号很小
                elif birth_year < 1970:
                    return min(20, max(1, int((birth_year - 1950) // 1.5)))  # 早期，组号较小
                elif birth_year < 1980:
                    return min(30, max(1, (birth_year - 1960)))  # 中期，组号中等
                else:
                    return min(40, max(1, int((birth_year - 1970) * 1.5)))  # 较晚期
            else:
                # 原有的备用逻辑，用于其他情况
                if birth_year < 1990:
                    return min(20, max(1, (birth_year - 1970) * 2))
                else:
                    return min(50, max(1, (birth_year - 1970) * 3))

        # 在有效组号中随机选择，但偏向较早的组号
        if len(valid_groups) <= 5:
            return random.choice(valid_groups)
        else:
            # 70%概率选择前半部分的组号
            if random.random() < 0.7:
                return random.choice(valid_groups[:len(valid_groups) // 2])
            else:
                return random.choice(valid_groups[len(valid_groups) // 2:])

    def validate_ssn_timing(self, area: int, group: int, serial: int,
                            birth_year: int, birth_month: int) -> bool:
        """验证SSN时间合理性"""
        # 计算该人应该获得SSN的时间范围
        if birth_year < 1980:
            # 1980年前出生：通常在14-18岁获得SSN
            expected_ssn_year_min = birth_year + 14
            expected_ssn_year_max = birth_year + 18
        elif birth_year < 1990:
            # 1980-1990：通常在5-14岁获得SSN
            expected_ssn_year_min = birth_year + 5
            expected_ssn_year_max = birth_year + 14
        elif birth_year < 2000:
            # 1990-2000：通常在1-5岁获得SSN
            expected_ssn_year_min = birth_year + 1
            expected_ssn_year_max = birth_year + 5
        else:
            # 2000年后：通常出生时或1岁内获得SSN
            expected_ssn_year_min = birth_year
            expected_ssn_year_max = birth_year + 1

        # 动态获取实际数据范围（包括推测数据）
        available_years = self.get_available_years()
        if not available_years:
            return True  # 没有数据时假设有效
            
        our_data_start_year = min(available_years)  # 现在是1985年
        our_data_end_year = max(available_years)    # 现在是2011年

        # 如果该人应该在我们的数据范围之前获得SSN，使用历史合理性检查
        if expected_ssn_year_max < our_data_start_year:
            # 对于应该在1985年前获得SSN的人，使用历史合理性检查
            # 这主要适用于1960年代及更早出生的人
            if birth_year < 1960:
                return group <= 15  # 1960年前出生的人，组号应该很小
            elif birth_year < 1970:
                return group <= 25  # 1960-1970年出生的人，组号相对较小
            else:
                return group <= 35  # 1970-1985年可能获得SSN的人
                
        # 如果该人应该在我们的数据范围内获得SSN，则可以使用精确数据验证
        if expected_ssn_year_min <= our_data_end_year:
            assignment_date = self.estimate_group_assignment_date(area, group)

            if assignment_date is None:
                return True  # 没有数据时假设有效

            assignment_year, assignment_month = assignment_date

            # 检查分配时间是否在出生后
            if assignment_year < birth_year or (
                    assignment_year == birth_year and assignment_month < birth_month):
                return False

            # 检查分配时间是否在合理范围内
            if assignment_year < expected_ssn_year_min or assignment_year > expected_ssn_year_max:
                return False

        return True

    def get_available_years(self) -> List[int]:
        """获取可用的年份列表"""
        return sorted(self.high_group_data.keys())

    def get_available_months(self, year: int) -> List[int]:
        """获取指定年份的可用月份列表"""
        if year in self.high_group_data:
            return sorted(self.high_group_data[year].keys())
        return []

    def get_statistics(self) -> Dict:
        """获取数据统计信息"""
        total_files = 0
        total_areas = set()
        date_range = []

        for year, months in self.high_group_data.items():
            for month, data in months.items():
                total_files += 1
                total_areas.update(data.keys())
                date_range.append(f"{year}-{month:02d}")

        return {
            "total_files": total_files,
            "total_areas": len(total_areas),
            "date_range": f"{min(date_range)} 到 {max(date_range)}" if date_range else "无数据",
            "areas_covered": sorted(total_areas)}

    def get_conservative_groups_for_birth_date(
            self,
            area: int,
            birth_year: int,
            birth_month: int) -> Optional[int]:
        """
        激进策略：A年出生的人用(A+5)年的High Group数据
        这样可以确保SSN发放时间总是在出生后5年，避免验证失败
        
        Args:
            area: 区域号
            birth_year: 出生年份  
            birth_month: 出生月份
            
        Returns:
            合适的组号，如果没有则返回None
        """
        available_years = self.get_available_years()
        if not available_years:
            # 没有High Group数据，回退到原方法
            return self.get_suitable_group_for_birth_date(area, birth_year, birth_month)
        
        # 激进策略：使用出生年份+5年的数据，但需要考虑数据边界
        min_year = min(available_years)
        max_year = max(available_years)
        
        # 根据出生年份和数据可用性调整策略
        if birth_year + 5 <= max_year:
            # 理想情况：出生年份+5年在数据范围内
            target_year = birth_year + 5
        elif birth_year + 3 <= max_year:
            # 次优选择：出生年份+3年在数据范围内
            target_year = birth_year + 3
        elif birth_year + 1 <= max_year:
            # 保守选择：出生年份+1年在数据范围内
            target_year = birth_year + 1
        elif birth_year <= max_year:
            # 最保守：使用出生年份当年数据
            target_year = birth_year
        else:
            # 出生年份超出数据范围，使用最晚可用年份
            target_year = max_year
        
        # 确保不早于最小年份
        if target_year < min_year:
            target_year = min_year
        
        # 获取目标年份6月的数据（年中数据比较稳定）
        target_groups = self.get_valid_groups_for_date(area, target_year, 6)
        
        if not target_groups:
            # 如果目标年份6月没有数据，尝试其他月份
            available_months = self.get_available_months(target_year)
            if available_months:
                # 优先使用年中的月份
                preferred_months = [6, 5, 7, 4, 8, 3, 9, 2, 10, 1, 11, 12]
                for month in preferred_months:
                    if month in available_months:
                        target_groups = self.get_valid_groups_for_date(area, target_year, month)
                        if target_groups:
                            break
        
        if not target_groups:
            # 如果还是没有数据，回退到原方法
            return self.get_suitable_group_for_birth_date(area, birth_year, birth_month)
        
        # 为了确保生成的SSN更合理，我们需要严格过滤组号
        # 不仅要确保组号在出生后才可用，还要确保组号的分配年份不早于出生年份
        
        # 获取出生年份的组号数据作为参考
        birth_groups = self.get_valid_groups_for_date(area, birth_year, birth_month)
        if not birth_groups:
            birth_groups = []
        
        # 进一步过滤：确保选择的组号的分配时间不早于出生年份
        safe_groups = []
        for group in target_groups:
            if group not in birth_groups:  # 首先确保是新增组号
                # 检查这个组号的分配时间
                assignment_date = self.estimate_group_assignment_date(area, group)
                if assignment_date:
                    assignment_year, assignment_month = assignment_date
                    # 确保分配年份不早于出生年份
                    if assignment_year >= birth_year:
                        safe_groups.append(group)
                else:
                    # 如果无法确定分配时间，保守地包含这个组号
                    safe_groups.append(group)
        
        # 如果严格过滤后没有合适的组号，回退到原来的新增组号列表
        newly_available = safe_groups if safe_groups else [g for g in target_groups if g not in birth_groups]
        
        if newly_available:
            # 优先选择新增的组号，这些组号确保在出生后才发放
            if len(newly_available) <= 5:
                return random.choice(newly_available)
            else:
                # 偏向选择较早的新增组号，但不要太晚
                mid_point = len(newly_available) // 2
                if random.random() < 0.7:
                    # 70%选择前半部分
                    return random.choice(newly_available[:mid_point])
                else:
                    # 30%选择后半部分
                    return random.choice(newly_available[mid_point:])
        else:
            # 如果没有新增组号，选择目标年份的较高组号
            # 这种情况可能发生在出生年份很早的情况下
            if len(target_groups) > 20:
                # 选择后1/3的组号
                high_groups = target_groups[-len(target_groups)//3:]
                return random.choice(high_groups)
            elif len(target_groups) > 5:
                # 选择后半部分
                return random.choice(target_groups[-len(target_groups)//2:])
            else:
                # 数据太少，随机选择
                return random.choice(target_groups)
