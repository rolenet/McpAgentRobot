"""
MCP协议实现
"""
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

class MCPMessage:
    """MCP协议消息基类"""
    
    def __init__(self, 
                 message_type: str,
                 sender_id: str,
                 receiver_id: str,
                 content: Dict[str, Any],
                 message_id: Optional[str] = None):
        self.message_id = message_id or str(uuid.uuid4())
        self.message_type = message_type
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.content = content
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """将消息转换为字典"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "timestamp": self.timestamp,
            "protocol": "MCP/1.0"
        }
    
    def to_json(self) -> str:
        """将消息转换为JSON字符串"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """从字典创建消息"""
        return cls(
            message_type=data["message_type"],
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            content=data["content"],
            message_id=data.get("message_id")
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MCPMessage':
        """从JSON字符串创建消息"""
        data = json.loads(json_str)
        return cls.from_dict(data)


class TextMessage(MCPMessage):
    """文本消息"""
    
    def __init__(self, sender_id: str, receiver_id: str, text: str, message_id: Optional[str] = None):
        super().__init__(
            message_type="text",
            sender_id=sender_id,
            receiver_id=receiver_id,
            content={"text": text},
            message_id=message_id
        )
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message_type": self.message_type,
            "content": self.content
        }


class ImageMessage(MCPMessage):
    """图像消息"""
    
    def __init__(self, sender_id: str, receiver_id: str, image_data: str, 
                 format: str = "base64", person_name: Optional[str] = None, message_id: Optional[str] = None):
        content = {"image_data": image_data, "format": format}
        if person_name is not None:
            content["person_name"] = person_name
            
        super().__init__(
            message_type="image",
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            message_id=message_id
        )


class AudioMessage(MCPMessage):
    """音频消息"""
    
    def __init__(self, sender_id: str, receiver_id: str, audio_data: str, 
                 format: str = "base64", message_id: Optional[str] = None):
        super().__init__(
            message_type="audio",
            sender_id=sender_id,
            receiver_id=receiver_id,
            content={"audio_data": audio_data, "format": format},
            message_id=message_id
        )


class CommandMessage(MCPMessage):
    """命令消息"""
    
    def __init__(self, sender_id: str, receiver_id: str, command: str, 
                 params: Dict[str, Any] = None, message_id: Optional[str] = None):
        super().__init__(
            message_type="command",
            sender_id=sender_id,
            receiver_id=receiver_id,
            content={"command": command, "params": params or {}},
            message_id=message_id
        )


class StatusMessage(MCPMessage):
    """状态消息"""
    
    def __init__(self, sender_id: str, receiver_id: str, status: str, 
                 details: Dict[str, Any] = None, message_id: Optional[str] = None):
        super().__init__(
            message_type="status",
            sender_id=sender_id,
            receiver_id=receiver_id,
            content={"status": status, "details": details or {}},
            message_id=message_id
        )