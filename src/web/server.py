from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi import Request
import asyncio
import json
import os

app = FastAPI()

# 获取当前文件所在目录的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

# 挂载静态文件
static_dir = os.path.join(base_dir, "mcpTest", "static")
os.makedirs(static_dir, exist_ok=True)

# 模板配置
templates_dir = os.path.join(base_dir, "mcpTest", "templates")
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# 存储所有 WebSocket 连接
# 全局变量，用于存储WebSocket连接
websocket_connections = set()
# 添加一个标志来跟踪服务器状态
server_running = True

@app.on_event("startup")
async def startup_event():
    global server_running
    server_running = True
    print("Web server started")

@app.on_event("shutdown")
async def shutdown_event():
    global server_running
    server_running = False
    print("Web server shutting down")

# 修改WebSocket处理部分
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_connections.add(websocket)
    print(f"WebSocket连接已建立，当前连接数: {len(websocket_connections)}")
    
    try:
        # 发送初始状态消息
        await websocket.send_text(json.dumps({
            "type": "status",
            "content": "connected"
        }))
        
        # 保持连接活跃
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                print(f"收到客户端消息: {message}")
                
                # 处理文本消息
                if message.get('type') == 'text':
                    # 转发消息给大脑智能体
                    try:
                        from src.brain.brain_agent import brain_instance
                        
                        if brain_instance:
                            # 创建一个新的消息对象，符合大脑智能体期望的格式
                            brain_message = {
                                'content': {'text': message['content']['text']},
                                'sender_id': message['sender_id'],
                                'receiver_id': message['receiver_id'],
                                'message_type': 'text'
                            }
                            
                            # 调用大脑的处理方法
                            await brain_instance._handle_text_message(brain_message)
                            
                            # 注意：大脑会将回复发送给mouth智能体，我们需要修改这部分逻辑
                        else:
                            print("未找到大脑智能体实例")
                            # 发送错误消息回客户端
                            error_message = {
                                "type": "chat",
                                "sender_id": "system",
                                "content": {
                                    "text": "大脑智能体未启动，无法处理消息"
                                }
                            }
                            await broadcast_message(error_message)
                    except Exception as e:
                        print(f"处理大脑消息时出错: {e}")
                        # 发送错误消息回客户端
                        error_message = {
                            "type": "chat",
                            "sender_id": "system",
                            "content": {
                                "text": f"处理消息时出错: {str(e)}"
                            }
                        }
                        await broadcast_message(error_message)
                
            except Exception as e:
                print(f"处理WebSocket消息时出错: {e}")
                break
                
    except Exception as e:
        print(f"WebSocket错误: {e}")
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)
        print(f"WebSocket连接已关闭，剩余连接数: {len(websocket_connections)}")

async def broadcast_message(message: dict):
    """广播消息到所有WebSocket连接"""
    if not websocket_connections:
        # print("没有活跃的WebSocket连接")
        return False
    
    # print(f"正在向{len(websocket_connections)}个连接广播消息")
    success = False
    
    # 使用列表复制，避免在迭代过程中修改集合
    for connection in list(websocket_connections):
        try:
            await connection.send_text(json.dumps(message))
            success = True
        except Exception as e:
            print(f"发送消息失败: {e}")
            if connection in websocket_connections:
                websocket_connections.remove(connection)
    
    return success