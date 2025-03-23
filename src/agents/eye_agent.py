"""
视觉智能体
"""
import cv2
import base64
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import asyncio
import time
import random
import string
import os

from src.agents.base_agent import BaseAgent
from src.utils.mcp_protocol import ImageMessage, TextMessage
from src.utils.face_recognition import FaceRecognition
from src.utils.person_database import PersonDatabase

class EyeAgent(BaseAgent):
    def __init__(self, agent_id: str, host: str, port: int):
        super().__init__(agent_id, "vision", host, port)
        self.camera = None
        self.is_capturing = False
        self.last_analysis_time = 0  # 上次分析图像的时间
        self.analysis_interval = 10.0  # 分析图像的时间间隔(秒)
        
        # 初始化人脸识别模块
        self.face_recognition = FaceRecognition()
        
        # 初始化人物数据库
        self.person_database = PersonDatabase()
        
        # 记录上次识别到的人物ID，用于避免重复问候
        self.last_recognized_person_id = None
        self.last_recognition_time = 0
        self.recognition_cooldown = 600.0  # 同一人物的问候冷却时间(秒)
    
    async def start(self):
        """启动视觉智能体"""
        await super().start()
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            self.logger.error("Failed to open camera")
            return
        
        self.is_capturing = True
        asyncio.create_task(self._capture_loop())
        self.logger.info("视觉智能体已启动")
        self.logger.info(f"已加载{len(self.person_database.get_all_persons())}个已知人物数据")
    
    async def stop(self):
        """停止视觉智能体"""
        self.is_capturing = False
        if self.camera:
            self.camera.release()
        await super().stop()
    
    async def _process_face_recognition(self, image_base64: str) -> Optional[str]:
        """处理人脸识别
        
        Args:
            image_base64: Base64编码的图像数据
            
        Returns:
            处理后的图像Base64编码，如果没有检测到人脸则返回None
        """
        try:
            # self.logger.info(f"开始处理人脸图像识别")
            # 检测人脸并提取特征
            faces, face_encodings, face_images = self.face_recognition.process_image(image_base64)
            # self.logger.info(f"已经监测到人脸图像")
            if len(faces) == 0:
                return None
            # self.logger.info(f"开始定义识别结果")
            # 识别结果
            recognized_names = []
            recognized_ids = []
            # self.logger.info(f"开始定义识别到的人物信息")
            recognized_info = []  # 存储识别到的人物信息，用于显示
            # self.logger.info(f"开始定义识别的时间")
            current_time = time.time()
            # self.logger.info(f"开始处理每个检测到的人脸")
            # 处理每个检测到的人脸
            for i, (face, encoding, face_image) in enumerate(zip(faces, face_encodings, face_images)):
                self.logger.info(f"查找相似人物")
                # 查找相似人物
                person_id = self.person_database.find_similar_person(encoding)
                
                if person_id is not None:
                    # 已知人物
                    person = self.person_database.get_person(person_id)
                    name = person["name"]
                    recognized_names.append(name)
                    recognized_ids.append(person_id)
                    
                    # 计算上次见面时间
                    last_seen = person["last_seen"]
                    time_diff = current_time - last_seen
                    time_info = self._format_time_diff(time_diff) if time_diff > 60 else "刚刚"
                    
                    # 更新人物信息
                    self.person_database.update_person(
                        person_id, 
                        last_seen=current_time,
                        face_image=face_image
                    )
                    
                    # 添加识别信息
                    recognized_info.append(f"{name} (见过{person['seen_count']}次，上次见面: {time_info})")
                    
                    self.logger.info(f"识别到已知人物: {name} (ID: {person_id}, 见过{person['seen_count']}次)")
                else:
                    self.logger.info(f"新人物，生成随机名称")
                    # 新人物，生成随机名称
                    random_name = self._generate_random_name()
                    
                    # 添加到数据库
                    new_id = self.person_database.add_person(
                        name=random_name,
                        face_encoding=encoding,
                        face_image=face_image
                    )
                    
                    recognized_names.append(random_name)
                    recognized_ids.append(new_id)
                    recognized_info.append(f"{random_name} (初次见面)")
                    self.logger.info(f"添加新人物: {random_name} (ID: {new_id})")
            self.logger.info(f"绘制人脸边界框和名称")
            # 绘制人脸边界框和名称
            processed_image = self.face_recognition.draw_faces(image_base64, faces, recognized_names)
            
            # 检查是否需要发送问候消息
            await self._send_greeting_if_needed(recognized_ids, recognized_names, recognized_info, current_time)
            
            return processed_image
        
        except Exception as e:
            self.logger.error(f"处理人脸识别时出错: {e}")
            return None
    
    def _generate_random_name(self) -> str:
        """生成随机人物名称"""
        prefixes = ["赵", "钱", "孙", "李", "王", "刘", "田"]
        names = ["小明", "小红", "小华", "小天", "小宇", "小花", "小美", "小宁", "小德", "小琳"]
        
        prefix = random.choice(prefixes)
        name = random.choice(names)
        
        # 添加随机数字后缀，确保唯一性
        suffix = ''.join(random.choices(string.digits, k=2))
        
        return f"{prefix}{name}{suffix}"
    
    def _format_time_diff(self, time_diff: float) -> str:
        """格式化时间差
        
        Args:
            time_diff: 时间差（秒）
            
        Returns:
            格式化后的时间差字符串
        """
        # 转换为整数
        seconds = int(time_diff)
        
        # 计算不同时间单位
        minutes = seconds // 60
        hours = minutes // 60
        days = hours // 24
        
        # 根据时间长短选择合适的显示格式
        if days > 0:
            return f"{days}天前"
        elif hours > 0:
            return f"{hours}小时前"
        elif minutes > 0:
            return f"{minutes}分钟前"
        else:
            return f"{seconds}秒前"
    
    async def _send_greeting_if_needed(self, person_ids: List[int], person_names: List[str], person_info: List[str], current_time: float) -> None:
        """如果需要，发送问候消息
        
        Args:
            person_ids: 识别到的人物ID列表
            person_names: 识别到的人物名称列表
            person_info: 识别到的人物详细信息列表
            current_time: 当前时间戳
        """
        if not person_ids:
            return
        
        # 选择第一个检测到的人物进行问候
        person_id = person_ids[0]
        person_name = person_names[0]
        
        # 检查是否需要问候（避免频繁问候同一个人）
        if (self.last_recognized_person_id != person_id or 
                current_time - self.last_recognition_time >= self.recognition_cooldown):
            
            # 更新最后识别记录
            self.last_recognized_person_id = person_id
            self.last_recognition_time = current_time
            
            # 获取人物信息
            person = self.person_database.get_person(person_id)
            seen_count = person["seen_count"]
            
            # 构建问候消息
            if seen_count <= 1:
                greeting = f"你好，{person_name}！很高兴认识你！"
            else:
                greeting = f"你好，{person_name}！很高兴再次见到你！" #这是我们第{seen_count}次见面了。"
            
            # 发送问候消息到大脑
            greeting_message = TextMessage(
                sender_id=self.agent_id,
                receiver_id="brain",
                text=f"[视觉识别] 我看到了{person_name}。{greeting}"
            )
            
            self.logger.info(f"发送问候消息: {greeting}")
            await self.send_message("brain", greeting_message.to_dict())
    
    async def _capture_loop(self):
        """持续捕获视频的循环"""
        while self.is_capturing:
            try:
                ret, frame = self.camera.read()
                if ret:
                    # 转换图像为JPEG格式的base64字符串
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    image_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    # 处理人脸识别
                    processed_image = await self._process_face_recognition(image_base64)
                    
                    # 发送到Web界面
                    from src.web.server import broadcast_message
                    success = await broadcast_message({
                        "type": "vision",
                        "content": processed_image or image_base64
                    })
                    
                    # 定期发送图像到大脑进行分析
                    current_time = time.time()
                    if current_time - self.last_analysis_time >= self.analysis_interval:
                        self.last_analysis_time = current_time
                        
                        # 获取当前识别到的人物名称（如果有）
                        person_name = None
                        if self.last_recognized_person_id is not None:
                            person = self.person_database.get_person(self.last_recognized_person_id)
                            if person:
                                person_name = person["name"]
                        
                        # 创建图像消息，包含人物名称
                        message = ImageMessage(
                            sender_id=self.agent_id,
                            receiver_id="brain",
                            image_data=image_base64,
                            person_name=person_name
                        )
                        
                        # 发送到大脑智能体
                        self.logger.info("发送图像到大脑进行分析")
                        await self.send_message("brain", message.to_dict())
                
                # 控制帧率，设置为1FPS
                await asyncio.sleep(1.0)  # 1FPS
            
            except Exception as e:
                self.logger.error(f"Error in capture loop: {e}")
                await asyncio.sleep(15.0)  # 出错时等待5秒再重试