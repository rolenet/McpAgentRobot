"""
听觉智能体
"""
import speech_recognition as sr
from typing import Dict, Any
import asyncio

from config import SPEECH_RECOGNITION

from src.agents.base_agent import BaseAgent
from src.utils.mcp_protocol import AudioMessage, TextMessage

class EarAgent(BaseAgent):
    def __init__(self, agent_id: str, host: str, port: int):
        super().__init__(agent_id, "audio_input", host, port)
        self.recognizer = sr.Recognizer()
        self.is_listening = False
    
    async def start(self):
        """启动听觉智能体"""
        await super().start()
        self.is_listening = True
        asyncio.create_task(self._listen_loop())
    
    async def stop(self):
        """停止听觉智能体"""
        self.is_listening = False
        await super().stop()
    
    async def _listen_loop(self):
        """持续监听音频的循环"""
        while self.is_listening:
            try:
                # 添加麦克风资源检查和重试机制
                max_mic_retries = 5
                for mic_attempt in range(max_mic_retries):
                    try:
                        with sr.Microphone() as source:
                            # 调整麦克风参数，确保能在眼睛智能体运行后正常工作
                            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                            self.logger.info("Listening...")
                            audio = await asyncio.to_thread(
                                self.recognizer.listen,
                                source,
                                timeout=SPEECH_RECOGNITION['timeout'],
                                phrase_time_limit=SPEECH_RECOGNITION['phrase_time_limit']
                            )
                            break
                    except Exception as mic_error:
                        self.logger.warning(f"麦克风访问错误 (尝试 {mic_attempt+1}/{max_mic_retries}): {mic_error}")
                        if mic_attempt == max_mic_retries - 1:
                            raise
                        await asyncio.sleep(1)  # 等待一秒后重试
                    
                    # 添加重试机制
                    max_retries = SPEECH_RECOGNITION['retry_count']
                    for attempt in range(max_retries):
                        try:
                            text = await asyncio.to_thread(
                                self.recognizer.recognize_google,
                                audio,
                                language=SPEECH_RECOGNITION['language']
                            )
                            break
                        except sr.RequestError:
                            if attempt == max_retries - 1:
                                raise
                            await asyncio.sleep(SPEECH_RECOGNITION['retry_delay'])
                    
                    # 发送文本消息到大脑
                    message = TextMessage(
                        sender_id=self.agent_id,
                        receiver_id="brain",
                        text=text
                    )
                    await self.send_message("brain", message.to_dict())
                    
                    # 同时发送到Web界面
                    try:
                        from src.web.server import broadcast_message
                        web_message = {
                            "type": "audio",
                            "sender_id": self.agent_id,
                            "content": text
                        }
                        await broadcast_message(web_message)
                        
                        # 同时作为聊天消息显示
                        chat_message = {
                            "type": "chat",
                            "sender_id": "user",
                            "content": {
                                "text": text
                            }
                        }
                        await broadcast_message(chat_message)
                    except Exception as e:
                        self.logger.error(f"发送消息到Web界面失败: {e}")
                    
            except sr.UnknownValueError:
                self.logger.info("Could not understand audio")
            except sr.RequestError as e:
                self.logger.error(f"Error with speech recognition service: {e}")
                await asyncio.sleep(2)  # 服务错误时等待更长时间
            except Exception as e:
                self.logger.error(f"Error in listen loop: {e}")
                await asyncio.sleep(1)