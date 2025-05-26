"""
数据加载器模块
负责从JSON文件中加载各种数据库信息
"""

import json
import os
from typing import Dict, Any, List


class DataLoader:
    """数据加载器类"""

    def __init__(self, data_dir: str = "data"):
        """
        初始化数据加载器

        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self._cache = {}
        # 初始化countries属性
        self.countries = self.load_countries()

    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """
        加载JSON文件

        Args:
            file_path: JSON文件路径

        Returns:
            解析后的JSON数据
        """
        if file_path in self._cache:
            return self._cache[file_path]

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._cache[file_path] = data
                return data
        except FileNotFoundError:
            raise FileNotFoundError(f"找不到数据文件: {file_path}")
        except json.JSONDecodeError:
            raise ValueError(f"JSON文件格式错误: {file_path}")

    def load_countries(self) -> Dict[str, Any]:
        """加载国家配置"""
        return self._load_json(
            os.path.join(
                self.data_dir,
                "countries",
                "countries.json"))

    def load_names(self, country: str) -> Dict[str, List[str]]:
        """加载姓名数据"""
        file_path = os.path.join(
            self.data_dir,
            "names",
            f"{country}_first_names.json")
        first_names = self._load_json(file_path)

        file_path = os.path.join(
            self.data_dir,
            "names",
            f"{country}_last_names.json")
        last_names = self._load_json(file_path)

        return {
            "first_names": first_names,
            "last_names": last_names
        }

    def load_phones(self, country: str) -> Dict[str, Any]:
        """加载电话号码格式"""
        file_path = os.path.join(
            self.data_dir,
            "phones",
            f"{country}_phone_formats.json")
        return self._load_json(file_path)

    def load_ssn(self, country: str) -> Dict[str, Any]:
        """加载社会保障号格式"""
        file_path = os.path.join(
            self.data_dir,
            "ssn",
            f"{country}_ssn_formats.json")
        return self._load_json(file_path)

    def load_addresses(self, country: str) -> Dict[str, Any]:
        """加载地址数据"""
        file_path = os.path.join(
            self.data_dir,
            "addresses",
            f"{country}_addresses.json")
        return self._load_json(file_path)

    def load_schools(self, country: str) -> Dict[str, Any]:
        """加载学校数据"""
        file_path = os.path.join(
            self.data_dir,
            "schools",
            f"{country}_schools.json")
        return self._load_json(file_path)

    def get_supported_countries(self) -> List[str]:
        """获取支持的国家列表"""
        return list(self.countries.keys())

    def get_states_for_country(self, country):
        """获取指定国家的州列表"""
        if country not in self.countries:
            return []

        country_data = self.countries[country]
        if 'states' not in country_data:
            return []

        return country_data['states']

    def get_state_info(self, country, state_code):
        """获取州的详细信息"""
        if country not in self.countries:
            return None

        country_data = self.countries[country]
        if 'states' not in country_data or state_code not in country_data['states']:
            return None

        return country_data['states'][state_code]
