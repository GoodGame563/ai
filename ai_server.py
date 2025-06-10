from transformers import (
    Qwen2VLForConditionalGeneration,
    AutoProcessor,
    TextIteratorStreamer,
)
from qwen_vl_utils import process_vision_info
import torch
from logging import Logger
import os


class AiModel:
    def __init__(self, logger: Logger):
        self.logger = logger
        min_pixels = 256 * 28 * 28
        max_pixels = 1280 * 28 * 28
        self.logger.info("Initializing AI model...")

        local_dir = "./local_model"
        model_name = "Qwen/Qwen2-VL-2B-Instruct"
        model_path = os.path.join(local_dir, model_name.replace('/', '_'))
        os.makedirs(model_path, exist_ok=True)

        # Проверка доступности CUDA
        if torch.cuda.is_available():
            device = "cuda"
            device_map = "auto"
            torch_dtype = torch.bfloat16
            self.logger.info("CUDA is available. Using GPU.")
        else:
            device = "cpu"
            device_map = {"": device}
            torch_dtype = torch.float32
            self.logger.info("CUDA is not available. Using CPU.")

        # Проверяем, есть ли модель локально
        if os.path.exists(os.path.join(model_path, "config.json")):
            self.logger.info(f"Loading model from local path: {model_path}")
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_path,
                torch_dtype=torch_dtype,
                device_map=device_map,
            )
            self.processor = AutoProcessor.from_pretrained(
                model_path,
                use_fast=True,
                min_pixels=min_pixels,
                max_pixels=max_pixels,
            )
        else:
            self.logger.info(f"Downloading model from HuggingFace: {model_name}")
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch_dtype,
                device_map=device_map,
            )
            self.model.save_pretrained(model_path)
            self.logger.info(f"Model saved to {model_path}")
            self.processor = AutoProcessor.from_pretrained(
                model_name,
                use_fast=True,
                min_pixels=min_pixels,
                max_pixels=max_pixels,
            )
            self.processor.save_pretrained(model_path)
            self.logger.info(f"Processor saved to {model_path}")
        self.logger.info("Model and processor initialized")

    def return_tokenizer(self):
        return self.processor.tokenizer

    def generate_text(
        self, messages: list, streamer: TextIteratorStreamer, max_tokens: int = 512
    ):
        self.logger.info("Starting generation")
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        self.logger.debug("Chat template applied")

        image_inputs, video_inputs = process_vision_info(messages)
        self.logger.debug("Vision info processed")

        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to("cuda")
        self.logger.debug("Inputs processed and moved to CUDA")

        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            streamer=streamer,
            temperature=0.7, 
            top_p=0.9,       
            top_k=50,        
            repetition_penalty=1.2, 
        )
        self.logger.info("Text generation completed")
        torch.cuda.empty_cache()
        self.logger.debug("CUDA cache cleared")
