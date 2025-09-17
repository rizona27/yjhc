# 业绩表现回测工具

这是一个基于 Python 和 Tkinter 的桌面应用程序，旨在帮助用户对历史业绩数据进行可视化分析和回测。该工具支持多种文件格式（CSV 和 Excel），并提供图表展示、数据分析以及用户友好的设置选项。

## 1\. 主要功能

  * **数据导入**：支持导入 `.csv` 和 `.xlsx` 格式的业绩数据文件。
  * **可视化分析**：绘制单位净值趋势图，直观展示业绩走势。
  * **性能回测**：允许自定义时间区间进行回测，计算年化收益和最大回撤。
  * **交互式图表**：支持鼠标悬停显示具体日期和净值数据。
  * **灵活设置**：可自定义图表导出、日志显示和提示框位置等。
  * **激活管理**：包含简单的激活机制，支持临时激活码和永久激活。

## 2\. 软件架构

该项目采用模块化设计，每个文件负责不同的核心功能，确保代码的清晰和可维护性。

  * `app.py`：主程序入口，负责构建 Tkinter 窗口和用户界面。
  * `core.py`：核心业务逻辑模块，处理数据清洗、性能计算和图表数据准备。
  * `utils.py`：通用工具函数库，包含文件读写、日期处理、日志记录等。
  * `gui_components.py`：负责创建各种 UI 组件，如菜单栏、主界面和日志窗口。
  * `event_handlers.py`：处理用户事件和输入验证，如日期输入框的焦点和回车事件。
  * `chart_utils.py`：图表工具模块，负责 Matplotlib 图表的创建和交互功能。
  * `config.py`：配置管理，存储应用程序的颜色主题和用户设置。
  * `tooltip.py`：自定义的工具提示组件，用于在鼠标悬停时显示信息。
  * `window_utils.py`：窗口辅助工具，用于居中窗口和创建激活窗口等。
  * `activation.py`：激活管理器，负责处理程序的加密、解密和授权。

## 3\. 安装和运行

### 3.1 依赖环境

本项目依赖以下 Python 库：

  * `pandas`
  * `matplotlib`
  * `pycryptodome`
  * `openpyxl`
  * `xlrd`
  * `python-dateutil`
  * `psutil`
  * `chardet`
  * `tkinter` (Python 内置库，通常无需单独安装)

### 3.2 安装步骤

1.  克隆本仓库到本地：

    ```bash
    git clone [你的仓库URL]
    cd [你的项目文件夹]
    ```

2.  （推荐）创建并激活一个虚拟环境：

    ```bash
    # 创建虚拟环境
    python -m venv venv
    # 激活虚拟环境 (Windows)
    .\venv\Scripts\activate
    # 激活虚拟环境 (macOS/Linux)
    source venv/bin/activate
    ```

3.  安装所有依赖库：

    ```bash
    pip install pandas matplotlib pycryptodome openpyxl xlrd python-dateutil psutil chardet
    ```

4.  运行程序：

    ```bash
    python app.py
    ```

## 4\. 可执行文件打包（Windows）

如果你希望将程序打包成一个独立的 Windows 桌面应用，可以使用 PyInstaller。

1.  确保你已安装所有依赖，并在虚拟环境中额外安装 PyInstaller：

    ```bash
    pip install pyinstaller
    ```

2.  使用 PyInstaller 生成一个 `.spec` 文件，并根据你的项目进行修改。一个示例 `.spec` 文件已在项目中提供。

3.  运行打包命令：

    ```bash
    pyinstaller --noconfirm --name "业绩表现回测工具" --onedir --windowed --icon "app.ico" app.py
    ```

    或者使用你定制的 `.spec` 文件：

    ```bash
    pyinstaller "业绩表现回测工具.spec"
    ```

4.  打包完成后，你会在 `dist` 文件夹中找到一个名为 `业绩表现回测工具` 的文件夹，其中包含了可执行文件和其他所有依赖。

## 5\. 许可协议

本项目基于 MIT 许可证开源。请参阅 `LICENSE` 文件了解更多信息。
