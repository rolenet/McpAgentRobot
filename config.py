"""
MCP智能体平台配置文件
"""
# 日志配置
LOG_LEVEL = "INFO"
# Ollama模型配置
OLLAMA_BASE_URL = "http://127.0.0.1:11434"

# 不同类型任务的模型配置
MODEL_CONFIG = {
    "text": {
        "model": "qwen2",  # 文本处理模型
        "params": {}
    },
    "image": {
        "model": "gemma3:4b",  # 图像处理模型
        "params": {},
        "multimodal": True
    },
    "audio": {
        "model": "qwen2",  # 音频处理模型
        "params": {"temperature": 0.5}
    }
}

# 默认模型（向后兼容）
OLLAMA_MODEL = MODEL_CONFIG["text"]["model"]
MULTIMODAL_SUPPORT = MODEL_CONFIG["image"]["multimodal"]  # 设置为True时使用支持图像的模型

# 服务器配置
SERVER_HOST = "localhost"
SERVER_PORT = 8000

# 客户端配置
CLIENT_HOST = "localhost"
CLIENT_PORT = 8001

# 智能体配置
AGENTS = {
    "brain": {
        "name": "Brain",
        "type": "brain",
        "host": "localhost",
        "port": 8010
    },
    "eye": {
        "name": "Eye",
        "type": "vision",
        "host": "localhost",
        "port": 8011
    },
    "ear": {
        "name": "Ear",
        "type": "audio_input",
        "host": "localhost",
        "port": 8012
    },
    "mouth": {
        "name": "Mouth",
        "type": "audio_output",
        "host": "localhost",
        "port": 8013
    }
}

# 添加语音识别配置
SPEECH_RECOGNITION = {
    "timeout": 3,           # 缩短超时时间
    "phrase_time_limit": 5, # 缩短单次识别时间
    "language": "zh-CN",    # 中文识别
    "retry_count": 3,       # 重试次数
    "retry_delay": 1        # 重试延迟（秒）
}
# Web服务配置
WEB_SERVER = {
    "host": "localhost",
    "port": 8070,
    "ws_path": "/ws"
}
# MCP协议配置
MCP_VERSION = "1.0"