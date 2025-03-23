import os
import sys
import asyncio
import logging

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request

from src.web.server import app
from src.platform.mcp_platform import MCPAgentPlatform

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

# 确保模板目录存在
templates_dir = os.path.join(current_dir, "templates")
os.makedirs(templates_dir, exist_ok=True)

# 确保静态文件目录存在
static_dir = os.path.join(current_dir, "static")
os.makedirs(static_dir, exist_ok=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 设置模板
templates = Jinja2Templates(directory=templates_dir)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 创建平台实例
platform = MCPAgentPlatform()

@app.on_event("startup")
async def startup_event():
    # 启动平台
    await platform.start()

@app.on_event("shutdown")
async def shutdown_event():
    # 关闭平台
    await platform.stop()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8070)