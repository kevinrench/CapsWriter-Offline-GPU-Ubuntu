# coding: utf-8


'''
这个文件仅仅是为了 PyInstaller 打包用
'''

import os
import sys
from pathlib import Path

# 自动添加 NVIDIA 库路径到 LD_LIBRARY_PATH
# 解决 Linux 下 pip 安装的 nvidia-* 包找不到库文件的问题
def setup_nvidia_paths():
    if sys.platform != 'linux':
        return
    
    site_packages = Path(sys.prefix) / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
    nvidia_path = site_packages / 'nvidia'
    
    if not nvidia_path.exists():
        return

    # 需要添加的子目录
    libs = [
        nvidia_path / 'cudnn' / 'lib',
        nvidia_path / 'cublas' / 'lib',
        nvidia_path / 'cuda_runtime' / 'lib',
    ]
    
    current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
    new_paths = []
    
    for lib_dir in libs:
        if lib_dir.exists() and str(lib_dir) not in current_ld_path:
            new_paths.append(str(lib_dir))
            
    if new_paths:
        # 将新路径添加到最前面
        os.environ['LD_LIBRARY_PATH'] = ':'.join(new_paths) + ':' + current_ld_path
        # 重新执行自身以生效环境变量（仅在第一次设置时）
        # 注意：简单设置 os.environ 对已加载的动态库可能无效，但在 Python 中
        # 对于 ctypes 或子进程加载是有用的。onnxruntime 往往是在 import 时动态加载。
        # 为了保险，我们可以在 import 其他重型库之前尽早执行此操作。

setup_nvidia_paths()

from multiprocessing import freeze_support
from util.server_cosmic import console

import core_server


if __name__ == '__main__':
    freeze_support()
    core_server.init()