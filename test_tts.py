"""
测试TTS语音播放功能
"""
import pyttsx3
import time
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("TTS-Test")

def test_tts():
    """测试TTS引擎"""
    try:
        logger.info("开始初始化TTS引擎")
        engine = pyttsx3.init()
        
        # 获取可用的语音
        voices = engine.getProperty('voices')
        logger.info(f"可用语音数量: {len(voices)}")
        for i, voice in enumerate(voices):
            logger.info(f"语音 {i}: ID={voice.id}, Name={voice.name}, Languages={voice.languages}")
        
        # 设置语音属性
        engine.setProperty('rate', 150)  # 语速
        engine.setProperty('volume', 0.9)  # 音量
        
        # 尝试设置中文语音
        chinese_voice = None
        for voice in voices:
            if 'chinese' in voice.name.lower() or 'zh' in voice.id.lower():
                chinese_voice = voice.id
                break
        
        if chinese_voice:
            logger.info(f"设置中文语音: {chinese_voice}")
            engine.setProperty('voice', chinese_voice)
        
        # 测试播放
        test_text = "这是一个测试消息，测试语音播放功能是否正常。"
        logger.info(f"准备播放测试语音: {test_text}")
        
        engine.say(test_text)
        logger.info("调用runAndWait开始播放")
        engine.runAndWait()
        logger.info("语音播放完成")
        
        # 再测试一次英文
        test_text_en = "This is a test message for speech synthesis."
        logger.info(f"准备播放英文测试语音: {test_text_en}")
        
        engine.say(test_text_en)
        logger.info("调用runAndWait开始播放")
        engine.runAndWait()
        logger.info("英文语音播放完成")
        
        return True
    except Exception as e:
        logger.error(f"TTS测试失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("开始TTS测试")
    result = test_tts()
    logger.info(f"TTS测试结果: {'成功' if result else '失败'}")