#!/usr/bin/env python3
"""
虚拟公民信息生成器 Web UI
"""

import os
import sys
import json
import glob
import socket
import webbrowser
import random
import threading
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_loader import DataLoader
from generators import PersonGenerator
from formatters import OutputFormatter
from tools.import_addresses import AddressImporter
from ssn_manager import SSNManager

app = Flask(__name__)

# 全局变量
data_loader = None
generator = None
ssn_manager = None
address_lock = threading.Lock()  # 添加线程锁用于保护地址数据


def find_free_port(start_port=10000):
    """找到一个可用的端口"""
    # 生成10000-65535之间的随机端口
    port = random.randint(start_port, 65535)
    max_attempts = 100  # 最多尝试100次

    for _ in range(max_attempts):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('localhost', port))
            sock.listen(1)
            sock.close()
            return port
        except OSError:
            port = random.randint(start_port, 65535)
            sock.close()
    return None


def init_app():
    """初始化应用"""
    global data_loader, generator, ssn_manager
    try:
        data_loader = DataLoader("data")
        # 默认不启用SSN验证，可通过API参数控制
        generator = PersonGenerator(data_loader, enable_ssn_validation=False)
        ssn_manager = SSNManager(data_loader)
        return True
    except Exception as e:
        print(f"初始化失败: {e}")
        return False


def get_recent_files(days=7):
    """获取最近N天的备份文件"""
    recent_files = []
    cutoff_date = datetime.now() - timedelta(days=days)

    if not os.path.exists("output"):
        return recent_files

    # 遍历output目录下的所有日期文件夹
    for date_folder in os.listdir("output"):
        folder_path = os.path.join("output", date_folder)
        if not os.path.isdir(folder_path):
            continue

        try:
            # 解析日期文件夹名（yymmdd格式）
            folder_date = datetime.strptime(date_folder, "%y%m%d")
            if folder_date >= cutoff_date:
                # 获取该文件夹下的所有json文件
                json_files = glob.glob(os.path.join(folder_path, "*.json"))
                for json_file in json_files:
                    recent_files.append({
                        "file_path": json_file,
                        "date": folder_date.strftime("%Y-%m-%d"),
                        "filename": os.path.basename(json_file)
                    })
        except ValueError:
            # 忽略无法解析的文件夹名
            continue

    return sorted(recent_files, key=lambda x: x["date"], reverse=True)


