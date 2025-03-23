"""
大脑控制中心智能体
"""
import asyncio
import logging
from typing import Dict, Any
import ollama

from src.agents.base_agent import BaseAgent
from src.utils.mcp_protocol import TextMessage, ImageMessage, AudioMessage
from config import OLLAMA_BASE_URL, MODEL_CONFIG
# Add at the top of the file
brain_instance = None

class BrainAgent(BaseAgent):
    def __init__(self, agent_id: str, host: str, port: int):
        super().__init__(agent_id, "brain", host, port)
        global brain_instance
        brain_instance = self
        self.ollama_client = ollama.Client(host=OLLAMA_BASE_URL)
        
        # 加载不同类型的模型配置
        self.model_config = MODEL_CONFIG
        self.default_model = self.model_config["text"]["model"]
        self.context = []  # 对话上下文
        
        # 检查图像模型是否支持多模态
        self.multimodal_support = self.model_config["image"].get("multimodal", False)
        
        self.logger.info(f"大脑智能体初始化完成")
        self.logger.info(f"文本模型: {self.model_config['text']['model']}")
        self.logger.info(f"图像模型: {self.model_config['image']['model']}, 多模态支持: {self.multimodal_support}")
        self.logger.info(f"音频模型: {self.model_config['audio']['model']}")
        
        # 注册特定消息处理器
        self.register_handler("text", self._handle_text_message)
        self.register_handler("image", self._handle_image_message)
        self.register_handler("audio", self._handle_audio_message)
    
    async def _handle_text_message(self, message: Dict[str, Any]):
        """处理文本消息"""
        try:
            text = message['content'].get('text', '')
            sender_id = message['sender_id']
            
            # 添加到上下文
            self.context.append({"role": "user", "content": text})
            
            # 使用Ollama生成响应
            try:
                # 添加重试机制
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # 使用文本专用模型
                        text_model = self.model_config["text"]["model"]
                        text_params = self.model_config["text"]["params"]
                        
                        response = await asyncio.to_thread(
                            self.ollama_client.chat,
                            model=text_model,
                            messages=self.context,
                            **text_params
                        )
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise
                        await asyncio.sleep(1)  # 等待1秒后重试
                    
                reply_text = response['message']['content']
                self.context.append({"role": "assistant", "content": reply_text})
                
                # 发送文本响应到嘴巴智能体
                reply_message = TextMessage(
                    sender_id=self.agent_id,
                    receiver_id="mouth",
                    text=reply_text
                )
                self.logger.info(f"发送回复到嘴巴智能体: {reply_text}")
                # self.logger.info(f"完整消息对象: {reply_message.to_dict()}")
                await self.send_message("mouth", reply_message.to_dict())
                
                # 同时发送到Web界面
                from src.web.server import broadcast_message
                web_reply = {
                    "type": "chat",
                    "sender_id": "brain",
                    "content": {
                        "text": reply_text
                    }
                }
                await broadcast_message(web_reply)
                
            except Exception as e:
                self.logger.error(f"Error generating response: {e}")
                # 发送错误消息到Web界面
                from src.web.server import broadcast_message
                error_message = {
                    "type": "chat",
                    "sender_id": "system",
                    "content": {
                        "text": f"生成回复时出错: {str(e)}"
                    }
                }
                await broadcast_message(error_message)
        
        except Exception as e:
            self.logger.error(f"Error processing text message: {e}")
    
    async def _handle_image_message(self, message: Dict[str, Any]):
        """处理图像消息"""
        try:
            image_data = message['content'].get('image_data', '')
            sender_id = message['sender_id']
            person_name = message['content'].get('person_name', None)
            
            if not image_data:
                self.logger.warning("收到空图像数据")
                return
                    
            self.logger.info(f"收到来自{sender_id}的图像数据，准备分析")
            if person_name:
                self.logger.info(f"图像中识别到的人物: {person_name}")
            
            # 根据是否支持多模态选择不同的处理方式
            if self.multimodal_support:
                # 多模态处理方式 - 专注于识别人物表情和动作
                try:
                    # 使用图像专用模型
                    image_model = self.model_config["image"]["model"]
                    image_params = self.model_config["image"]["params"]
                    
                    # 使用generate接口而非chat接口
                    # 构建请求参数 - 明确要求识别表情和动作
                    generate_params = {
                        "model": image_model,
                        "prompt": "请简洁地分析图像中人物的表情和动作。只需描述你看到的表情（如微笑、严肃、惊讶等）和动作（如挥手、站立、坐着等），不要添加其他解释。",
                        "images": [image_data],  # 直接将base64图像数据放入images数组
                        "stream": False
                    }
                    
                    # 合并用户配置的参数
                    if image_params:
                        generate_params.update(image_params)
                    
                    # 调用Ollama API进行图像分析
                    response = await asyncio.to_thread(
                        self.ollama_client.generate,  # 使用generate而非chat
                        **generate_params
                    )
                    
                    analysis = response['response']  # generate接口返回的是response字段
                except Exception as e:
                    self.logger.error(f"多模态图像分析失败: {e}")
                    analysis = "无法识别表情和动作。"
            else:
                # 非多模态处理方式 - 使用纯文本提示
                analysis = "我看到了一个图像，但我无法识别人物的表情和动作。"
            
            # 提取对话历史，保留最近10条对话
            recent_context = []
            for item in self.context[-20:]:  # 获取最近20条记录进行筛选
                if item.get("role") in ["user", "assistant"]:  # 只保留用户和助手的对话
                    recent_context.append(item)
                if len(recent_context) >= 10:  # 最多保留10条
                    break
            
            # 将分析结果添加到上下文
            self.context.append({
                "role": "system", 
                "content": f"[视觉信息] 图像中{('的' + person_name) if person_name else ''}人物表情和动作: {analysis}"
            })
            
            # 生成基于视觉信息的简洁回复
            try:
                # 使用图像专用模型
                image_model = self.model_config["image"]["model"]
                image_params = self.model_config["image"]["params"]
                
                # 构建请求参数 - 强调简洁性
                person_info = f"名字是{person_name}的人" if person_name else "对方"
                
                # 根据是否有对话历史构建不同的提示
                if recent_context:
                    # 有对话历史，生成上下文相关的回复
                    greeting_prompt = f"你是一个友好的AI助手小美。你看到{person_info}，他/她的表情和动作是: {analysis}。请根据这些信息和最近的对话历史，生成一句非常简短自然的回应。回应必须简洁，不超过15个字，除非用户明确要求详细内容。"
                else:
                    # 无对话历史，生成初次见面的问候
                    greeting_prompt = f"你是一个友好的AI助手小美。你看到{person_info}，他/她的表情和动作是: {analysis}。请生成一句非常简短自然的问候语。问候必须简洁，不超过15个字。"
                
                generate_params = {
                    "model": image_model,
                    "prompt": greeting_prompt,
                    "stream": False
                }
                
                # 合并用户配置的参数
                if image_params:
                    generate_params.update(image_params)
                
                # 调用Ollama API生成回复
                greeting_response = await asyncio.to_thread(
                    self.ollama_client.generate,
                    **generate_params
                )
                
                greeting_text = greeting_response['response']
                
                # 将回复添加到上下文
                self.context.append({"role": "assistant", "content": greeting_text})
                
                # 发送回复到嘴巴智能体
                reply_message = TextMessage(
                    sender_id=self.agent_id,
                    receiver_id="mouth",
                    text=greeting_text
                )
                await self.send_message("mouth", reply_message.to_dict())
                
                # 同时发送到Web界面
                from src.web.server import broadcast_message
                web_reply = {
                    "type": "chat",
                    "sender_id": "brain",
                    "content": {
                        "text": greeting_text
                    }
                }
                await broadcast_message(web_reply)
                
            except Exception as e:
                self.logger.error(f"生成图像回复失败: {e}")
                
        except Exception as e:
            self.logger.error(f"处理图像消息时出错: {e}")
    
    async def _handle_audio_message(self, message: Dict[str, Any]):
        """处理音频消息"""
        try:
            audio_text = message['content'].get('text', '')  # 假设音频已被转换为文本
            sender_id = message['sender_id']
            
            if not audio_text:
                self.logger.warning("收到空音频文本")
                return
                
            self.logger.info(f"收到来自{sender_id}的音频文本: {audio_text}")
            
            # 添加到上下文
            self.context.append({"role": "user", "content": f"[语音输入] {audio_text}"})
            
            # 使用音频专用模型
            try:
                # 添加重试机制
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # 使用音频专用模型
                        audio_model = self.model_config["audio"]["model"]
                        audio_params = self.model_config["audio"]["params"]
                        
                        response = await asyncio.to_thread(
                            self.ollama_client.chat,
                            model=audio_model,
                            messages=self.context,
                            **audio_params
                        )
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise
                        await asyncio.sleep(10)  # 等待1秒后重试
                
                reply_text = response['message']['content']
                self.context.append({"role": "assistant", "content": reply_text})
                
                # 发送文本响应到嘴巴智能体
                reply_message = TextMessage(
                    sender_id=self.agent_id,
                    receiver_id="mouth",
                    text=reply_text
                )
                self.logger.info(f"发送音频回复到嘴巴智能体: {reply_text}")
                await self.send_message("mouth", reply_message.to_dict())
                
                # 同时发送到Web界面
                from src.web.server import broadcast_message
                web_reply = {
                    "type": "chat",
                    "sender_id": "brain",
                    "content": {
                        "text": reply_text
                    }
                }
                await broadcast_message(web_reply)
                
            except Exception as e:
                self.logger.error(f"生成音频回复失败: {e}")
                # 发送错误消息到Web界面
                from src.web.server import broadcast_message
                error_message = {
                    "type": "chat",
                    "sender_id": "system",
                    "content": {
                        "text": f"生成音频回复时出错: {str(e)}"
                    }
                }
                await broadcast_message(error_message)
        
        except Exception as e:
            self.logger.error(f"处理音频消息时出错: {e}")
    
    async def process_text_message(self, message):
        """处理文本消息并返回回复"""
        try:
            text = message.get('content', {}).get('text', '')
            self.logger.info(f"收到文本消息: {text}")
            
            # 这里可以添加更复杂的处理逻辑，例如调用LLM等
            # 简单示例：直接返回回复
            response = f"你好，我收到了你的消息: {text}"
            
            return response
        except Exception as e:
            self.logger.error(f"处理文本消息时出错: {e}")
            return "抱歉，我无法处理你的消息"