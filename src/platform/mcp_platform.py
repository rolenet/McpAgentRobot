"""
MCP平台管理类
"""
import asyncio
import logging
from typing import Dict, List

from src.agents.eye_agent import EyeAgent
from src.agents.ear_agent import EarAgent
from src.brain.brain_agent import BrainAgent
from src.agents.mouth_agent import MouthAgent

class MCPAgentPlatform:
    def __init__(self):
        self.logger = logging.getLogger("MCPAgentPlatform")
        self.agents = {}
        
    async def start(self):
        """启动所有智能体"""
        # 创建并启动大脑智能体
        brain = BrainAgent("brain", "localhost", 8010)
        await brain.start()
        self.agents["brain"] = brain
        self.logger.info("Started agent: brain")
        
        # 创建并启动耳朵智能体（先启动耳朵，确保获取麦克风资源）
        ear = EarAgent("ear", "localhost", 8012)
        await ear.start()
        self.agents["ear"] = ear
        self.logger.info("Started agent: ear")
        
        # 创建并启动眼睛智能体
        eye = EyeAgent("eye", "localhost", 8011)
        await eye.start()
        self.agents["eye"] = eye
        self.logger.info("Started agent: eye")
        
        # 创建并启动嘴巴智能体
        mouth = MouthAgent("mouth", "localhost", 8013)
        await mouth.start()
        self.agents["mouth"] = mouth
        self.logger.info("Started agent: mouth")
        
    async def stop(self):
        """停止所有智能体"""
        for agent_id, agent in self.agents.items():
            await agent.stop()
            self.logger.info(f"Stopped agent: {agent_id}")