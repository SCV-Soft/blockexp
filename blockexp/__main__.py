import asyncio

from blockexp import init_app

app = asyncio.run(init_app())

if __name__ == '__main__':
    app.serve()
