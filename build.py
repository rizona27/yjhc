# build.py
import PyInstaller.__main__
import os

# 定义UPX路径（请修改成你自己的路径）
upx_path = r'E:\yjhc\upx-5.0.2-win64'

# 定义参数
args = [
    'app.py',  # 主入口文件
    '--name=PerformanceBacktestTool',  # 可执行文件名称
    '--windowed',  # 不显示控制台窗口
    '--add-data=app.ico;.',  # 添加图标文件到打包，注意，现在它会放在输出文件夹的根目录
    '--hidden-import=pandas._libs.tslibs.timedeltas',
    '--hidden-import=pandas._libs.tslibs.nattype',
    '--hidden-import=pandas._libs.tslibs.base',
    '--hidden-import=matplotlib.backends.backend_tkagg',
    '--hidden-import=openpyxl',
    '--hidden-import=xlrd',
    '--hidden-import=chardet',
    '--hidden-import=psutil',
    '--hidden-import=python_dateutil',
    '--hidden-import=Crypto.Cipher._mode_cbc',
    '--hidden-import=Crypto.Util._strxor',
    '--clean',  # 清理临时文件
    f'--upx-dir={upx_path}'  # 使用 f-string 格式化路径，或使用 + 连接
]

# 检查app.ico是否存在，并添加图标参数
icon_path = 'app.ico'
if os.path.exists(icon_path):
    args.insert(2, f'--icon={icon_path}')

# 执行打包
PyInstaller.__main__.run(args)