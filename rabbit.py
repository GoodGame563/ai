import asyncio
import aio_pika
import json
from transformers import TextIteratorStreamer
from ai_server import AiModel
from nats_decorator import NatsPublisher, NatsPublish
from logging import Logger
from threading import Thread

def truncate_strings(vector, max_length=2000):
    return [s[:max_length] for s in vector]
def merge_string_vectors(vector_of_vectors):
    return [' '.join(subvector) for subvector in vector_of_vectors]


class AsyncRabbitMQConsumer:
    def __init__(
        self,
        logger: Logger,
        host: str,
        username: str,
        password: str,
        port: int,
        ai_model: AiModel,
        nats: NatsPublisher,
        tokenizer,
        queue = "analysis_queue",
    ):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.logger = logger
        self.ai_model = ai_model
        self.tokenizer = tokenizer
        self.publish = nats
        self.connections = {}
        self.queue = queue

    async def connect(self, queue_name):
        connection = await aio_pika.connect_robust(
            host=self.host, login=self.username, password=self.password, port=self.port
        )
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue(queue_name, durable=True)
        return connection, queue

    async def generate(self, task_type: str, publisher: NatsPublish, messages: list):
        streamer = TextIteratorStreamer(self.tokenizer, True)
        thread = Thread(
            target=self.ai_model.generate_text, args=(messages, streamer, 1024)
        )
        thread.start()
        for new_text in streamer:
            if len(new_text) > 0:
                final_result = {
                    "message": new_text,
                    "task_type": task_type,
                }
                await publisher.publish(final_result)
        await publisher.publish({
                    "message": "__end__",
                    "task_type": task_type,
                    
                })
        



    async def process_message(self, message: aio_pika.IncomingMessage):
        async with message.process(requeue=True):
            try:
                body = message.body
                msg = json.loads(body)
                # self.logger.info(f"Received message: {msg}")

                task_type = msg.get("task_type")
                task_id = msg.get("task_id")
                payload = msg.get("payload", [])

                if not isinstance(payload, list):
                    raise ValueError("Payload must be a list of strings")

                publisher = NatsPublish(self.logger, self.publish, task_id)

                if task_type == "photo":
                    messages = [
                        {
                            "role": "system",
                            "content": "Вы — эксперт по анализу фотографий в карточках товаров на маркетплейсах, способный выявлять сильные и слабые стороны визуального контента с учетом его влияния на покупательское поведение. Ваши ответы всегда уникальны, избегают шаблонных фраз и повторов, а вместо отказов (например, 'я не могу') предлагают альтернативные подходы или уточнения."
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Проанализируйте фотографии первой карточки товара и сравните их с фотографиями конкурирующих карточек, которые имеют более высокие продажи на маркетплейсе. Определите конкретные недостатки наших фотографий, включая, но не ограничиваясь: низкое разрешение, плохое освещение, отсутствие демонстрации товара в использовании, слабую композицию или недостаточную привлекательность. Затем выделите сильные стороны фотографий конкурентов, такие как высокое качество изображения, разнообразие ракурсов, использование инфографики, lifestyle-съемка или акцент на ключевые преимущества товара. Составьте структурированный список критериев, по которым наши фотографии уступают, с пояснениями и конкретными примерами из фотографий конкурентов, демонстрирующими их преимущества (например, четкий показ текстуры, использование моделей, инфографика с характеристиками). Анализ должен быть точным, основанным исключительно на визуальных элементах, с акцентом на: 1) влияние фотографий на восприятие товара; 2) их роль в стимулировании покупки; 3) соответствие ожиданиям целевой аудитории. Избегайте шаблонных формулировок и повторов, предоставляя оригинальный и глубокий анализ. Если данных недостаточно (например, нет доступа к фотографиям), предложите, как уточнить запрос или какие аспекты можно дополнительно рассмотреть для более точного анализа."
                                }
                            ]
                        }
                    ]
                    payload = payload[0:3]
                    for i in range(len(payload)):
                        messages[1]["content"].append(
                            {
                                "type": "image",
                                "image": payload[i],
                            }
                        )
                    await self.generate(task_type, publisher, messages)
                elif task_type == "reviews":
                    messages = [
                        {
                            "role": "system",
                            "content": "Вы — эксперт по анализу отзывов покупателей на маркетплейсах, способный выявлять сильные и слабые стороны текстов отзывов с учетом их влияния на доверие и решение покупателей. Ваши ответы всегда уникальны, избегают шаблонных фраз и повторов, а вместо отказов (например, 'я не могу') предлагают альтернативные подходы или уточнения."
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Проанализируйте отзывы на первую карточку товара и сравните их с отзывами на карточки конкурентов, которые ранжируются выше на маркетплейсе. Выделите конкретные проблемы в наших отзывах, включая, но не ограничиваясь: негативные комментарии, недостаток детализации, низкие оценки, отсутствие или неэффективные ответы продавца. Затем определите сильные стороны отзывов конкурентов, такие как позитивный тон, подробные описания опыта использования, высокие оценки, активное и профессиональное взаимодействие продавца с покупателями. Составьте структурированный список критериев, по которым наши отзывы уступают, с пояснениями и конкретными примерами из отзывов конкурентов, демонстрирующими их преимущества (например, эмоциональные отзывы, конкретные детали, убедительные ответы продавца). Анализ должен быть объективным, основанным исключительно на текстах отзывов, с акцентом на: 1) доверие, которое отзывы вызывают у покупателей; 2) их влияние на решение о покупке; 3) качество взаимодействия продавца. Избегайте шаблонных формулировок и повторов, предоставляя оригинальный и глубокий анализ. Если данных недостаточно, предложите, как уточнить запрос для более точного анализа."
                                }
                            ]
                        }
                    ]
                    payload = merge_string_vectors(payload)
                    payload = payload[0:8]
                    payload = truncate_strings(payload, 2000)
                    for i in range(len(payload)):
                        if i == 0:
                            messages[1]["content"][0][
                                "text"
                            ] += f"\nОтзывы на первую карточку товара:\n{payload[i]}"
                        else:
                            messages[1]["content"][0][
                                "text"
                            ] += f"\nОтзывы на карточку конкурентов товара:\n{payload[i]}"

                    await self.generate(task_type, publisher, messages)
                elif task_type == "text":
                    messages = [
                        {
                            "role": "system",
                            "content": "Вы — эксперт по анализу текстов описаний товаров на маркетплейсах, способный выявлять сильные и слабые стороны текстов с учетом SEO, структуры и привлекательности для покупателей. Ваши ответы всегда уникальны, избегают шаблонных фраз и повторов, а вместо отказов (например, 'я не могу') предлагают альтернативные подходы или решения."
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Проанализируйте текст описания первой карточки товара и сравните его с текстами описаний конкурирующих карточек, которые ранжируются выше на маркетплейсе. Определите конкретные недостатки нашего описания, включая, но не ограничиваясь: низкую плотность ключевых слов, слабую структуру, отсутствие акцента на преимущества, недостаточную информативность или слабую привлекательность для покупателя. Составьте структурированный список критериев, по которым наше описание уступает, с пояснениями и конкретными примерами из описаний конкурентов, демонстрирующими их сильные стороны (например, удачное использование ключевых слов, четкие заголовки, эмоциональные триггеры). Анализ должен быть четким, основанным исключительно на текстовых данных, с акцентом на: 1) плотность и релевантность ключевых слов для SEO; 2) логичную и удобную структуру текста; 3) убедительность и привлекательность для целевой аудитории. Избегайте шаблонных формулировок и повторов, предоставляя оригинальный анализ. Если данных недостаточно, предложите, как можно уточнить запрос для более точного анализа."
                                }
                            ]
                        }
                    ]
                    for i in range(len(payload)):
                        if i == 0:
                            messages[1]["content"][0][
                                "text"
                            ] += f"\nОписание на первую карточку товара:\n{payload[i]}"
                        else:
                            messages[1]["content"][0][
                                "text"
                            ] += f"\nОписание на карточку конкурентов товара:\n{payload[i]}"
                    await self.generate(task_type, publisher, messages)
                else:
                    raise ValueError(f"Unknown task_type: {task_type}")

                self.logger.info(f"Generation successful for task_id: {task_id}")

            except Exception as e:
                self.logger.error(f"Error processing message: {str(e)}")
                raise

    async def start_consuming(self, queue_name):
        connection, queue = await self.connect(queue_name)
        await queue.consume(self.process_message)
        self.logger.info(f"Started consuming from {queue_name}")
        self.connections[queue_name] = connection
        return connection

    async def run(self):
        tasks = [self.start_consuming(self.queue)]
        connections = await asyncio.gather(*tasks)
        try:
            await asyncio.Event().wait()
        finally:
            for conn in connections:
                await conn.close()

    async def __del__(self):
        for conn in self.connections.values():
            if not conn.is_closed:
                await conn.close()