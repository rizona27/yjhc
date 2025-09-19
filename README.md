# 业绩表现回测工具 (Performance Backtest Tool)

一个基于Python开发的桌面应用程序，用于金融产品业绩数据的回测分析与可视化。支持多种数据格式导入，提供专业的业绩指标计算和图表展示功能。

![Python](https://img.shields.io/badge/Python-3.7%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

## 功能特点

### 📊 数据导入与处理
- 支持CSV、Excel（xls/xlsx）多种数据格式
- 自动识别日期和净值列（支持多种列名格式）
- 智能日期格式解析（YYYY-MM-DD, YYYY/MM/DD, YYYYMMDD）
- 自动数据清洗和排序

### 📈 业绩分析功能
- **固定周期回测**：近1周、2周、3周、1月、2月、3月、6月、1年及成立以来
- **自定义区间分析**：任意时间段的业绩回测
- **专业指标计算**：年化收益率、最大回撤
- **数据验证**：自动检查数据有效性和日期范围

### 🎨 数据可视化
- 净值趋势图展示
- 自动标记最高点和最低点
- 鼠标悬停显示详细数据
- 可配置的提示框位置和透明度
- 图表导出功能（PNG格式，300DPI）

### ⚙️ 个性化设置
- 可配置导出目录
- 悬停数据显示设置
- 提示框位置自定义
- 日志窗口显示控制

### 🔒 授权管理
- 设备绑定激活系统
- 临时激活（7天试用）
- 永久激活
- 激活状态实时显示

## 安装说明

### 前提条件
- Windows操作系统
- Python 3.7或更高版本

### 从源码安装
1. 克隆或下载本项目
2. 安装依赖包：
   ```
   pip install -r requirements.txt
   ```
3. 运行主程序：
   ```
   python app.py
   ```

### 使用预编译版本
1. 下载最新的发布版本（.exe文件）
2. 直接运行可执行文件，无需安装Python

## 使用方法

### 基本操作流程
1. **导入数据**：通过"文件"菜单导入CSV或Excel格式的净值数据
2. **查看分析结果**：
   - 固定周期回测结果自动显示在右侧表格中
   - 自定义区间分析需要输入开始和结束日期后点击"分析"按钮
3. **交互式图表**：
   - 鼠标悬停显示具体日期和净值
   - 图表上方显示最高点和最低点信息
4. **导出结果**：可将图表导出为高清PNG图像

### 数据文件格式要求
- 至少包含两列：日期和单位净值
- 日期列支持多种列名：日期、净值日期、Date、date、交易日期等
- 净值列支持多种列名：单位净值、净值、累计净值、NAV等

### 激活说明
- 未激活状态下可使用基本功能
- 临时激活码：0315（7天试用期）
- 永久激活需使用设备特定的激活码
- 在"关于→工具激活"中输入激活码

## 项目结构

```
PerformanceBacktestTool/
├── app.py                 # 主应用程序
├── activation.py          # 激活管理模块
├── analysis_operations.py # 分析操作模块
├── chart_utils.py         # 图表工具模块
├── config.py              # 配置管理模块
├── core.py                # 核心分析逻辑
├── event_handlers.py      # 事件处理模块
├── file_operations.py     # 文件操作模块
├── gui_components.py      # GUI组件模块
├── utils.py               # 工具函数模块
├── window_utils.py        # 窗口工具模块
├── tooltip.py             # 工具提示模块
├── build.py               # 构建脚本
├── reconfig.py            # 配置重置工具
├── requirements.txt       # 依赖包列表
└── app.ico                # 应用程序图标
```

## 开发说明

### 从源码构建
```bash
# 安装依赖
pip install -r requirements.txt

# 打包为可执行文件
python build.py
```

### 配置重置
如果遇到配置问题，可以运行：
```bash
python reconfig.py
```
这将重置所有用户配置到默认状态。

## 常见问题

### Q: 导入数据时提示"未找到有效的日期列"
A: 请检查数据文件是否包含日期信息，并确保日期列名包含"日期"、"date"等相关关键词

### Q: 图表显示不正常
A: 尝试重置应用程序或检查数据日期格式是否正确

### Q: 激活码无效
A: 请确认输入的激活码格式正确（16位字符，分为4组，如XXXX-XXXX-XXXX-XXXX）

## 许可证

本项目采用 MIT 许可证 - 详见LICENSE文件

## 更新日志

### v1.2.0
- 初始版本发布
- 基本业绩分析功能
- 图表可视化
- 激活系统