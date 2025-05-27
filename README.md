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

Virtual Citizen Generator是一个高度可配置的虚拟美国公民信息生成工具，专为开发者、测试工程师和数据分析师设计。它能够生成高度真实的虚拟个人信息，包括基本信息、联系方式、教育背景、家庭关系等，并支持强大的SSN在线验证和智能替换功能。

### ✨ 核心特性

- **🎲 真实数据生成**: 基于真实地址、学校、电话区号等数据源
- **🔐 智能SSN验证**: 支持本人和父母SSN的在线验证，实时状态反馈
- **🔄 SSN智能替换**: 随机替换和验证替换两种模式，确保数据有效性
- **📊 多格式输出**: 支持JSON、CSV、YAML、TEXT四种输出格式
- **🌐 现代Web界面**: 响应式Web UI，支持实时生成、验证、历史管理和数据操作
- **⚙️ 高度可配置**: 支持命令行参数和配置文件
- **👨‍👩‍👧‍👦 完整家庭关系**: 支持生成父母信息，保持家庭逻辑一致性
- **🏫 真实教育背景**: 基于真实学校数据的高中和大学信息
- **📍 地理一致性**: 确保地址、电话区号、学校等地理信息一致
- **🔄 批量处理**: 支持批量生成和数据导入功能
- **💾 备注管理**: 支持为每个虚拟公民添加备注信息
- **✅ 验证状态追踪**: 智能验证图标，清晰显示所有SSN验证状态

### 🆕 最新功能亮点

- **实时SSN验证**: 支持在Web界面中实时验证本人和父母SSN
- **智能替换系统**: 提供随机替换和验证替换两种SSN更新模式
- **验证状态可视化**: 通过颜色图标直观显示验证状态（✓ 通过、⚠ 超时、✗ 失败等）
- **历史记录管理**: 完整的历史记录查看、编辑和删除功能
- **数据同步**: 模态框与卡片数据实时同步更新
- **智能验证图标**: 只有当所有SSN都验证通过时才显示完全验证标识

## 🚀 快速开始

### 📋 系统要求

- Python 3.8 或更高版本
- 2GB+ 可用内存
- 支持的操作系统：Windows、macOS、Linux
- 网络连接（用于SSN在线验证功能）

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

#### Web界面（推荐）

```bash
# 启动Web UI
python webui.py

# 浏览器访问显示的地址（如：http://localhost:45678）
```

**Web界面功能：**
- 📝 **生成信息**: 实时生成虚拟公民信息，支持SSN验证
- 📋 **历史记录**: 查看、编辑和管理已生成的记录
- 📥 **数据导入**: 批量导入地址和学校数据
- 🔍 **SSN验证**: 点击验证按钮实时验证SSN有效性
- 🔄 **SSN替换**: 随机替换或验证替换无效的SSN
- 📝 **备注功能**: 为每个记录添加和编辑备注
- 📋 **数据复制**: 支持JSON和文本格式的一键复制

#### 命令行界面

```bash
# 生成单个虚拟公民
python main.py --country US --state CA --gender male --age 25-30

# 批量生成包含父母信息的数据
python main.py --country US --state NY --count 5 --parents both --backup

# 启用SSN验证的完整示例
python main.py --country US --state TX --education college --enable-ssn-validation --format json
```

## 📚 详细功能

### 🔐 SSN验证系统

#### 验证状态说明

| 状态 | 图标 | 描述 | 操作建议 |
|------|------|------|----------|
| ✅ `verified_valid` | ✓ | 在线验证通过 | 无需操作 |
| ✅ `parse_error_valid` | ✓ | 有效但详细信息不可用 | 无需操作 |
| ⚠️ `timeout` | ⏱ | 验证超时 | 可重新验证 |
| ❌ `verified_invalid` | ✗ | 验证确认无效 | 建议替换 |
| ❌ `network_error` | ⚠ | 网络错误 | 检查网络后重试 |
| 🚫 `blocked` | 🚫 | 验证被阻止 | 建议替换 |
| ❓ `verification_failed` | ? | 验证失败 | 建议替换 |
| ⚪ `not_verified` | - | 未验证 | 可以验证 |

#### SSN替换功能

- **随机替换**: 快速生成新的随机SSN（无验证）
- **验证替换**: 生成经过在线验证的有效SSN（推荐，但较慢）

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
    "verified": true,
    "status": "verified_valid",
    "details": {
      // 验证详细信息
    },
    "error": null
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
    "father": {
      "name": {
        "first_name": "Robert",
        "last_name": "Brewer"
      },
      "birthday": "19671203",
      "phone": "(714) 555-0123",
      "email": "robertbrewer@cox.net",
      "address": {
        "full_address": "8901 Market St, San Francisco, CA 94103-8901"
      },
      "ssn": {
        "number": "548-12-3456",
        "verified": true,
        "status": "verified_valid"
      }
    },
    "mother": {
      // 类似的母亲信息结构
    }
  },
  "state_info": {
    "name": "California",
    "chinese_name": "加利福尼亚州"
  },
  "note": "这是一个备注示例"
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
| `PA` | Pennsylvania | 宾夕法尼亚州 | ✅ 完整 |
| `OH` | Ohio | 俄亥俄州 | ✅ 完整 |
| `GA` | Georgia | 乔治亚州 | ✅ 完整 |
| `NC` | North Carolina | 北卡罗来纳州 | ✅ 完整 |

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

#### Web界面导入（推荐）

1. 访问Web界面的"导入数据"标签页
2. 选择导入类型（住宅地址或学校信息）
3. 在文本框中粘贴数据，每行一条记录
4. 点击"开始导入"按钮

