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
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_loader import DataLoader
from generators import PersonGenerator
from formatters import OutputFormatter

app = Flask(__name__)

# 全局变量
data_loader = None
generator = None


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
    global data_loader, generator
    try:
        data_loader = DataLoader("data")
        # 默认不启用SSN验证，可通过API参数控制
        generator = PersonGenerator(data_loader, enable_ssn_validation=False)
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

        # 处理SSN格式（兼容新旧格式）
        ssn_data = data.get("ssn", "")
        if isinstance(ssn_data, dict):
            # 新格式：{"number": "123-45-6789", "verified": true}
            ssn = ssn_data.get("number", "")
        else:
            # 旧格式：直接是字符串
            ssn = ssn_data

        return {
            "name": full_name,
            "age": age,
            "address": data.get("address", {}).get("full_address", ""),
            "phone": data.get("phone", ""),
            "ssn": ssn,
            "gender": "男" if data.get("gender") == "male" else "女"
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
            person_data = generator.generate_person(
                country=data.get('country'),
                gender=data.get('gender'),
                state=data.get('state'),
                age=data.get('age_range'),
                education=data.get('education'),
                parents=data.get('parents', 'none')
            )
            people.append(person_data)

        # 备份功能
        if data.get('backup', False):
            today = datetime.now().strftime('%y%m%d')
            backup_dir = os.path.join("output", today)
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            for person in people:
                name = person["name"]
                birthday = person["birthday"]
                filename = f"{name['last_name']}{name['first_name']}-{birthday}.json"
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
