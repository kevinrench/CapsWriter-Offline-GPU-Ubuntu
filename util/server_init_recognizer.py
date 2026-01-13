import time
import sherpa_onnx
from multiprocessing import Queue
import signal
from platform import system
from config import ServerConfig as Config
from config import ParaformerArgs, ModelPaths
from util.server_cosmic import console
from util.server_recognize import recognize
from util.empty_working_set import empty_current_working_set



def disable_jieba_debug():
    # 关闭 jieba 的 debug
    import jieba
    import logging
    jieba.setLogLevel(logging.INFO)


def init_recognizer(queue_in: Queue, queue_out: Queue, sockets_id):

    # -----------------------------------------------------------
    # 临时修复：确保子进程也能找到 NVIDIA 库
    import os
    import sys
    from pathlib import Path
    if sys.platform == 'linux':
        site_packages = Path(sys.prefix) / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
        nvidia_path = site_packages / 'nvidia'
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
            os.environ['LD_LIBRARY_PATH'] = ':'.join(new_paths) + ':' + current_ld_path
    # -----------------------------------------------------------

    # Ctrl-C 退出
    signal.signal(signal.SIGINT, lambda signum, frame: exit())

    # 导入模块
    with console.status("载入模块中…", spinner="bouncingBall", spinner_style="yellow"):
        import sherpa_onnx
        from funasr_onnx import CT_Transformer
        disable_jieba_debug()
    console.print('[green4]模块加载完成', end='\n\n')

    # 载入语音模型
    console.print('[yellow]语音模型载入中', end='\r'); t1 = time.time()
    recognizer = sherpa_onnx.OfflineRecognizer.from_paraformer(
        **{key: value for key, value in ParaformerArgs.__dict__.items() if not key.startswith('_')}
    )
    console.print(f'[green4]语音模型载入完成', end='\n\n')

    # 载入标点模型
    punc_model = None
    if Config.format_punc:
        console.print('[yellow]标点模型载入中', end='\r')
        punc_model = CT_Transformer(ModelPaths.punc_model_dir, quantize=True)
        console.print(f'[green4]标点模型载入完成', end='\n\n')

    console.print(f'模型加载耗时 {time.time() - t1 :.2f}s', end='\n\n')

    # 清空物理内存工作集
    if system() == 'Windows':
        empty_current_working_set()

    queue_out.put(True)  # 通知主进程加载完了

    while True:
        # 从队列中获取任务消息
        # 阻塞最多1秒，便于中断退出
        try:
            task = queue_in.get(timeout=1)       
        except:
            continue

        if task.socket_id not in sockets_id:    # 检查任务所属的连接是否存活
            continue

        result = recognize(recognizer, punc_model, task)   # 执行识别
        queue_out.put(result)      # 返回结果

