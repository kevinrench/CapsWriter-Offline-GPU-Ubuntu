#!/bin/bash

# 获取当前 Python 环境中的 nvidia 库路径
PY_PREFIX=$(python -c "import sys; print(sys.prefix)")
SITE_PACKAGES=$PY_PREFIX/lib/python$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")/site-packages
NVIDIA_PATH=$SITE_PACKAGES/nvidia

# 自动扫描所有 nvidia 子目录下的 lib 文件夹
NVIDIA_LIBS=""
if [ -d "$NVIDIA_PATH" ]; then
    for dir in $NVIDIA_PATH/*/lib; do
        if [ -d "$dir" ]; then
            NVIDIA_LIBS="$NVIDIA_LIBS:$dir"
        fi
    done
fi

# 构造 LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH$NVIDIA_LIBS

echo "Using LD_LIBRARY_PATH with all nvidia libs."

# 启动服务
python start_server.py