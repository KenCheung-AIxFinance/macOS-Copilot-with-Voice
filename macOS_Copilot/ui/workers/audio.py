import time
import speech_recognition as sr
from PyQt6.QtCore import QThread
from macOS_Copilot.ui.workers.signals import WorkerSignals

class AudioWorker(QThread):
    """处理音频识别的工作线程"""
    def __init__(self, recognizer):
        super().__init__()
        self.recognizer = recognizer
        self.signals = WorkerSignals()
        self.is_running = True
        self.is_speaking = False
        self.is_paused = False
        self.microphone = None
        self.should_reset = False

    def set_speaking(self, speaking):
        """设置说话状态"""
        self.is_speaking = speaking
        if speaking:
            # 当AI开始说话时，标记需要重置麦克风
            self.should_reset = True
            
    def set_paused(self, paused):
        """设置暂停状态"""
        self.is_paused = paused
        if paused or not paused:
            # 无论是暂停还是取消暂停，都标记需要重置麦克风
            self.should_reset = True

    def run(self):
        while self.is_running:
            # 处理正常语音识别
            if not self.is_speaking and not self.is_paused:
                try:
                    # 如果需要重置麦克风，则关闭当前麦克风并重新创建
                    if self.should_reset:
                        if self.microphone:
                            try:
                                self.microphone.__exit__(None, None, None)
                            except:
                                pass
                            self.microphone = None
                        time.sleep(0.5)  # 短暂等待，确保资源释放
                        self.should_reset = False
                    
                    # 创建新的麦克风连接
                    if not self.microphone:
                        self.microphone = sr.Microphone().__enter__()
                        # 调整噪声阈值
                        self.recognizer.adjust_for_ambient_noise(self.microphone, duration=0.5)
                        
                    self.signals.status.emit("正在聆听...")
                    audio = self.recognizer.listen(
                        self.microphone, 
                        timeout=5, 
                        phrase_time_limit=10
                    )
                    self.signals.status.emit("正在处理...")
                    text = self.recognizer.recognize_google(audio, language='zh-CN')
                    self.signals.result.emit(text)
                    
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except Exception as e:
                    self.signals.error.emit(f"语音识别错误: {str(e)}")
                    # 发生错误时标记需要重置麦克风
                    self.should_reset = True
                    time.sleep(0.5)
                    
            elif self.is_speaking:
                # AI说话时，关闭麦克风连接，完全停止录音
                if self.microphone:
                    try:
                        self.microphone.__exit__(None, None, None)
                    except:
                        pass
                    self.microphone = None
                
                self.signals.status.emit("AI朗读中，语音识别已禁用...")
                time.sleep(0.5)  # 减少CPU使用
                
            elif self.is_paused:
                # 暂停状态，不进行任何录音
                if self.microphone:
                    try:
                        self.microphone.__exit__(None, None, None)
                    except:
                        pass
                    self.microphone = None
                
                # self.signals.status.emit("语音输入已暂停")
                time.sleep(0.5)
                
            time.sleep(0.1)

    def stop(self):
        self.is_running = False 