"""人脸识别模块
用于检测和提取人脸特征
"""
import cv2
import base64
import numpy as np
import logging
from typing import List, Tuple, Optional, Dict, Any
import io
from PIL import Image, ImageDraw, ImageFont

class FaceRecognition:
    """人脸识别类
    用于检测和提取人脸特征
    """
    def __init__(self):
        self.logger = logging.getLogger("FaceRecognition")
        # 加载人脸检测器
        self.logger.info("加载人脸检测器")
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.logger.info("人脸识别模块初始化完成")
    
    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """检测图像中的人脸
        
        Args:
            image: 输入图像，OpenCV格式（BGR）
            
        Returns:
            人脸边界框列表，每个边界框为(x, y, w, h)格式
        """
        # 转换为灰度图像
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # self.logger.info("转换为灰度图像")
        # 检测人脸
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        # self.logger.info("得到人脸边界框")
        return faces
    
    def extract_face_encoding(self, image: np.ndarray, face_location: Tuple[int, int, int, int]) -> np.ndarray:
        """提取人脸特征向量
        
        Args:
            image: 输入图像，OpenCV格式（BGR）
            face_location: 人脸边界框，(x, y, w, h)格式
            
        Returns:
            人脸特征向量
        """
        # 提取人脸区域
        x, y, w, h = face_location
        face_image = image[y:y+h, x:x+w]
        
        # 调整大小为固定尺寸
        face_image = cv2.resize(face_image, (128, 128))
        
        # 转换为灰度图像
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        
        # 使用HOG特征作为人脸编码
        # 计算HOG特征
        hog = cv2.HOGDescriptor((128, 128), (16, 16), (8, 8), (8, 8), 9)
        hog_features = hog.compute(gray)
        
        # 归一化特征向量
        if np.linalg.norm(hog_features) > 0:
            hog_features = hog_features / np.linalg.norm(hog_features)
        
        return hog_features
    
    def process_image(self, image_base64: str) -> Tuple[List[Tuple[int, int, int, int]], List[np.ndarray], List[str]]:
        """处理Base64编码的图像，检测人脸并提取特征
        
        Args:
            image_base64: Base64编码的图像数据
            
        Returns:
            人脸边界框列表，人脸特征向量列表，人脸图像Base64编码列表
        """
        try:
            # self.logger.info(f"开始解码Base64图像")
            # 解码Base64图像
            image_data = base64.b64decode(image_base64)
            image_array = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image is None:
                self.logger.error("无法解码图像数据")
                return [], [], []
            
            # 检测人脸
            faces = self.detect_faces(image)
            
            if len(faces) == 0:
                self.logger.info("未检测到人脸")
                return [], [], []
            
            # 提取每个人脸的特征
            face_encodings = []
            face_images_base64 = []
            
            for face in faces:
                # 提取特征
                encoding = self.extract_face_encoding(image, face)
                face_encodings.append(encoding)
                
                # 提取人脸图像并编码为Base64
                x, y, w, h = face
                face_image = image[y:y+h, x:x+w]
                _, buffer = cv2.imencode('.jpg', face_image, [cv2.IMWRITE_JPEG_QUALITY, 80])
                face_image_base64 = base64.b64encode(buffer).decode('utf-8')
                face_images_base64.append(face_image_base64)
            
            self.logger.info(f"检测到{len(faces)}个人脸")
            return faces, face_encodings, face_images_base64
        
        except Exception as e:
            self.logger.error(f"处理图像时出错: {e}")
            return [], [], []
    
    def draw_faces(self, image_base64: str, faces: List[Tuple[int, int, int, int]], 
                   names: List[str] = None) -> str:
        """在图像上绘制人脸边界框和名称
        
        Args:
            image_base64: Base64编码的图像数据
            faces: 人脸边界框列表
            names: 人脸对应的名称列表
            
        Returns:
            绘制了人脸边界框和名称的图像的Base64编码
        """
        try:
            # 解码Base64图像
            image_data = base64.b64decode(image_base64)
            image_array = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image is None:
                self.logger.error("无法解码图像数据")
                return image_base64
            
            # 如果没有提供名称，使用默认名称
            if names is None:
                names = [f"Person {i+1}" for i in range(len(faces))]
            
            # 将OpenCV图像转换为PIL图像以支持中文文本
            image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(image_pil)
            
            # 使用系统默认字体
            font_size = 30
            try:
                font = ImageFont.truetype("simhei.ttf", font_size)  # 使用黑体
            except:
                try:
                    font = ImageFont.truetype("simsun.ttc", font_size)  # 尝试使用宋体
                except:
                    font = ImageFont.load_default()  # 如果都失败了使用默认字体
            
            # 绘制每个人脸的边界框和名称
            for i, (x, y, w, h) in enumerate(faces):
                # 绘制边界框
                cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # 绘制名称
                name = names[i] if i < len(names) else f"Person {i+1}"
                # 在PIL图像上绘制中文文本
                draw.text((x, max(y-font_size, 0)), name, font=font, fill=(0, 255, 0))
            
            # 将PIL图像转换回OpenCV格式
            image = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
            
            # 编码为Base64
            _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 70])
            return base64.b64encode(buffer).decode('utf-8')
        
        except Exception as e:
            self.logger.error(f"绘制人脸时出错: {e}")
            return image_base64