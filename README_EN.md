# MCP Agent Platform

## Project Introduction

This is a human-computer interaction system based on multi-agent architecture, integrating visual recognition, speech recognition, and speech synthesis capabilities. The system consists of multiple specialized agents working together to achieve a natural human-computer interaction experience.

## System Architecture

The system employs a distributed multi-agent architecture, utilizing the MCP (Multi-agent Communication Protocol) protocol for efficient communication and collaboration between agents.

### Agents

- **Brain Agent**
  - Responsible for core decision-making and coordination
  - Processes information from other agents
  - Integrates Ollama large model API for multimodal understanding and generation
  - Manages agent states and task scheduling

- **Eye Agent**
  - Processes visual input
  - Implements face detection and recognition
  - Supports real-time video stream processing
  - Generates image analysis results

- **Ear Agent**
  - Processes audio input
  - Implements speech recognition
  - Supports real-time audio stream processing
  - Provides noise suppression and signal enhancement

- **Mouth Agent**
  - Responsible for audio output
  - Implements speech synthesis
  - Supports emotional speech synthesis
  - Provides natural voice interaction experience

### Communication Mechanism

The system uses a WebSocket-based real-time communication mechanism, implementing message passing between agents through the MCP protocol:

1. **Message Types**
   - Text Message (TextMessage)
   - Image Message (ImageMessage)
   - Audio Message (AudioMessage)
   - Command Message (CommandMessage)
   - Status Message (StatusMessage)

2. **Message Routing**
   - Message routing based on sender and receiver IDs
   - Supports broadcast and point-to-point communication
   - Implements reliable message delivery and confirmation mechanisms

3. **State Management**
   - Real-time monitoring of agent states
   - Dynamic allocation of system resources
   - Task queue priority management

### Technical Principles

#### Face Recognition Technology

The system uses deep learning models to implement face recognition functionality:

1. **Face Detection**
   - Uses MTCNN (Multi-task Cascaded Convolutional Networks)
   - Implements face detection and landmark localization through P-Net, R-Net, and O-Net
   - Processes video streams in real-time, supporting multi-face detection

2. **Feature Extraction**
   - Employs FaceNet deep learning model to extract 128-dimensional face feature vectors
   - Uses Triplet Loss training strategy to optimize feature extraction
   - Implements face alignment and normalization

3. **Similarity Calculation**
   - Uses cosine similarity to calculate feature vector distances
   - Sets dynamic thresholds for identity matching
   - Implements feature vector indexing and fast retrieval

#### Speech Processing Technology

1. **Speech Recognition**
   - Uses Wav2Vec pre-trained model for feature extraction
   - Employs CTC (Connectionist Temporal Classification) decoding algorithm
   - Integrates Chinese speech recognition model with real-time transcription

2. **Speech Synthesis**
   - Implements end-to-end speech synthesis based on FastSpeech2
   - Uses HiFiGAN vocoder for high-quality audio generation
   - Supports emotion control and speech rate adjustment

#### Multimodal Processing

1. **Feature Fusion**
   - Implements multimodal fusion of visual and speech features
   - Uses Attention mechanism for cross-modal alignment
   - Supports collaborative understanding of multimodal information

2. **Context Management**
   - Maintains multi-turn dialogue history
   - Implements cross-modal information correlation analysis
   - Updates dialogue state dynamically

### Large Model Integration

The system integrates the Ollama large model API to achieve multimodal intelligent processing. Different models are configured based on task types:

1. **Model Configuration**
   - Text Processing: Uses qwen2 model
   - Image Processing: Uses gemma3:4b model with multimodal support
   - Audio Processing: Uses qwen2 model with temperature parameter set to 0.5

2. **Features Implementation**
   - **Image Understanding**
     - Scene analysis and object recognition
     - Facial feature extraction and emotion analysis
     - Image description generation

   - **Dialogue Generation**
     - Context-aware dialogue management
     - Multi-turn dialogue history maintenance
     - Personalized response generation

   - **Multimodal Fusion**
     - Combined understanding of image and text
     - Bidirectional conversion between speech and text
     - Comprehensive analysis of multimodal information

3. **Configuration Example**
```python
# Ollama Model Configuration
OLLAMA_BASE_URL = "http://127.0.0.1:11434"

# Model Configuration for Different Task Types
MODEL_CONFIG = {
    "text": {
        "model": "qwen2",  # Text processing model
        "params": {}
    },
    "image": {
        "model": "gemma3:4b",  # Image processing model
        "params": {},
        "multimodal": True
    },
    "audio": {
        "model": "qwen2",  # Audio processing model
        "params": {"temperature": 0.5}
    }
}
```

### Core Features

1. **Face Recognition**
   - Real-time face detection and recognition
   - Person information database management
   - Facial feature extraction and matching
   - Stranger recognition and recording

2. **Voice Interaction**
   - Chinese speech recognition
   - Speech synthesis output
   - Real-time voice dialogue
   - Emotional speech synthesis

3. **Web Interface**
   - Visual robot interface
   - Real-time status display
   - Interactive control panel
   - System monitoring dashboard

## Installation Guide

### Requirements

- Python 3.10+
- Windows/Linux/MacOS

### Installation Steps

1. Clone the project
```bash
git clone [repository-url]
cd mcpTest
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

### Configuration

The following parameters can be configured in `config.py`:

- Server configuration
- Agent parameters
- Model settings
- Speech recognition parameters

## Usage Guide

### Start the System

1. Run the main program
```bash
python main.py
```

2. Access the Web interface
```
http://localhost:8070
```

### Features Usage

1. **Face Recognition**
   - The system automatically detects and recognizes faces in the camera
   - First-time recognized faces will be automatically recorded

2. **Voice Interaction**
   - The system supports Chinese speech recognition
   - You can dialogue with the system through voice

## Tech Stack

- **Backend**
  - Python
  - FastAPI
  - WebSocket
  - OpenCV
  - SpeechRecognition
  - pyttsx3

- **Frontend**
  - HTML/CSS
  - JavaScript
  - WebSocket

## Directory Structure

```
├── config.py           # Configuration file
├── main.py            # Main program
├── requirements.txt   # Dependencies list
├── src/
│   ├── agents/       # Agent implementations
│   ├── brain/        # Brain logic
│   ├── platform/     # Platform core
│   ├── utils/        # Utility functions
│   └── web/          # Web service
├── static/           # Static resources
└── templates/        # Page templates
```