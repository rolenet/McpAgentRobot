"""人物数据库模块
用于存储和加载已识别的人物信息
"""
import os
import json
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
import time

class PersonDatabase:
    """人物数据库类
    用于存储和加载已识别的人物信息
    """
    def __init__(self, database_path: str = "data/persons"):
        self.logger = logging.getLogger("PersonDatabase")
        self.database_path = database_path
        self.persons = {}  # 存储人物信息的字典，键为人物ID，值为人物信息
        self.next_id = 1  # 下一个可用的人物ID
        
        # 确保数据目录存在
        os.makedirs(self.database_path, exist_ok=True)
        
        # 加载已有人物数据
        self.load_persons()
    
    def load_persons(self) -> None:
        """加载所有已保存的人物数据"""
        try:
            # 检查索引文件是否存在
            index_path = os.path.join(self.database_path, "index.json")
            if not os.path.exists(index_path):
                self.logger.info("人物索引文件不存在，创建新索引")
                return
            
            # 加载索引文件
            with open(index_path, "r", encoding="utf-8") as f:
                index_data = json.load(f)
                self.next_id = index_data.get("next_id", 1)
                person_files = index_data.get("persons", [])
            
            # 加载每个人物的数据
            for person_file in person_files:
                person_path = os.path.join(self.database_path, person_file)
                if os.path.exists(person_path):
                    with open(person_path, "r", encoding="utf-8") as f:
                        person_data = json.load(f)
                        # 将特征向量从列表转换回numpy数组
                        if "face_encoding" in person_data and person_data["face_encoding"]:
                            person_data["face_encoding"] = np.array(person_data["face_encoding"])
                        self.persons[person_data["id"]] = person_data
            
            self.logger.info(f"成功加载{len(self.persons)}个人物数据")
        
        except Exception as e:
            self.logger.error(f"加载人物数据时出错: {e}")
    
    def save_index(self) -> None:
        """保存人物索引"""
        try:
            index_data = {
                "next_id": self.next_id,
                "persons": [f"person_{person_id}.json" for person_id in self.persons.keys()]
            }
            
            index_path = os.path.join(self.database_path, "index.json")
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            self.logger.error(f"保存人物索引时出错: {e}")
    
    def save_person(self, person_id: int) -> None:
        """保存单个人物数据"""
        try:
            if person_id not in self.persons:
                self.logger.warning(f"人物ID {person_id} 不存在")
                return
            
            person_data = self.persons[person_id].copy()
            
            # 将numpy数组转换为列表以便JSON序列化
            if "face_encoding" in person_data and person_data["face_encoding"] is not None:
                person_data["face_encoding"] = person_data["face_encoding"].tolist()
            
            person_path = os.path.join(self.database_path, f"person_{person_id}.json")
            with open(person_path, "w", encoding="utf-8") as f:
                json.dump(person_data, f, ensure_ascii=False, indent=2)
            
            # 更新索引
            self.save_index()
        
        except Exception as e:
            self.logger.error(f"保存人物数据时出错: {e}")
    
    def add_person(self, name: str, face_encoding: np.ndarray, face_image: str) -> int:
        """添加新人物
        
        Args:
            name: 人物名称
            face_encoding: 人脸特征向量
            face_image: 人脸图像的base64编码
            
        Returns:
            新添加的人物ID
        """
        person_id = self.next_id
        self.next_id += 1
        
        # 创建人物数据
        person_data = {
            "id": person_id,
            "name": name,
            "face_encoding": face_encoding,
            "face_image": face_image,
            "first_seen": time.time(),
            "last_seen": time.time(),
            "seen_count": 1
        }
        
        # 添加到内存中
        self.persons[person_id] = person_data
        
        # 保存到文件
        self.save_person(person_id)
        
        self.logger.info(f"添加新人物: {name} (ID: {person_id})")
        return person_id
    
    def update_person(self, person_id: int, last_seen: float = None, face_image: str = None) -> None:
        """更新人物信息
        
        Args:
            person_id: 人物ID
            last_seen: 最后一次见到的时间戳
            face_image: 新的人脸图像base64编码
        """
        if person_id not in self.persons:
            self.logger.warning(f"人物ID {person_id} 不存在")
            return
        
        person = self.persons[person_id]
        
        # 更新最后见到时间
        if last_seen is None:
            last_seen = time.time()
        person["last_seen"] = last_seen
        
        # 更新见到次数
        person["seen_count"] += 1
        
        # 更新人脸图像
        if face_image:
            person["face_image"] = face_image
        
        # 保存更新
        self.save_person(person_id)
        
        self.logger.info(f"更新人物信息: {person['name']} (ID: {person_id})")
    
    def find_similar_person(self, face_encoding: np.ndarray, threshold: float = 0.5) -> Optional[int]:
        """查找相似的人物
        
        Args:
            face_encoding: 人脸特征向量
            threshold: 相似度阈值，默认为0.8
            
        Returns:
            如果找到相似人物，返回人物ID；否则返回None
        """
        self.logger.debug(f"开始查找相似人物，输入特征向量形状: {face_encoding.shape}, 数据类型: {face_encoding.dtype}")
        self.logger.debug(f"相似度阈值: {threshold}, 类型: {type(threshold)}")
        
        if not self.persons:
            self.logger.info("人物数据库为空，无法查找相似人物")
            return None
        
        # 计算与所有已知人物的相似度
        max_similarity = 0.0  # 确保使用浮点数
        most_similar_id = None
        self.logger.debug(f"人物数据库中共有{len(self.persons)}个人物")
        
        for person_id, person in self.persons.items():
            if "face_encoding" not in person or person["face_encoding"] is None:
                self.logger.debug(f"人物ID {person_id} 没有人脸特征向量，跳过")
                continue
            
            self.logger.debug(f"计算与人物ID {person_id} 的相似度，人物特征向量形状: {person['face_encoding'].shape}, 数据类型: {person['face_encoding'].dtype}")
            
            # 计算余弦相似度
            try:
                similarity = self._cosine_similarity(face_encoding, person["face_encoding"])
                
                # 记录原始相似度值和类型
                self.logger.debug(f"与人物ID {person_id} 的原始相似度: {similarity}, 类型: {type(similarity)}")
                
                # 确保similarity是标量值
                if isinstance(similarity, np.ndarray):
                    self.logger.debug(f"相似度是NumPy数组，形状: {similarity.shape}, 数据类型: {similarity.dtype}, 值: {similarity}")
                    if similarity.size == 1:
                        original_similarity = similarity
                        similarity = float(similarity.item())
                        self.logger.debug(f"将单元素数组转换为标量: 从 {original_similarity} 到 {similarity}")
                    else:
                        original_similarity = similarity
                        similarity = float(similarity.mean())
                        self.logger.warning(f"相似度结果是多元素数组，大小: {original_similarity.size}, 取平均值: {similarity}")
                elif not isinstance(similarity, (int, float, np.number)):
                    self.logger.warning(f"相似度不是数值类型，而是 {type(similarity)}，设置为0")
                    similarity = 0.0
                else:
                    # 确保是Python原生浮点数
                    original_similarity = similarity
                    similarity = float(similarity)
                    if original_similarity != similarity:
                        self.logger.debug(f"将相似度从 {original_similarity} 转换为浮点数: {similarity}")
                
                self.logger.debug(f"与人物ID {person_id} 的最终相似度: {similarity}")
                
                # 使用标量值进行比较 - 确保两边都是Python原生浮点数
                self.logger.debug(f"比较相似度: 当前值 {similarity} (类型: {type(similarity)}) vs 最大值 {max_similarity} (类型: {type(max_similarity)})")
                # 再次确保比较时使用的是Python原生浮点数
                similarity_float = float(similarity)
                max_similarity_float = float(max_similarity)
                
                if similarity_float > max_similarity_float:
                    self.logger.debug(f"找到更高相似度: {similarity_float} > {max_similarity_float}")
                    max_similarity = similarity_float
                    most_similar_id = person_id
            except Exception as e:
                self.logger.error(f"计算与人物ID {person_id} 的相似度时出错: {e}")
                import traceback
                self.logger.error(f"错误详情: {traceback.format_exc()}")
                continue
        
        # 如果最大相似度超过阈值，返回对应的人物ID
        self.logger.debug(f"最大相似度: {max_similarity} (类型: {type(max_similarity)}), 最相似人物ID: {most_similar_id}")
        
        # 确保阈值比较使用相同类型
        threshold_float = float(threshold)
        max_similarity_float = float(max_similarity)
        self.logger.debug(f"阈值比较: {max_similarity_float} >= {threshold_float}")
        
        if max_similarity_float >= threshold_float and most_similar_id is not None:
            self.logger.info(f"找到相似人物: {self.persons[most_similar_id]['name']} (ID: {most_similar_id}, 相似度: {max_similarity_float:.2f})")
            return most_similar_id
        else:
            self.logger.info(f"未找到相似度超过阈值的人物，最大相似度: {max_similarity_float:.2f}")
            return None
    
    def get_person(self, person_id: int) -> Optional[Dict[str, Any]]:
        """获取人物信息
        
        Args:
            person_id: 人物ID
            
        Returns:
            人物信息字典，如果不存在则返回None
        """
        return self.persons.get(person_id)
    
    def get_all_persons(self) -> Dict[int, Dict[str, Any]]:
        """获取所有人物信息
        
        Returns:
            所有人物信息的字典
        """
        return self.persons
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算两个向量的余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            余弦相似度，范围为[0, 1]
        """
        try:
            # 记录输入向量的形状和类型
            self.logger.debug(f"输入向量形状: vec1={vec1.shape}, vec2={vec2.shape}")
            self.logger.debug(f"输入向量类型: vec1={type(vec1)}, vec2={type(vec2)}")
            self.logger.debug(f"输入向量数据类型: vec1.dtype={vec1.dtype}, vec2.dtype={vec2.dtype}")
            
            # 确保向量形状匹配
            if vec1.shape != vec2.shape:
                self.logger.warning(f"向量形状不匹配: {vec1.shape} vs {vec2.shape}")
                # 如果形状不匹配，尝试调整形状
                if vec1.size == vec2.size:
                    vec1 = vec1.reshape(vec2.shape)
                    self.logger.debug(f"调整vec1形状为: {vec1.shape}")
                else:
                    # 如果无法调整，返回0表示不相似
                    self.logger.warning(f"向量大小不匹配，无法调整形状: {vec1.size} vs {vec2.size}")
                    return 0.0
            
            # 将向量展平并确保是一维数组
            vec1_flat = vec1.flatten()
            vec2_flat = vec2.flatten()
            self.logger.debug(f"展平后向量形状: vec1_flat={vec1_flat.shape}, vec2_flat={vec2_flat.shape}")
            self.logger.debug(f"展平后向量数据: vec1_flat前5个元素={vec1_flat[:5] if vec1_flat.size >= 5 else vec1_flat}")
            self.logger.debug(f"展平后向量数据: vec2_flat前5个元素={vec2_flat[:5] if vec2_flat.size >= 5 else vec2_flat}")
            
            # 计算余弦相似度
            dot = np.sum(vec1_flat * vec2_flat)
            norm1 = np.linalg.norm(vec1_flat)
            norm2 = np.linalg.norm(vec2_flat)
            
            # 记录中间计算结果
            self.logger.debug(f"点积结果: {dot}, 类型: {type(dot)}, 是否为数组: {isinstance(dot, np.ndarray)}")
            if isinstance(dot, np.ndarray):
                self.logger.debug(f"点积数组形状: {dot.shape}, 数据类型: {dot.dtype}")
            
            self.logger.debug(f"范数结果: norm1={norm1}, 类型: {type(norm1)}, norm2={norm2}, 类型: {type(norm2)}")
            if isinstance(norm1, np.ndarray):
                self.logger.debug(f"norm1数组形状: {norm1.shape}, 数据类型: {norm1.dtype}")
            if isinstance(norm2, np.ndarray):
                self.logger.debug(f"norm2数组形状: {norm2.shape}, 数据类型: {norm2.dtype}")
            
            # 确保所有值都是标量
            if isinstance(dot, np.ndarray):
                self.logger.debug(f"将点积从NumPy数组转换为标量，原始值: {dot}")
                dot = float(dot.item() if dot.size == 1 else dot.mean())
                self.logger.debug(f"转换后的点积值: {dot}")
            else:
                dot = float(dot)
                
            if isinstance(norm1, np.ndarray):
                self.logger.debug(f"将norm1从NumPy数组转换为标量，原始值: {norm1}")
                norm1 = float(norm1.item() if norm1.size == 1 else norm1.mean())
                self.logger.debug(f"转换后的norm1值: {norm1}")
            else:
                norm1 = float(norm1)
                
            if isinstance(norm2, np.ndarray):
                self.logger.debug(f"将norm2从NumPy数组转换为标量，原始值: {norm2}")
                norm2 = float(norm2.item() if norm2.size == 1 else norm2.mean())
                self.logger.debug(f"转换后的norm2值: {norm2}")
            else:
                norm2 = float(norm2)
            
            # 避免除以零
            if norm1 == 0.0 or norm2 == 0.0:
                self.logger.warning("向量范数为零，返回相似度0")
                return 0.0
                
            # 计算相似度，确保结果是标量值
            similarity = dot / (norm1 * norm2)
            self.logger.debug(f"初始相似度计算结果: {similarity}, 类型: {type(similarity)}")
            
            # 确保结果是标量值，而不是数组
            if isinstance(similarity, np.ndarray):
                self.logger.debug(f"相似度是NumPy数组，形状: {similarity.shape}, 数据类型: {similarity.dtype}, 值: {similarity}")
                if similarity.size == 1:
                    similarity = float(similarity.item())
                    self.logger.debug(f"将单元素数组转换为标量: {similarity}")
                else:
                    self.logger.warning(f"相似度结果是多元素数组，大小: {similarity.size}, 取平均值: {similarity.mean()}")
                    similarity = float(similarity.mean())
                    self.logger.debug(f"转换后的相似度值: {similarity}")
            else:
                # 确保即使不是数组也转换为Python原生浮点数
                similarity = float(similarity)
                self.logger.debug(f"确保相似度为Python原生浮点数: {similarity}")
            
            # 确保结果在[0, 1]范围内
            if similarity < 0.0 or similarity > 1.0:
                self.logger.warning(f"相似度超出[0,1]范围: {similarity}，将进行裁剪")
            
            final_similarity = float(max(0.0, min(1.0, similarity)))
            self.logger.debug(f"最终相似度结果: {final_similarity}, 类型: {type(final_similarity)}")
            return final_similarity
            
        except Exception as e:
            self.logger.error(f"计算余弦相似度时出错: {e}")
            import traceback
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            return 0.0