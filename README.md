# AI Component for Thesis Project

This repository contains the AI component for the thesis project. It implements a vision-language model based on Qwen2-VL-2B-Instruct for image analysis and processing.

## Features

- Integration with NATS for message streaming
- RabbitMQ support for message queuing
- Local model caching and loading
- GPU acceleration support (CUDA)
- Automatic device detection (CPU/GPU)

## Technical Stack

- Python 3.12
- PyTorch
- Transformers (Hugging Face)
- NATS
- RabbitMQ
- Qwen2-VL-2B-Instruct model

## Requirements

- Python 3.12+
- CUDA support (optional, for GPU acceleration)
- At least 8GB RAM
- Disk space for model storage (~5GB)

## Installation

1. Create a virtual environment:
```bash
python -m venv myvenv
```

2. Activate the virtual environment:
```bash
# Windows
myvenv\Scripts\activate

# Linux/Mac
source myvenv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env-clear` to `.env` and fill in your configuration values:
```bash
cp .env-clear .env
```

## Configuration

The application uses environment variables for configuration. Create a `.env` file with the following parameters:

- `NATS_HOST` - NATS server host
- `NATS_PORT` - NATS server port
- `NATS_STREAM` - NATS stream name
- `RABBIT_HOST` - RabbitMQ host
- `RABBIT_PORT` - RabbitMQ port
- `RABBIT_USERNAME` - RabbitMQ username
- `RABBIT_PASSWORD` - RabbitMQ password
- `RABBIT_QUEUE_NAME` - RabbitMQ queue name

## Model Information

The project uses the Qwen2-VL-2B-Instruct model, which is automatically downloaded and cached locally in the `local_model` directory. The model supports both CPU and GPU execution, with automatic device detection.

## Development

- The main AI server logic is in `ai_server.py`
- NATS integration is handled by `nats_decorator.py`
- RabbitMQ integration is in `rabbit.py`
- Main application entry point is `main.py`