"""
嘴巴智能体 - 负责语音输出
"""
import asyncio
import logging
from typing import Dict, Any
import pyttsx3
import threading
import time
import os

from src.agents.base_agent import BaseAgent
from src.utils.mcp_protocol import TextMessage

class MouthAgent(BaseAgent):
    def __init__(self, agent_id: str, host: str, port: int):
        super().__init__(agent_id, "speech", host, port)
        # 初始化TTS引擎
        self.tts_queue = asyncio.Queue()
        
        # 注册消息处理器
        self.register_handler("text", self._handle_text_message)
    
    async def start(self):
        """启动嘴巴智能体"""
        await super().start()

        # 测试TTS引擎
        test_result = await self._test_tts()
        if not test_result:
            self.logger.warning("TTS测试失败，语音功能可能不可用")
        
        # 启动TTS处理循环
        asyncio.create_task(self._process_tts_queue())
        
        self.logger.info("嘴巴智能体已启动")
    
    async def _test_tts(self):
        """测试TTS引擎"""
        try:
            # 在单独的线程中初始化和测试TTS引擎
            result = await asyncio.to_thread(self._init_and_test_tts)
            return result
        except Exception as e:
            self.logger.error(f"TTS测试失败: {e}")
            return False
    
    def _init_and_test_tts(self):
        """初始化并测试TTS引擎"""
        try:
            self.logger.info("初始化TTS引擎")
            engine = pyttsx3.init()
            
            # 设置语音属性
            engine.setProperty('rate', 180)  # 语速
            engine.setProperty('volume', 0.9)  # 音量
            
            # 获取可用的语音
            voices = engine.getProperty('voices')
            self.logger.info(f"可用语音数量: {len(voices)}")
            
            # 尝试设置中文语音
            for voice in voices:
                self.logger.info(f"语音: ID={voice.id}, Name={voice.name}")
                if 'chinese' in voice.name.lower() or 'zh' in voice.id.lower():
                    engine.setProperty('voice', voice.id)
                    self.logger.info(f"设置中文语音: {voice.id}")
                    break
            
            # 测试播放
            test_text = "嘴巴智能体启动！"
            self.logger.info(f"测试TTS: {test_text}")
            
            engine.say(test_text)
            engine.runAndWait()
            engine.stop()  # 使用完毕后停止引擎
            
            self.logger.info("TTS引擎初始化和测试完成")
            return True
        except Exception as e:
            self.logger.error(f"TTS引擎初始化或测试失败: {e}")
            return False
    
    async def _process_tts_queue(self):
        """处理TTS队列"""
        while True:
            try:
                text = await self.tts_queue.get()
                # self.logger.info(f"准备播放语音: {text}")
                
                # 在线程中执行TTS，避免阻塞主线程
                thread = threading.Thread(
                    target=self._speak_text, 
                    args=(text,)
                )
                thread.daemon = True
                thread.start()
                
                self.tts_queue.task_done()
            except Exception as e:
                self.logger.error(f"处理TTS队列时出错: {e}")
            await asyncio.sleep(0.1)
    
    def _speak_text(self, text):
        """使用TTS引擎播放文本"""
        try:
            self.logger.info(f"开始播放语音: {text}")
            # 每次播放前重新初始化引擎
            engine = pyttsx3.init()
            # 设置语音属性
            engine.setProperty('rate', 250)  # 语速
            engine.setProperty('volume', 0.9)  # 音量
            
            # 尝试设置中文语音
            voices = engine.getProperty('voices')
            for voice in voices:
                if 'chinese' in voice.name.lower() or 'zh' in voice.id.lower():
                    engine.setProperty('voice', voice.id)
                    break
                    
            engine.say(text)
            engine.runAndWait()
            # 使用完毕后停止引擎
            engine.stop()
            self.logger.info("语音播放完成")
        except Exception as e:
            self.logger.error(f"语音播放失败: {e}")
    
    async def _handle_text_message(self, message: Dict[str, Any]):
        """处理文本消息（语音输出）"""
        try:
            self.logger.info(f"收到文本消息: {message}")
            # 检查消息格式
            if 'content' in message:
                if isinstance(message['content'], dict) and 'text' in message['content']:
                    text = message['content']['text']
                else:
                    text = message['content']
            else:
                text = message.get('text', '')
            
            sender_id = message.get('sender_id', 'unknown')
            
            self.logger.info(f"收到来自{sender_id}的语音输出请求: {text}")
            
            # 将语音输出发送到Web界面
            from src.web.server import broadcast_message
            await broadcast_message({
                "type": "speech",
                "content": text
            })
            
            # 添加到TTS队列
            await self.tts_queue.put(text)
            
        except Exception as e:
            self.logger.error(f"处理文本消息时出错: {e}")
    
    async def stop(self):
        """停止嘴巴智能体"""
        # 等待TTS队列处理完成
        if hasattr(self, 'tts_queue') and self.tts_queue:
            await self.tts_queue.join()
        
        await super().stop()
        self.logger.info("嘴巴智能体已停止")