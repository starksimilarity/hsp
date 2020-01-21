import asyncio
import aio_pika
import logging


def on_message(message):
    with message.process():
        print(f"[x] {message.body}")

async def msg_consumer():
    conn = await aio_pika.connect_robust("amqp://guest:guest@172.17.0.2")
    channel = await conn.channel()
    msg_exchange = await channel.declare_exchange("messages", aio_pika.ExchangeType.FANOUT)
    queue = await channel.declare_queue("", exclusive=True)
    await queue.bind(msg_exchange)
    
    while True:
        await queue.consume(on_message)

async def cmd_consumer():
    conn = await aio_pika.connect_robust("amqp://guest:guest@172.17.0.2")
    channel = await conn.channel()
    cmd_exchange = await channel.declare_exchange("commands", aio_pika.ExchangeType.FANOUT)
    queue = await channel.declare_queue("", exclusive=True)
    await queue.bind(cmd_exchange) 
    while True:
        await queue.consume(on_message)

async def dbg_consumer():
    conn = await aio_pika.connect_robust("amqp://guest:guest@172.17.0.2")
    channel = await conn.channel()
    cmd_exchange = await channel.declare_exchange("debug", aio_pika.ExchangeType.FANOUT)
    queue = await channel.declare_queue("", exclusive=True)
    await queue.bind(cmd_exchange) 
    while True:
        await queue.consume(on_message)

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(
        cmd_consumer(),
        msg_consumer(),
        dbg_consumer()
        ))

if __name__ == "__main__":
    main()
