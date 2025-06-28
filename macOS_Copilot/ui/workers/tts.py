import os
import time
import asyncio
import edge_tts
from PyQt6.QtCore import QThread
from macOS_Copilot.ui.workers.signals import WorkerSignals

class TTSWorker(QThread):
    """处理语音合成的工作线程"""
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self.text = ""
        self.voice = 'zh-CN-XiaoxiaoNeural'

    def set_text(self, text):
        self.text = text

    def run(self):
        try:
            # 生成唯一的临时文件名，避免多次调用冲突
            temp_file = f"temp_{int(time.time())}.mp3"
            
            # 语音合成与播放
            communicate = edge_tts.Communicate(self.text, self.voice)
            asyncio.run(communicate.save(temp_file))
            os.system(f"afplay {temp_file}")
            
            # 合成完成后删除临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception as e:
            self.signals.error.emit(f"TTS错误: {str(e)}")
        finally:
            self.signals.finished.emit() 