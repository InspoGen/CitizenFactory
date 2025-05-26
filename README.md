# 🏛️ Virtual Citizen Generator | 虚拟公民信息生成器

<div align="center">

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Code Style](https://img.shields.io/badge/code%20style-PEP8-orange)
![Status](https://img.shields.io/badge/status-Production%20Ready-brightgreen)

**一个专业的虚拟美国公民信息生成器，支持真实数据源和在线SSN验证**

[English](#english) | [中文](#中文)

</div>

---

## 🎯 项目概述

Virtual Citizen Generator是一个高度可配置的虚拟美国公民信息生成工具，专为开发者、测试工程师和数据分析师设计。它能够生成高度真实的虚拟个人信息，包括基本信息、联系方式、教育背景、家庭关系等，并支持SSN在线验证功能。

### ✨ 核心特性

- **🎲 真实数据生成**: 基于真实地址、学校、电话区号等数据源
- **🔐 SSN验证**: 可选的社会保障号在线验证功能
- **📊 多格式输出**: 支持JSON、CSV、YAML、TEXT四种输出格式
- **🌐 Web界面**: 现代化的Web UI，支持实时生成和历史管理
- **⚙️ 高度可配置**: 支持命令行参数和配置文件
- **👨‍👩‍👧‍👦 家庭关系**: 支持生成父母信息，保持家庭逻辑一致性
- **🏫 教育背景**: 基于真实学校数据的高中和大学信息
- **📍 地理一致性**: 确保地址、电话区号、学校等地理信息一致
- **🔄 批量处理**: 支持批量生成和数据导入功能

## 🚀 快速开始

### 📋 系统要求

- Python 3.8 或更高版本
- 2GB+ 可用内存
- 支持的操作系统：Windows、macOS、Linux

### 💻 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/virtual-citizen-generator.git
cd virtual-citizen-generator

# 安装依赖
pip install -r requirements.txt

# 验证安装
python main.py --list-countries
```

### 🎮 基本使用

#### 命令行界面

```bash
# 生成单个虚拟公民
python main.py --country US --state CA --gender male --age 25-30

# 批量生成包含父母信息的数据
python main.py --country US --state NY --count 5 --parents both --backup

# 启用SSN验证的完整示例
python main.py --country US --state TX --education college --enable-ssn-validation --format json
```

#### Web界面

```bash
# 启动Web UI
python webui.py

# 浏览器访问 http://localhost:随机端口
```

## 📚 详细功能

### 🏗️ 数据结构

生成的虚拟公民信息包含以下完整结构：

```json
{
  "name": {
    "first_name": "Austin",
    "last_name": "Brewer"
  },
  "gender": "male",
  "birthday": "19961011",
  "country": "US",
  "state": "CA",
  "address": {
    "street": "8901 Market St",
    "city": "San Francisco", 
    "state": "CA",
    "zip_code": "94103-8901",
    "full_address": "8901 Market St, San Francisco, CA 94103-8901"
  },
  "phone": "(714) 697-8192",
  "email": "austinbrewer@cox.net",
  "ssn": {
    "number": "548-45-4219",
    "verified": false
  },
  "education": {
    "education_level": "college",
    "high_school": {
      "name": "Arcadia High School",
      "abbreviation": "AHS",
      "address": "180 Campus Dr, Arcadia, CA 91007-6917",
      "start_date": "201009",
      "graduation_date": "201406"
    },
    "college": {
      "name": "University of California, Merced",
      "abbreviation": "UCM", 
      "address": "5200 Lake Rd, Merced, CA 95343-5603",
      "start_date": "201409",
      "graduation_date": "201806"
    }
  },
  "parents": {
    "father": { /* 完整的父亲信息 */ },
    "mother": { /* 完整的母亲信息 */ }
  },
  "state_info": {
    "name": "California",
    "chinese_name": "加利福尼亚州"
  }
}
```

### 🎛️ 命令行参数

| 参数 | 类型 | 描述 | 示例 |
|------|------|------|------|
| `--country` | string | 国家代码 | `US` |
| `--state` | string | 州代码 | `CA`, `NY`, `TX` |
| `--gender` | choice | 性别 | `male`, `female` |
| `--age` | string | 年龄范围 | `18-25`, `30-40` |
| `--education` | choice | 教育水平 | `none`, `high_school`, `college` |
| `--parents` | choice | 父母信息 | `none`, `father`, `mother`, `both` |
| `--format` | choice | 输出格式 | `json`, `text`, `yaml`, `csv` |
| `--count` | integer | 生成数量 | `1-100` |
| `--backup` | flag | 备份到文件 | - |
| `--enable-ssn-validation` | flag | 启用SSN验证 | - |

### 🌍 支持的地区

当前支持美国以下州：

| 州代码 | 州名 | 中文名 | 数据完整性 |
|--------|------|--------|-----------|
| `CA` | California | 加利福尼亚州 | ✅ 完整 |
| `NY` | New York | 纽约州 | ✅ 完整 |
| `TX` | Texas | 德克萨斯州 | ✅ 完整 |
| `FL` | Florida | 佛罗里达州 | ✅ 完整 |
| `IL` | Illinois | 伊利诺伊州 | ✅ 完整 |
| `NV` | Nevada | 内华达州 | ✅ 完整 |

## 🛠️ 高级配置

### 📝 配置文件

创建 `config/custom.json`：

```json
{
  "country": "US",
  "state": "CA",
  "age_range": "25-35",
  "education": "college",
  "parents": "both",
  "output_format": "json",
  "count": 10,
  "backup": true,
  "enable_ssn_validation": true,
  "data_dir": "data"
}
```

使用配置文件：
```bash
python main.py --config config/custom.json
```

### 📊 批量数据导入

#### 导入住宅地址

```bash
# 创建地址文件 import-data/addresses.txt
echo "1234 Lexington Ave, New York, NY 10022-1234" > import-data/addresses.txt
echo "5678 Main St, Buffalo, NY 14203-5678" >> import-data/addresses.txt

# 导入地址数据
python tools/import_addresses.py --type addresses --file import-data/addresses.txt
```

#### 导入学校信息

```bash
# 创建学校文件 import-data/schools.txt
echo "Harvard University|Harvard|college|Cambridge, MA 02138-3800" > import-data/schools.txt

# 导入学校数据  
python tools/import_addresses.py --type schools --file import-data/schools.txt
```

## 🏛️ 项目架构

```
virtual-citizen-generator/
├── 🎯 main.py                    # 主程序入口
├── 🌐 webui.py                   # Web界面服务器
├── ⚙️ config/                    # 配置文件目录
├── 📦 src/                       # 核心源码
│   ├── 📊 data_loader.py         # 数据加载器
│   ├── 🎲 generators.py          # 信息生成器
│   ├── 📋 formatters.py          # 输出格式化器
│   ├── 🔐 ssn_validator.py       # SSN验证器
│   └── 📈 high_group_loader.py   # 高组清单加载器
├── 📁 data/                      # 原始数据文件
│   ├── 📍 addresses/             # 地址数据
│   ├── 🏫 schools/               # 学校数据
│   ├── 👤 names/                 # 姓名数据
│   ├── 📞 phones/                # 电话区号数据
│   └── 🆔 ssn/                   # SSN区域数据
├── 🛠️ tools/                     # 工具脚本
├── 🎨 templates/                 # Web界面模板
├── 📤 output/                    # 输出文件目录
└── 📋 High Group/                # SSN高组清单历史数据
```

## 🔒 安全与隐私

### ⚠️ 重要声明

- **仅用于开发测试**: 本工具生成的所有信息均为虚拟数据，仅供软件开发、测试和教育用途
- **禁止非法使用**: 严禁将生成的信息用于身份盗用、欺诈或其他非法活动
- **数据保护**: 所有生成的数据在本地存储，不会上传到任何服务器
- **SSN验证**: SSN验证功能使用公开的验证服务，不存储个人信息

### 🛡️ 隐私保护

- 输出文件默认被`.gitignore`保护，不会被提交到版本控制
- 支持一次性生成模式，不保存任何文件
- Web界面支持清除历史记录功能

## 🤝 贡献指南

我们欢迎社区贡献！请遵循以下步骤：

1. **Fork** 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 **Pull Request**

### 📝 代码规范

- 遵循 PEP8 编码规范
- 添加适当的注释和文档字符串
- 确保所有测试通过
- 保持代码覆盖率 > 80%

## 📄 许可证

本项目采用 MIT 许可证 - 详情请查看 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- 感谢提供真实地址数据的公开数据源
- 感谢 Flask 框架提供优秀的Web开发体验
- 感谢所有贡献者和测试用户的支持

## 📞 支持与反馈

- 🐛 **Bug报告**: [Issues](https://github.com/yourusername/virtual-citizen-generator/issues)
- 💡 **功能建议**: [Feature Requests](https://github.com/yourusername/virtual-citizen-generator/discussions)
- 📧 **联系我们**: [your-email@example.com](mailto:your-email@example.com)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给它一个Star！⭐**

Made with ❤️ by the Virtual Citizen Generator Team

</div> 