def get_basic_info_from_file(file_path):
    """从文件中读取基本信息"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        name = data.get("name", {})
        full_name = f"{name.get('first_name', '')} {name.get('last_name', '')}"

        # 计算年龄
        birthday = data.get("birthday", "")
        age = ""
        if birthday and len(birthday) == 8:
            birth_year = int(birthday[:4])
            current_year = datetime.now().year
            age = current_year - birth_year

        # 处理SSN格式（兼容新旧格式，保留完整的SSN对象）
        ssn_data = data.get("ssn", "")
        if isinstance(ssn_data, dict):
            # 新格式：{"number": "123-45-6789", "verified": true, "status": "..."}
            ssn_info = ssn_data
        else:
            # 旧格式：直接是字符串，构造为对象格式
            ssn_info = {
                "number": ssn_data,
                "verified": False,
                "status": "not_verified",
                "details": None,
                "error": None
            }

        # 处理州信息
        state_code = data.get("state", "")
        state_info = data.get("state_info", {})
        if state_info and isinstance(state_info, dict):
            state_display = f"{state_code} {state_info.get('name', '')} {state_info.get('chinese_name', '')}"
        else:
            state_display = state_code

        return {
            "name": full_name,
            "age": age,
            "address": data.get("address", {}).get("full_address", ""),
            "phone": data.get("phone", ""),
            "ssn": ssn_info,  # 返回完整的SSN对象
            "gender": "男" if data.get("gender") == "male" else "女",
            "state": state_display,
            "note": data.get("note", "")  # 添加备注支持
        }
    except Exception as e:
        print(f"读取文件失败 {file_path}: {e}")
        return None


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/countries')
def get_countries():
    """获取支持的国家列表"""
    try:
        countries = data_loader.get_supported_countries()
        return jsonify({"success": True, "countries": countries})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/states/<country>')
def get_states(country):
    """获取指定国家的州列表"""
    try:
        states = data_loader.get_states_for_country(country)
        return jsonify({"success": True, "states": states})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/generate', methods=['POST'])
def generate_person():
    """生成虚拟公民信息"""
    global generator  # 将global声明移到函数开头

    try:
        data = request.json

        # 检查是否需要启用SSN验证
        enable_ssn_validation = data.get('enable_ssn_validation', False)

        # 如果当前generator的SSN验证设置与请求不符，重新创建generator
        if generator.enable_ssn_validation != enable_ssn_validation:
            generator = PersonGenerator(
                data_loader, enable_ssn_validation=enable_ssn_validation)

        # 生成人员信息
        people = []
        count = data.get('count', 1)

        for i in range(count):
            max_person_attempts = 3  # 每个人最多尝试3次
            person_generated = False
            
            for attempt in range(max_person_attempts):
                try:
                    person_data = generator.generate_person(
                        country=data.get('country'),
                        gender=data.get('gender'),
                        state=data.get('state'),
                        age=data.get('age_range'),
                        education=data.get('education'),
                        parents=data.get('parents', 'none')
                    )
                    people.append(person_data)
                    person_generated = True
                    break
                    
                except Exception as e:
                    print(f"第{i+1}个人生成失败，第{attempt+1}次尝试: {str(e)}")
                    if attempt == max_person_attempts - 1:
                        # 最后一次尝试也失败了
                        if enable_ssn_validation:
                            # 如果启用了SSN验证，返回明确的错误信息
                            error_msg = f"生成第{i+1}个人时失败: {str(e)}"
                            if "经过100次尝试仍无法生成验证通过的SSN" in str(e):
                                error_msg += "\n建议：1) 尝试更换出生年份范围 2) 暂时关闭SSN在线验证"
                            return jsonify({"success": False, "error": error_msg})
                        else:
                            # 如果没有启用SSN验证，这是意外错误
                            return jsonify({"success": False, "error": f"生成第{i+1}个人时发生意外错误: {str(e)}"})
            
            if not person_generated:
                return jsonify({"success": False, "error": f"无法生成第{i+1}个人"})

        # 备份功能
        if data.get('backup', False):
            today = datetime.now().strftime('%y%m%d')
            backup_dir = os.path.join("output", today)
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            for person in people:
                name = person["name"]
                birthday = person["birthday"]
                filename = f"{name['first_name']}{name['last_name']}-{birthday}.json"
                backup_file = os.path.join(backup_dir, filename)

                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(OutputFormatter.format_json(person))

        return jsonify({"success": True, "people": people})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/recent_people')
def get_recent_people():
    """获取最近的人员信息"""
    try:
        recent_files = get_recent_files()
        people_list = []

        for file_info in recent_files:
            basic_info = get_basic_info_from_file(file_info["file_path"])
            if basic_info:
                basic_info["file_path"] = file_info["file_path"]
                basic_info["date"] = file_info["date"]
                people_list.append(basic_info)

        return jsonify({"success": True, "people": people_list})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/person_detail')
def get_person_detail():
    """获取人员详细信息"""
    try:
        file_path = request.args.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return jsonify({"success": False, "error": "文件不存在"})

        with open(file_path, 'r', encoding='utf-8') as f:
            person_data = json.load(f)

        return jsonify({"success": True, "person": person_data})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/format_text', methods=['POST'])
def format_text():
    """将人员数据格式化为text格式"""
    try:
        person_data = request.json
        if not person_data:
            return jsonify({"success": False, "error": "缺少人员数据"})
        
        # 使用OutputFormatter格式化为text
        text_output = OutputFormatter.format_text(person_data)
        return jsonify({"success": True, "text": text_output})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


def process_address(importer, address_line, line_num, address_data, country="US"):
    """处理单个地址的验证和导入
    
    Args:
        importer: AddressImporter实例
        address_line: 要处理的地址行
        line_num: 行号（用于错误报告）
        address_data: 地址数据字典
        country: 国家代码
        
    Returns:
        tuple: (是否成功, 错误消息或None)
    """
    try:
        original_address_line = address_line.strip()
        if not original_address_line:
            return False, None

        # 获取9位邮编
        zip_plus4 = importer.get_zip_plus4_from_full_address(original_address_line)
        if zip_plus4 == "0":
            return False, f"第 {line_num} 行: 无法获取9位邮编或地址无效 - {original_address_line}"

        # 使用原始解析逻辑来提取街道、城市、州
        parsed_original = importer.parse_address(original_address_line)
        if not parsed_original:
            return False, f"第 {line_num} 行: 地址格式不规范 - {original_address_line}"

        street, city, state, _ = parsed_original
        updated_address_line = f"{street}, {city}, {state} {zip_plus4}"

        # 使用线程锁保护共享数据的访问和修改
        with address_lock:
            # 按州分组
            if state not in address_data[country]:
                address_data[country][state] = []

            # 检查是否已存在
            if updated_address_line not in address_data[country][state]:
                address_data[country][state].append(updated_address_line)
                # 立即保存更新后的地址数据
                importer.save_addresses_data(address_data)
                return True, None
            else:
                return False, f"第 {line_num} 行: 地址已存在 - {original_address_line}"

    except Exception as e:
        return False, f"第 {line_num} 行处理失败: {str(e)} - {address_line}"


@app.route('/api/import_data', methods=['POST'])
def import_data_api():
    """处理数据导入请求"""
    try:
        data = request.json
        import_type = data.get('import_type')
        raw_data = data.get('import_data')

        if not import_type or not raw_data:
            return jsonify({"success": False, "error": "缺少导入类型或数据内容"})

        importer = AddressImporter()
        lines = raw_data.strip().split('\n')
        imported_count = 0
        errors = []

        if import_type == 'addresses':
            # 加载现有数据
            address_data = importer.load_addresses_data()
            country = "US"  # 默认为US
            if country not in address_data:
                address_data[country] = {}

            # 使用线程池进行并行处理，最大并行度为5
            with ThreadPoolExecutor(max_workers=5) as executor:
                # 创建future到行号的映射
                future_to_line = {
                    executor.submit(process_address, importer, line.strip(), line_num, address_data): line_num 
                    for line_num, line in enumerate(lines, 1)
                }

                # 处理完成的任务
                for future in as_completed(future_to_line):
                    try:
                        success, error = future.result()
                        if success:
                            imported_count += 1
                        if error:
                            errors.append(error)
                    except Exception as e:
                        errors.append(f"处理任务时发生错误: {str(e)}")

        elif import_type == 'schools':
            school_data = importer.load_schools_data()
            country = "US" # 默认为US
            if country not in school_data:
                school_data[country] = {}

            for line_num, line in enumerate(lines, 1):
                school_info = importer.parse_school_line(line)
                if school_info:
                    parsed_address = importer.parse_address(school_info["address"])
                    if not parsed_address:
                        errors.append(f"第 {line_num} 行: 学校地址解析失败 - {school_info['address']}")
                        continue
                    
                    _, _, state, _ = parsed_address
                    
                    if state not in school_data[country]:
                        school_data[country][state] = {
                            "high_schools": [],
                            "colleges": []
                        }
                    
                    school_type_key = "high_schools" if school_info["type"] == "high_school" else "colleges"
                    
                    # 确保学校类型键存在
                    if school_type_key not in school_data[country][state]:
                         school_data[country][state][school_type_key] = []

                    schools_list = school_data[country][state][school_type_key]
                    
                    school_entry = {
                        "name": school_info["name"],
                        "abbreviation": school_info["abbreviation"],
                        "address": school_info["address"]
                    }
                    
                    existing_names = [s["name"] for s in schools_list]
                    if school_info["name"] not in existing_names:
                        schools_list.append(school_entry)
                        imported_count += 1
                    else:
                        errors.append(f"第 {line_num} 行: 学校已存在 - {school_info['name']}")
                else:
                    errors.append(f"第 {line_num} 行: 解析失败 - {line.strip()}")
            if imported_count > 0:
                 importer.save_schools_data(school_data)
        else:
            return jsonify({"success": False, "error": "无效的导入类型"})

        if imported_count > 0:
            return jsonify({"success": True, "message": f"成功导入 {imported_count} 条记录。", "errors": errors})
        else:
            return jsonify({"success": False, "error": "没有导入任何记录。", "errors": errors})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/verify_ssn', methods=['POST'])
def verify_ssn_api():
    """SSN在线验证API"""
    try:
        data = request.json
        ssn = data.get('ssn')
        state = data.get('state')
        birth_year = data.get('birth_year')
        
        if not ssn:
            return jsonify({"success": False, "error": "缺少SSN参数"})
        
        # 创建SSN验证器
        from src.ssn_validator import SSNValidator
        validator = SSNValidator(timeout=10)
        
        # 执行验证
        validation_result = validator.validate_ssn_with_details(ssn, state, birth_year)
        
        return jsonify({
            "success": True, 
            "validation_result": validation_result
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/update_person_ssn', methods=['POST'])
def update_person_ssn_api():
    """更新保存的人员SSN验证状态"""
    try:
        data = request.json
        file_path = data.get('file_path')
        validation_result = data.get('validation_result')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({"success": False, "error": "文件不存在"})
        
        if not validation_result:
            return jsonify({"success": False, "error": "缺少验证结果"})
        
        # 读取现有数据
        with open(file_path, 'r', encoding='utf-8') as f:
            person_data = json.load(f)
        
        # 更新SSN验证状态
        if isinstance(person_data.get('ssn'), dict):
            person_data['ssn']['verified'] = validation_result.get('validation_passed', False)
            person_data['ssn']['status'] = validation_result.get('validation_status', 'unknown')
            person_data['ssn']['details'] = validation_result
            person_data['ssn']['error'] = validation_result.get('validation_details', {}).get('error')
        else:
            # 兼容旧格式
            ssn_number = person_data.get('ssn', '')
            person_data['ssn'] = {
                'number': ssn_number,
                'verified': validation_result.get('validation_passed', False),
                'status': validation_result.get('validation_status', 'unknown'),
                'details': validation_result,
                'error': validation_result.get('validation_details', {}).get('error')
            }
        
        # 保存更新后的数据
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(person_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({"success": True, "message": "SSN验证状态已更新"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/update_parent_ssn', methods=['POST'])
def update_parent_ssn_api():
    """更新保存的父母SSN验证状态"""
    try:
        data = request.json
        file_path = data.get('file_path')
        parent_type = data.get('parent_type')  # 'father' or 'mother'
        validation_result = data.get('validation_result')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({"success": False, "error": "文件不存在"})
        
        if not parent_type or parent_type not in ['father', 'mother']:
            return jsonify({"success": False, "error": "无效的父母类型"})
        
        if not validation_result:
            return jsonify({"success": False, "error": "缺少验证结果"})
        
        # 读取现有数据
        with open(file_path, 'r', encoding='utf-8') as f:
            person_data = json.load(f)
        
        # 更新父母SSN验证状态
        if 'parents' in person_data and parent_type in person_data['parents']:
            parent = person_data['parents'][parent_type]
            if isinstance(parent.get('ssn'), dict):
                parent['ssn']['verified'] = validation_result.get('validation_passed', False)
                parent['ssn']['status'] = validation_result.get('validation_status', 'unknown')
                parent['ssn']['details'] = validation_result
                parent['ssn']['error'] = validation_result.get('validation_details', {}).get('error')
            else:
                # 兼容旧格式
                ssn_number = parent.get('ssn', '')
                parent['ssn'] = {
                    'number': ssn_number,
                    'verified': validation_result.get('validation_passed', False),
                    'status': validation_result.get('validation_status', 'unknown'),
                    'details': validation_result,
                    'error': validation_result.get('validation_details', {}).get('error')
                }
        
        # 保存更新后的数据
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(person_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({"success": True, "message": f"父母SSN验证状态已更新"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/backup_person', methods=['POST'])
def backup_person_api():
    """备份单个人员信息"""
    try:
        person_data = request.json
        if not person_data:
            return jsonify({"success": False, "error": "缺少人员数据"})
        
        # 生成备份文件
        today = datetime.now().strftime('%y%m%d')
        backup_dir = os.path.join("output", today)
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        name = person_data["name"]
        birthday = person_data["birthday"]
        filename = f"{name['first_name']}{name['last_name']}-{birthday}.json"
        backup_file = os.path.join(backup_dir, filename)

        # 检查文件是否已存在
        if os.path.exists(backup_file):
            return jsonify({"success": False, "error": "该人员信息已经备份过了"})

        # 保存文件
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(OutputFormatter.format_json(person_data))

        return jsonify({"success": True, "message": f"备份成功: {filename}"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/delete_person', methods=['POST'])
def delete_person_api():
    """删除历史记录文件"""
    try:
        data = request.json
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({"success": False, "error": "缺少文件路径"})
        
        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": "文件不存在"})
        
        # 删除文件
        os.remove(file_path)
        
        return jsonify({"success": True, "message": "文件已删除"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/update_person_note', methods=['POST'])
def update_person_note_api():
    """更新人员备注"""
    try:
        data = request.json
        file_path = data.get('file_path')
        note = data.get('note', '')
        
        if not file_path:
            return jsonify({"success": False, "error": "缺少文件路径"})
        
        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": "文件不存在"})
        
        # 读取现有数据
        with open(file_path, 'r', encoding='utf-8') as f:
            person_data = json.load(f)
        
        # 更新备注
        person_data['note'] = note
        
        # 保存更新后的数据
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(person_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({"success": True, "message": "备注已更新"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/replace_ssn_random', methods=['POST'])
def replace_ssn_random_api():
    """随机替换SSN（本地生成，不验证）"""
    try:
        data = request.json
        file_path = data.get('file_path')
        target_path = data.get('target_path', 'ssn')
        
        if not file_path:
            return jsonify({"success": False, "error": "缺少文件路径"})
        
        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": "文件不存在"})
        
        # 读取现有数据
        with open(file_path, 'r', encoding='utf-8') as f:
            person_data = json.load(f)
        
        # 使用SSN管理器替换SSN
        updated_data = ssn_manager.replace_ssn_random(person_data, target_path)
        
        # 保存更新后的数据
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            "success": True, 
            "message": "SSN已随机替换",
            "new_ssn": updated_data.get("ssn", {}).get("number") if target_path == "ssn" else "已更新"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/replace_ssn_validated', methods=['POST'])
def replace_ssn_validated_api():
    """在线验证替换SSN"""
    try:
        data = request.json
        file_path = data.get('file_path')
        target_path = data.get('target_path', 'ssn')
        
        if not file_path:
            return jsonify({"success": False, "error": "缺少文件路径"})
        
        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": "文件不存在"})
        
        # 读取现有数据
        with open(file_path, 'r', encoding='utf-8') as f:
            person_data = json.load(f)
        
        # 使用SSN管理器进行在线验证替换
        updated_data, success = ssn_manager.replace_ssn_with_validation(person_data, target_path)
        
        if success:
            # 保存更新后的数据
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(updated_data, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                "success": True, 
                "message": "SSN已在线验证并替换",
                "new_ssn": updated_data.get("ssn", {}).get("number") if target_path == "ssn" else "已更新"
            })
        else:
            return jsonify({
                "success": False, 
                "error": "无法生成通过验证的SSN，请稍后重试"
            })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == '__main__':
    if init_app():
        print("启动 Web UI 服务器...")
        port = find_free_port()
        if port:
            url = f"http://localhost:{port}"
            print(f"访问地址: {url}")

            # 先打开浏览器
            webbrowser.open(url)

            # 然后启动服务器
            app.run(debug=True, host='0.0.0.0', port=port, use_reloader=False)
        else:
            print("无法找到可用的端口，无法启动服务器")
    else:
        print("初始化失败，无法启动服务器")
