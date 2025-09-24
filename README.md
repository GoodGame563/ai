# AI Analysis Service (Thesis)

This repository implements the AI microservice for the thesis project: "Development of an analytics system for marketplace product grids using neural network technologies for automation and acceleration of assortment analysis".

## Purpose & Architecture

The AI service automates the analysis of product data from the Wildberries marketplace. It uses a vision-language neural network (Qwen2-VL-2B-Instruct) for image and text processing, providing insights for assortment optimization. The service is a Python microservice, communicating with other system components via NATS and RabbitMQ message brokers.

### Main Components
- `main.py`: Entry point, orchestrates startup, integration, and async event loop.
- `ai_server.py`: Implements the AI model logic, inference routines, and model loading/caching.
- `nats_decorator.py`: Handles NATS streaming for inter-service communication.
- `rabbit.py`: Manages RabbitMQ queues for task distribution and consumption.
- `local_model/`: Stores the Qwen2-VL-2B-Instruct model and tokenizer files (auto-downloaded).
- `requirements.txt`: All Python dependencies (PyTorch, Transformers, NATS, RabbitMQ, etc).

## Workflow
1. Receives analysis tasks via RabbitMQ (from API gateway).
2. Loads and caches the neural model (CPU/GPU auto-detection, CUDA support).
3. Processes product images and text, extracting features and generating analytics.
4. Publishes results to NATS for downstream consumption (API, web, DB).
5. Supports asynchronous task handling for scalability.

## Features
- Vision-language model for product analysis (Qwen2-VL-2B-Instruct)
- Automatic device selection (CPU/GPU)
- Asynchronous task handling (asyncio)
- Integration with message brokers (NATS, RabbitMQ)
- Local model caching for performance
- Logging via Python `logging` module

## Technical Stack
- Python 3.12+
- PyTorch
- Transformers (Hugging Face)
- NATS
- RabbitMQ
- Docker for containerization

## Requirements
- Python 3.12+
- CUDA support (optional, for GPU acceleration)
- At least 8GB RAM
- Disk space for model storage (~5GB)

## Installation & Usage
1. Create a virtual environment:
   ```powershell
   python -m venv myvenv
   myvenv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Copy `.env-clear` to `.env` and fill in broker credentials:
   - NATS and RabbitMQ connection details
   - Other required variables (see `.env-clear` for full list)
3. Download model files to `local_model/` (auto on first run).
4. Start the service:
   ```powershell
   python main.py
   ```

## Configuration
The application uses environment variables for configuration. Create a `.env` file with the following parameters:
- `NATS_HOST`, `NATS_PORT`, `NATS_STREAM`
- `RABBIT_HOST`, `RABBIT_PORT`, `RABBIT_USERNAME`, `RABBIT_PASSWORD`, `RABBIT_QUEUE_NAME`

## Model Information
- Qwen2-VL-2B-Instruct (Hugging Face Transformers)
- Supports image and text input
- Model files stored locally for speed

## Development Notes
- Main AI server logic is in `ai_server.py`
- NATS integration is handled by `nats_decorator.py`
- RabbitMQ integration is in `rabbit.py`
- All integration logic is asynchronous (asyncio)
- See thesis for detailed algorithm description and workflow diagrams
