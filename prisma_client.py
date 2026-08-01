import os
from prisma import Prisma
from dotenv import load_dotenv

load_dotenv()

prisma = Prisma()


def connect():
    if not prisma.is_connected():
        prisma.connect()


def disconnect():
    if prisma.is_connected():
        prisma.disconnect()


if __name__ == "__main__":
    connect()
    print("Prisma connected")
    disconnect()
