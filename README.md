# MCP智能体平台 / MCP Agent Platform

## 项目简介 / Project Introduction

这是一个基于多智能体架构的人机交互系统，集成了视觉识别、语音识别和语音合成等功能。系统由多个专门的智能体协同工作，实现了自然的人机交互体验。

This is a human-computer interaction system based on multi-agent architecture, integrating visual recognition, speech recognition, and speech synthesis capabilities. The system consists of multiple specialized agents working together to achieve a natural human-computer interaction experience.

## 系统架构 / System Architecture

系统由以下主要组件构成 / The system consists of the following main components:

### 智能体 / Agents

- **大脑智能体 (Brain Agent)**
  - 负责系统的核心决策和协调
  - 处理来自其他智能体的信息
  - Responsible for core decision-making and coordination
  - Processes information from other agents

- **视觉智能体 (Eye Agent)**
  - 处理视觉输入
  - 实现人脸检测和识别
  - Processes visual input
  - Implements face detection and recognition

- **听觉智能体 (Ear Agent)**
  - 处理音频输入
  - 实现语音识别
  - Processes audio input
  - Implements speech recognition

- **发声智能体 (Mouth Agent)**
  - 负责语音输出
  - 实现语音合成
  - Responsible for audio output
  - Implements speech synthesis

### 核心功能 / Core Features

1. **人脸识别 / Face Recognition**
   - 实时人脸检测和识别
   - 人物信息数据库管理
   - Real-time face detection and recognition
   - Person information database management

2. **语音交互 / Voice Interaction**
   - 中文语音识别
   - 语音合成输出
   - Chinese speech recognition
   - Speech synthesis output

3. **Web界面 / Web Interface**
   - 可视化机器人界面
   - 实时状态显示
   - Visual robot interface
   - Real-time status display

## 安装说明 / Installation Guide

### 环境要求 / Requirements

- Python 3.10+
- Windows/Linux/MacOS

### 安装步骤 / Installation Steps

1. 克隆项目 / Clone the project
```bash
git clone [repository-url]
cd mcpTest
```

2. 安装依赖 / Install dependencies
```bash
pip install -r requirements.txt
```

### 配置说明 / Configuration

在`config.py`中可以配置以下参数 / The following parameters can be configured in `config.py`:

- 服务器配置 / Server configuration
- 智能体参数 / Agent parameters
- 模型设置 / Model settings
- 语音识别参数 / Speech recognition parameters

## 使用说明 / Usage Guide

### 启动系统 / Start the System

1. 运行主程序 / Run the main program
```bash
python main.py
```

2. 访问Web界面 / Access the Web interface
```
http://localhost:8070
```

### 功能使用 / Features Usage

1. **人脸识别 / Face Recognition**
   - 系统会自动检测和识别摄像头中的人脸
   - 首次识别的人脸会被自动记录
   - The system automatically detects and recognizes faces in the camera
   - First-time recognized faces will be automatically recorded

2. **语音交互 / Voice Interaction**
   - 系统支持中文语音识别
   - 可以通过语音与系统进行对话
   - The system supports Chinese speech recognition
   - You can dialogue with the system through voice

## 技术栈 / Tech Stack

- **后端 / Backend**
  - Python
  - FastAPI
  - WebSocket
  - OpenCV
  - SpeechRecognition
  - pyttsx3

- **前端 / Frontend**
  - HTML/CSS
  - JavaScript
  - WebSocket

## 目录结构 / Directory Structure

```
├── config.py           # 配置文件 / Configuration file
├── main.py            # 主程序 / Main program
├── requirements.txt   # 依赖清单 / Dependencies list
├── src/
│   ├── agents/       # 智能体实现 / Agent implementations
│   ├── brain/        # 大脑逻辑 / Brain logic
│   ├── platform/     # 平台核心 / Platform core
│   ├── utils/        # 工具函数 / Utility functions
│   └── web/          # Web服务 / Web service
├── static/           # 静态资源 / Static resources
└── templates/        # 页面模板 / Page templates
```