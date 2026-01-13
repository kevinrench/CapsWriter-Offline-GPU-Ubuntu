# CapsWriter-Offline Linux NVIDIA GPU 加速指南

本文档记录了在 Linux 环境下（以 Ubuntu/Debian 为例）为 CapsWriter-Offline 开启 NVIDIA GPU 加速的完整步骤。

## 1. 环境准备

- **硬件**: NVIDIA 显卡 (支持 CUDA 12.x，例如 RTX 30系列及以上)
- **驱动**: 确保已安装 NVIDIA 显卡驱动 (`nvidia-smi` 可正常输出)
- **Python 环境**: Conda 环境 (Python 3.10 - 3.12)

## 2. 依赖库替换与安装

ASR 核心库 `sherpa-onnx` 和推理引擎 `onnxruntime` 默认安装的是 CPU 版本。需要替换为 GPU 版本，并补充 NVIDIA 运行时库。

### 2.1 卸载 CPU 版本
```bash
pip uninstall -y onnxruntime sherpa-onnx
```

### 2.2 安装 GPU 版本
**安装 onnxruntime-gpu:**
```bash
pip install onnxruntime-gpu
```

**安装 sherpa-onnx (CUDA 适配版):**
请根据你的 CUDA 版本选择合适的安装命令。以下以 CUDA 12 为例：
```bash
# 参考: https://k2-fsa.github.io/sherpa/onnx/cuda.html
pip install "sherpa-onnx==1.12.21+cuda12.cudnn9" -f https://k2-fsa.github.io/sherpa/onnx/cuda.html
```

### 2.3 安装 NVIDIA 依赖库
Linux 下 pip 安装的 `onnxruntime-gpu` 通常不包含完整的动态链接库（如 `libcublas`, `libcudnn`, `libcurand`, `libcufft` 等），需要手动安装：

```bash
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cuda-runtime-cu12 nvidia-curand-cu12 nvidia-cufft-cu12
```

## 3. 配置文件修改

修改项目根目录下的 `config.py`，启用 CUDA Provider。

**文件:** `config.py`
**修改内容:**
```python
class ParaformerArgs:
    # ... 其他配置保持不变 ...
    decoding_method = 'greedy_search'
    debug = False
    
    # [新增] 指定使用 CUDA
    provider = 'cuda' 
```

## 4. 解决库加载路径问题 (关键步骤)

在 Linux 环境中，pip 安装的 NVIDIA 库位于 `site-packages/nvidia` 目录下，系统默认无法找到这些动态链接库（`.so` 文件），会导致 `Failed to load library ...` 错误。

**解决方案**: 创建一个专用启动脚本 `run_gpu.sh`，在启动 Python 前自动将所有 NVIDIA 库路径加入 `LD_LIBRARY_PATH`。

**脚本:** `run_gpu.sh`
```bash
#!/bin/bash

# 获取当前 Python 环境中的 nvidia 库路径
PY_PREFIX=$(python -c "import sys; print(sys.prefix)")
# 自动获取 python 版本号 (如 3.12)
PY_VER=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
SITE_PACKAGES=$PY_PREFIX/lib/python$PY_VER/site-packages
NVIDIA_PATH=$SITE_PACKAGES/nvidia

# 自动扫描所有 nvidia 子目录下的 lib 文件夹并加入环境变量
NVIDIA_LIBS=""
if [ -d "$NVIDIA_PATH" ]; then
    for dir in $NVIDIA_PATH/*/lib; do
        if [ -d "$dir" ]; then
            NVIDIA_LIBS="$NVIDIA_LIBS:$dir"
        fi
    done
fi

# 构造 LD_LIBRARY_PATH (保留原有路径)
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH$NVIDIA_LIBS

echo "已配置 NVIDIA 库路径，正在启动服务..."
echo "LD_LIBRARY_PATH 包含: $NVIDIA_LIBS"

# 启动服务
python start_server.py
```

给脚本赋予执行权限：
```bash
chmod +x run_gpu.sh
```

## 5. 启动与验证

使用新脚本启动：
```bash
./run_gpu.sh
```

**成功标志:**
1. 输出日志中不再出现 `Fallback to cpu!`。
2. 模型加载速度显著提升（通常 < 5秒）。
3. 使用 `nvidia-smi` 查看，可以看到 Python 进程占用显存（通常约 400MB - 1GB）。

## 6. 常见问题

**Q: 启动时报 `PermissionError: ... -> '/tmp/jieba.cache'`**
**A:** 这是因为之前可能用了 `sudo` 运行程序，导致缓存文件归属权变成了 root。
**解决:** 清理缓存文件 `sudo rm -f /tmp/jieba.cache`，然后普通用户重新运行即可。

**Q: 报错 `libcurand.so.10 not found` 或其他 `.so` 缺失**
**A:** 说明缺少对应的 nvidia 库。检查步骤 2.3 是否安装了所有必要的包，特别是 `nvidia-curand-cu12` 和 `nvidia-cufft-cu12`。