**住宅地址格式：**
```
123 Main St, Anytown, CA 90210
456 Oak Ave, Another City, NY 10001-1234
```

**学校信息格式：**
```
Central High School|CHS|high_school|456 Oak Ave, Anytown, CA 90210
State University|SU|college|789 College Blvd, University City, CA 90220
```

#### 命令行导入

```bash
# 导入住宅地址
python tools/import_data.py --type addresses --file import-data/addresses.txt

# 导入学校信息
python tools/import_data.py --type schools --file import-data/schools.txt
```

## 🎨 Web界面指南

### 📋 主要功能页面

#### 1. 生成信息页面
- **配置参数**: 选择国家、州、性别、年龄范围等
- **实时生成**: 点击生成按钮即可创建虚拟公民
- **SSN验证**: 生成后可点击"验证SSN"按钮进行在线验证
- **SSN替换**: 对验证失败的SSN提供替换选项
- **即时操作**: 复制、备份、删除、添加备注

#### 2. 历史记录页面
- **记录浏览**: 查看最近7天的生成记录
- **详情查看**: 点击卡片查看完整信息
- **数据管理**: 编辑备注、删除记录
- **验证状态**: 清晰显示每个SSN的验证状态

#### 3. 数据导入页面
- **批量导入**: 支持地址和学校数据的批量导入
- **实时反馈**: 显示导入进度和错误信息
- **格式指导**: 内置格式说明和示例

### 🎯 最佳实践

#### SSN验证建议
1. **首次生成**: 建议启用"启用SSN在线验证"选项
2. **批量验证**: 对历史数据可以逐个点击验证
3. **替换策略**: 
   - 验证失败的SSN建议使用"验证更换SSN"
   - 临时使用可选择"随机更换SSN"

#### 性能优化
1. **批量生成**: 单次生成建议不超过50个记录
2. **网络设置**: SSN验证需要稳定的网络连接
3. **数据备份**: 重要数据及时备份到文件

## 🔧 故障排除

### 常见问题

#### SSN验证问题
- **验证超时**: 检查网络连接，稍后重试
- **验证被阻止**: 可能触发了频率限制，建议稍后再试
- **网络错误**: 检查防火墙和代理设置

#### Web界面问题
- **页面无法访问**: 确认端口没有被占用
- **数据不更新**: 尝试刷新浏览器页面
- **功能异常**: 查看浏览器开发者工具的控制台错误

#### 数据导入问题
- **格式错误**: 确认数据格式符合要求
- **重复数据**: 系统会自动跳过重复项
- **权限问题**: 确认对data目录有写入权限

### 性能调优

```bash
# 查看系统状态
python tools/system_check.py

# 清理临时文件
python tools/cleanup.py

# 数据库优化
python tools/optimize_data.py
```

## 📈 版本历史

### v2.1.0 (当前版本)
- ✅ 新增SSN实时验证功能
- ✅ 新增SSN智能替换系统
- ✅ 优化Web界面交互体验
- ✅ 新增验证状态可视化
- ✅ 新增备注管理功能
- ✅ 修复历史记录验证状态显示问题
- ✅ 优化数据同步机制

### v2.0.0
- ✅ 全新Web界面设计
- ✅ 新增历史记录管理
- ✅ 新增数据导入功能
- ✅ 优化数据结构
- ✅ 新增多种输出格式

### v1.0.0
- ✅ 基础命令行功能
- ✅ 真实数据源集成
- ✅ 基础SSN验证功能

## 🤝 贡献指南

欢迎贡献代码！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

### 开发环境设置

```bash
# 克隆开发分支
git clone -b develop https://github.com/yourusername/virtual-citizen-generator.git

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
python -m pytest tests/

# 代码格式检查
flake8 src/
black src/
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## ⚠️ 免责声明

此工具仅用于合法的开发、测试和教育目的。生成的信息均为虚构内容，请勿用于任何非法活动。使用者应遵守当地法律法规。

## 📞 联系方式

- 📧 Email: your-email@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/virtual-citizen-generator/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/virtual-citizen-generator/discussions)

---

<div align="center">

**如果这个项目对你有帮助，请给它一个 ⭐️！**

Made with ❤️ by [Your Name]

</div>

---

## English

# 🏛️ Virtual Citizen Generator

A professional virtual US citizen information generator with real data sources and online SSN verification.

### 🌟 Key Features

- **🎲 Realistic Data Generation**: Based on real addresses, schools, phone area codes, and other data sources
- **🔐 Smart SSN Verification**: Real-time online SSN verification for individuals and parents
- **🔄 Intelligent SSN Replacement**: Random and verified replacement modes
- **🌐 Modern Web Interface**: Responsive web UI with real-time generation, verification, and history management
- **📊 Multiple Output Formats**: JSON, CSV, YAML, and TEXT formats supported
- **👨‍👩‍👧‍👦 Complete Family Relations**: Generate parent information with family logic consistency
- **🏫 Authentic Education Background**: Based on real school data
- **📍 Geographic Consistency**: Ensures address, phone area code, and school geographic consistency

### 🚀 Quick Start

```bash
# Clone and install
git clone https://github.com/yourusername/virtual-citizen-generator.git
cd virtual-citizen-generator
pip install -r requirements.txt

# Start Web UI
python webui.py

# Or use command line
python main.py --country US --state CA --gender male --age 25-30
```

### 📚 Documentation

For detailed English documentation, API reference, and examples, please visit our [Wiki](https://github.com/yourusername/virtual-citizen-generator/wiki).

---

⚖️ **Legal Notice**: This tool is for legitimate development, testing, and educational purposes only. All generated information is fictional. Users must comply with local laws and regulations. 