import asyncio
from hello import main as document_handler
from appendaudio import main as general_handler

class MicroserviceRunner:
    def __init__(self, n):
        self.n = n

    async def run_document_handler(self):
        await document_handler()

    async def run_general_handler(self):
        await general_handler()

    def run(self):
        if self.n == 1:
            asyncio.run(self.run_document_handler())
        elif self.n == 2:
            asyncio.run(self.run_general_handler())
        else:
            print("Invalid input, please enter 1 or 2.")

if __name__ == "__main__":
    n = int(input("Enter your number (1 for document handler, 2 for general handler): "))
    runner = MicroserviceRunner(n)
    runner.run()
