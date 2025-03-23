"""
基础智能体类
"""
import asyncio
import json
import logging
from typing import Dict, Any, Callable, Coroutine, Optional, List
import websockets

from src.utils.mcp_protocol import MCPMessage

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class BaseAgent:
    """基础智能体类"""
    
    def __init__(self, agent_id: str, agent_type: str, host: str, port: int):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.host = host
        self.port = port
        self.logger = logging.getLogger(f"Agent:{agent_id}")
        self.connections = {}  # 存储与其他智能体的连接
        self.message_handlers = {}  # 消息处理器
        self.server = None
        self.is_running = False
        # 添加智能体地址映射
        self.agent_addresses = {}

    def get_agent_address(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取智能体的地址信息"""
        # 如果已经有连接，直接返回
        if agent_id in self.connections:
            return {"agent_id": agent_id, "connection": self.connections[agent_id]}
        
        # 如果有地址映射，返回地址信息
        if agent_id in self.agent_addresses:
            return self.agent_addresses[agent_id]
        
        # 默认地址映射
        default_addresses = {
            "brain": {"host": "localhost", "port": 8010},
            "eye": {"host": "localhost", "port": 8011},
            "ear": {"host": "localhost", "port": 8012},
            "mouth": {"host": "localhost", "port": 8013}
        }
        
        if agent_id in default_addresses:
            self.agent_addresses[agent_id] = default_addresses[agent_id]
            return default_addresses[agent_id]
        
        return None

    async def start(self):
        """启动智能体服务器"""
        self.is_running = True
        self.server = await websockets.serve(
            self._handle_connection, self.host, self.port
        )
        self.logger.info(f"Agent {self.agent_id} started on {self.host}:{self.port}")
        
        # 注册默认消息处理器
        self.register_handler("text", self._handle_text_message)
        self.register_handler("command", self._handle_command_message)
        self.register_handler("status", self._handle_status_message)
    
    async def stop(self):
        """停止智能体服务器"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        self.is_running = False
        self.logger.info(f"Agent {self.agent_id} stopped")
    
    async def connect_to_agent(self, agent_id: str, host: str, port: int):
        """连接到其他智能体"""
        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            try:
                uri = f"ws://{host}:{port}"
                connection = await websockets.connect(
                    uri,
                    ping_interval=20,  # 20秒发送一次心跳
                    ping_timeout=10    # 10秒内没有响应则断开
                )
                self.connections[agent_id] = connection
                self.logger.info(f"Connected to agent {agent_id} at {uri}")
                
                # 发送状态消息表明已连接
                status_msg = {
                    "message_type": "status",
                    "sender_id": self.agent_id,
                    "receiver_id": agent_id,
                    "content": {
                        "status": "connected",
                        "details": {
                            "agent_type": self.agent_type
                        }
                    }
                }
                await connection.send(json.dumps(status_msg))
                
                # 启动接收消息的任务
                asyncio.create_task(self._receive_messages(agent_id, connection))
                return True
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1}/{max_retries} failed to connect to agent {agent_id}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                
        return False
    
    async def _receive_messages(self, agent_id: str, connection):
        """接收来自特定连接的消息"""
        while True:
            try:
                message = await connection.recv()
                await self._process_message(message)
            except websockets.exceptions.ConnectionClosed:
                self.logger.info(f"Connection to agent {agent_id} closed")
                if agent_id in self.connections:
                    del self.connections[agent_id]
                # 尝试重新连接
                if await self.connect_to_agent(agent_id, self.host, self.port):
                    self.logger.info(f"Reconnected to agent {agent_id}")
                break
            except Exception as e:
                self.logger.error(f"Error receiving messages from {agent_id}: {e}")
                await asyncio.sleep(1)  # 避免过于频繁的错误日志
    
    async def _handle_connection(self, websocket, path):
        """处理新的WebSocket连接"""
        try:
            # 等待身份验证消息
            message = await websocket.recv()
            data = json.loads(message)
            
            if data.get("message_type") == "status" and data.get("content", {}).get("status") == "connected":
                sender_id = data.get("sender_id")
                self.connections[sender_id] = websocket
                self.logger.info(f"Agent {sender_id} connected")
                
                # 发送确认消息
                response = {
                    "message_type": "status",
                    "sender_id": self.agent_id,
                    "receiver_id": sender_id,
                    "content": {
                        "status": "accepted",
                        "details": {
                            "agent_type": self.agent_type
                        }
                    }
                }
                await websocket.send(json.dumps(response))
                
                # 处理后续消息
                while True:
                    message = await websocket.recv()
                    await self._process_message(message)
            else:
                self.logger.warning(f"Received invalid connection message: {data}")
                await websocket.close()
        except websockets.exceptions.ConnectionClosed:
            # 查找并移除断开的连接
            for agent_id, conn in list(self.connections.items()):
                if conn == websocket:
                    del self.connections[agent_id]
                    self.logger.info(f"Agent {agent_id} disconnected")
                    break
        except Exception as e:
            self.logger.error(f"Error handling connection: {e}")
    
    async def _process_message(self, message_data):
        """处理接收到的消息"""
        try:
            if isinstance(message_data, str):
                data = json.loads(message_data)
            else:
                data = message_data
            
            message_type = data.get("message_type")
            
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](data)
            else:
                self.logger.warning(f"No handler for message type: {message_type}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    async def send_message(self, receiver_id: str, message: Dict[str, Any]):
        """发送消息到指定智能体"""
        try:
            # self.logger.info(f"尝试发送消息到 {receiver_id}: {message}")
            # 获取接收者的地址
            receiver = self.get_agent_address(receiver_id)
            if not receiver:
                self.logger.error(f"未找到智能体: {receiver_id}")
                return False
            if isinstance(message, MCPMessage):
                message_data = message.to_json()
            elif isinstance(message, dict):
                # 确保消息包含必要字段
                if "sender_id" not in message:
                    message["sender_id"] = self.agent_id
                if "receiver_id" not in message:
                    message["receiver_id"] = receiver_id
                message_data = json.dumps(message)
            else:
                message_data = message
            
            if receiver_id in self.connections:
                try:
                    await self.connections[receiver_id].send(message_data)
                    # self.logger.info(f"消息已发送到 {receiver_id}")
                    return True
                except Exception as e:
                    self.logger.error(f"Error sending message to {receiver_id}: {e}")
                    return False
            else:
                # 尝试建立连接
                if "host" in receiver and "port" in receiver:
                    self.logger.info(f"尝试连接到智能体 {receiver_id} ({receiver['host']}:{receiver['port']})")
                    if await self.connect_to_agent(receiver_id, receiver["host"], receiver["port"]):
                        # 连接成功，重新尝试发送消息
                        return await self.send_message(receiver_id, message)
                    else:
                        self.logger.error(f"无法连接到智能体 {receiver_id}")
                        return False
                else:
                    self.logger.warning(f"No connection to agent {receiver_id} and no address information")
                    return False
            # self.logger.info(f"消息已发送到 {receiver_id}")
            return True
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            return False
    
    def register_handler(self, message_type: str, handler: Callable[[Dict[str, Any]], Coroutine]):
        """注册消息处理器"""
        self.message_handlers[message_type] = handler
        self.logger.info(f"Registered handler for message type: {message_type}")
    
    # 默认消息处理器
    async def _handle_text_message(self, message: Dict[str, Any]):
        """处理文本消息的默认方法"""
        self.logger.info(f"Received text message from {message['sender_id']}: {message['content'].get('text', '')}")
    
    async def _handle_command_message(self, message: Dict[str, Any]):
        """处理命令消息的默认方法"""
        command = message['content'].get('command', '')
        self.logger.info(f"Received command from {message['sender_id']}: {command}")
    
    async def _handle_status_message(self, message: Dict[str, Any]):
        """处理状态消息的默认方法"""
        status = message['content'].get('status', '')
        self.logger.info(f"Received status update from {message['sender_id']}: {status}")
        
        # 处理特定状态
        if status == "connected":
            self.logger.info(f"Agent {message['sender_id']} connected with type: "
                           f"{message['content'].get('details', {}).get('agent_type')}")
        elif status == "accepted":
            self.logger.info(f"Connection accepted by {message['sender_id']}")
        elif status == "disconnected":
            if message['sender_id'] in self.connections:
                del self.connections[message['sender_id']]
            self.logger.info(f"Agent {message['sender_id']} disconnected")
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """广播消息到所有连接的智能体"""
        results = []
        for agent_id in self.connections:
            result = await self.send_message(agent_id, message)
            results.append((agent_id, result))
        return results
    
    async def disconnect_from_agent(self, agent_id: str):
        """断开与指定智能体的连接"""
        if agent_id in self.connections:
            try:
                # 发送断开连接状态消息
                status_msg = {
                    "message_type": "status",
                    "sender_id": self.agent_id,
                    "receiver_id": agent_id,
                    "content": {
                        "status": "disconnected",
                        "details": {
                            "reason": "client_disconnect"
                        }
                    }
                }
                await self.send_message(agent_id, status_msg)
                
                # 关闭连接
                await self.connections[agent_id].close()
                del self.connections[agent_id]
                self.logger.info(f"Disconnected from agent {agent_id}")
                return True
            except Exception as e:
                self.logger.error(f"Error disconnecting from agent {agent_id}: {e}")
                return False
        return False
    
    async def disconnect_all(self):
        """断开与所有智能体的连接"""
        agent_ids = list(self.connections.keys())
        results = []
        for agent_id in agent_ids:
            result = await self.disconnect_from_agent(agent_id)
            results.append((agent_id, result))
        return results
    
    def get_connected_agents(self) -> List[str]:
        """获取所有已连接的智能体ID列表"""
        return list(self.connections.keys())
    
    def is_connected_to(self, agent_id: str) -> bool:
        """检查是否与指定智能体保持连接"""
        return agent_id in self.connections