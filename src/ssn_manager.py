"""
SSN管理器模块
统合所有SSN生成、验证和替换功能
"""

import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass

from data_loader import DataLoader
from high_group_loader import HighGroupLoader
from ssn_validator import SSNValidator


@dataclass
class SSNGenerationConfig:
    """SSN生成配置"""
    country: str
    state: str
    birth_year: int
    birth_month: int = 6
    max_attempts: int = 100
    concurrent_workers: int = 5
    timeout: int = 10


class SSNManager:
    """SSN管理器 - 统合所有SSN相关功能"""
    
    def __init__(self, data_loader: DataLoader):
        """
        初始化SSN管理器
        
        Args:
            data_loader: 数据加载器实例
        """
        self.data_loader = data_loader
        self.high_group_loader = HighGroupLoader()
        self._stop_event = threading.Event()
        
    def generate_ssn_local(self, config: SSNGenerationConfig) -> str:
        """
        本地生成SSN（不进行在线验证）
        
        Args:
            config: SSN生成配置
            
        Returns:
            生成的SSN字符串
        """
        ssn_data = self.data_loader.load_ssn(config.country)
        country_data = ssn_data[config.country]
        
        # 1. 根据州获取区域号范围
        if config.state not in country_data["structure"]["area_number"]["state_ranges"]:
            state = random.choice(list(country_data["structure"]["area_number"]["state_ranges"].keys()))
        else:
            state = config.state
            
        area_ranges = country_data["structure"]["area_number"]["state_ranges"][state]
        
        # 随机选择区域号
        range_str = random.choice(area_ranges)
        if "-" in range_str:
            start, end = map(int, range_str.split("-"))
            area_number = random.randint(start, end)
        else:
            area_number = int(range_str)
            
        # 2. 使用高组数据获取合适的组号
        group_number = None
        if self.high_group_loader.high_group_data:
            group_number = self.high_group_loader.get_conservative_groups_for_birth_date(
                area_number, config.birth_year, config.birth_month)
        
        if group_number is None:
            group_number = self._generate_fallback_group(config.birth_year)
            
        # 3. 生成序列号
        serial_number = self._generate_serial_number(config.birth_year)
        
        # 4. 格式化SSN
        return f"{int(area_number):03d}-{int(group_number):02d}-{int(serial_number):04d}"
    
    def generate_ssn_with_validation(self, config: SSNGenerationConfig) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        并行生成并验证SSN，直到找到有效的为止
        
        Args:
            config: SSN生成配置
            
        Returns:
            Tuple[Optional[str], Dict[str, Any]]: (SSN字符串或None, 验证状态详情)
        """
        self._stop_event.clear()
        result_lock = threading.Lock()
        valid_ssn_found = [None]  # 使用列表来存储结果，便于线程间共享
        validation_details = [None]
        
        def generate_and_validate_worker(worker_id: int) -> Optional[Tuple[str, Dict[str, Any]]]:
            """单个工作线程的生成和验证逻辑"""
            try:
                validator = SSNValidator(timeout=config.timeout)
                attempts = 0
                
                while attempts < config.max_attempts and not self._stop_event.is_set():
                    attempts += 1
                    
                    # 生成SSN
                    ssn = self.generate_ssn_local(config)
                    
                    try:
                        # 在线验证
                        validation_result = validator.validate_ssn_with_details(
                            ssn, config.state, config.birth_year)
                        
                        # 检查是否有效
                        if (validation_result.get("validation_passed") == True and 
                            validation_result.get("validation_status") == "verified_valid"):
                            
                            with result_lock:
                                if valid_ssn_found[0] is None:  # 第一个找到有效SSN的线程
                                    valid_ssn_found[0] = ssn
                                    validation_details[0] = validation_result
                                    self._stop_event.set()  # 通知其他线程停止
                                    return ssn, validation_result
                            
                    except Exception as e:
                        # 验证失败，继续尝试
                        continue
                        
                return None
                
            except Exception as e:
                print(f"Worker {worker_id} 异常: {str(e)}")
                return None
        
        # 使用线程池并行处理
        try:
            with ThreadPoolExecutor(max_workers=config.concurrent_workers) as executor:
                # 提交所有工作任务
                futures = [
                    executor.submit(generate_and_validate_worker, i) 
                    for i in range(config.concurrent_workers)
                ]
                
                # 等待第一个成功的结果
                for future in as_completed(futures, timeout=300):  # 5分钟超时
                    try:
                        result = future.result()
                        if result is not None:
                            # 找到有效SSN，取消其他任务
                            for f in futures:
                                f.cancel()
                            break
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"并行验证过程异常: {str(e)}")
        
        # 返回结果
        if valid_ssn_found[0] is not None:
            return valid_ssn_found[0], {
                "status": "verified_valid",
                "verified": True,
                "details": validation_details[0],
                "error": None
            }
        else:
            return None, {
                "status": "generation_failed_concurrent",
                "verified": False,
                "details": None,
                "error": f"经过{config.max_attempts}次并行尝试仍无法生成验证通过的SSN"
            }
    
    def replace_ssn_random(self, person_data: Dict[str, Any], target_path: str = None) -> Dict[str, Any]:
        """
        随机替换SSN（本地生成，不验证）
        
        Args:
            person_data: 人员数据
            target_path: 目标路径（"ssn", "parents.father.ssn", "parents.mother.ssn"）
            
        Returns:
            更新后的人员数据
        """
        # 解析目标路径
        if target_path is None:
            target_path = "ssn"
            
        # 获取配置信息
        birth_year = int(person_data["birthday"][:4])
        state = person_data["state"]
        
        config = SSNGenerationConfig(
            country=person_data["country"],
            state=state,
            birth_year=birth_year
        )
        
        # 生成新SSN
        new_ssn = self.generate_ssn_local(config)
        
        # 更新数据
        updated_data = person_data.copy()
        if target_path == "ssn":
            updated_data["ssn"] = {
                "number": new_ssn,
                "verified": False,
                "status": "not_verified",
                "details": None,
                "error": None
            }
        elif target_path.startswith("parents."):
            parts = target_path.split(".")
            parent_type = parts[1]  # father 或 mother
            if "parents" in updated_data and parent_type in updated_data["parents"]:
                updated_data["parents"][parent_type]["ssn"] = {
                    "number": new_ssn,
                    "verified": False,
                    "status": "not_verified", 
                    "details": None,
                    "error": None
                }
        
        return updated_data
    
    def replace_ssn_with_validation(self, person_data: Dict[str, Any], target_path: str = None) -> Tuple[Dict[str, Any], bool]:
        """
        在线验证替换SSN
        
        Args:
            person_data: 人员数据
            target_path: 目标路径（"ssn", "parents.father.ssn", "parents.mother.ssn"）
            
        Returns:
            Tuple[Dict[str, Any], bool]: (更新后的人员数据, 是否成功)
        """
        # 解析目标路径获取配置信息
        if target_path is None or target_path == "ssn":
            birth_year = int(person_data["birthday"][:4])
            target_path = "ssn"
        elif target_path.startswith("parents."):
            parts = target_path.split(".")
            parent_type = parts[1]
            if "parents" in person_data and parent_type in person_data["parents"]:
                birth_year = int(person_data["parents"][parent_type]["birthday"][:4])
            else:
                return person_data, False
        else:
            return person_data, False
            
        state = person_data["state"]
        
        config = SSNGenerationConfig(
            country=person_data["country"],
            state=state,
            birth_year=birth_year,
            max_attempts=20,  # 每个工作线程最多20次尝试
            concurrent_workers=5
        )
        
        # 并行生成并验证SSN
        new_ssn, validation_result = self.generate_ssn_with_validation(config)
        
        if new_ssn is not None:
            # 更新数据
            updated_data = person_data.copy()
            if target_path == "ssn":
                updated_data["ssn"] = {
                    "number": new_ssn,
                    "verified": validation_result["verified"],
                    "status": validation_result["status"],
                    "details": validation_result["details"],
                    "error": validation_result["error"]
                }
            elif target_path.startswith("parents."):
                parts = target_path.split(".")
                parent_type = parts[1]
                if "parents" in updated_data and parent_type in updated_data["parents"]:
                    updated_data["parents"][parent_type]["ssn"] = {
                        "number": new_ssn,
                        "verified": validation_result["verified"],
                        "status": validation_result["status"],
                        "details": validation_result["details"],
                        "error": validation_result["error"]
                    }
            
            return updated_data, True
        else:
            return person_data, False
    
    def _generate_fallback_group(self, birth_year: int) -> int:
        """生成备用组号"""
        current_year = 2024
        if birth_year < 1980:
            return random.choice([1, 3, 5, 7, 9, 11, 13, 15, 17, 19])
        elif birth_year <= 1995:
            return random.randint(70, 85)
        elif birth_year <= 2000:
            return random.randint(85, 95)
        elif birth_year <= 2011:
            return random.randint(95, 99)
        else:
            return random.randint(1, 99)
    
    def _generate_serial_number(self, birth_year: int) -> int:
        """生成序列号"""
        current_year = 2024
        if birth_year <= 1990:
            max_serial = random.randint(3000, 6000)
            return random.randint(1, max_serial // 2)
        elif birth_year <= 2000:
            max_serial = random.randint(5000, 8000)
            return random.randint(1000, max_serial)
        elif birth_year <= 2011:
            max_serial = random.randint(7000, 9999)
            return random.randint(2000, max_serial)
        else:
            return random.randint(1, 9999) 