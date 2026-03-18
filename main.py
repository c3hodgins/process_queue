from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from utils.queue import TaskQueue, QueueNode
from datetime import datetime
import asyncio
import os

async def worker(state):
    state.is_working = True

    while state.queue.head is not None:
        node = state.queue.pop()
        filename = node.process_name

        process = await asyncio.create_subprocess_exec(
            "/home/c3hod/pyproj/process_queue/.process_queue/bin/python",
            filename, stdout = asyncio.subprocess.PIPE, stdin = asyncio.subprocess.PIPE)
        print(f'Starting {filename} at {datetime.now()}')
        stdout, stderr = await process.communicate()

        print(f'File: {filename} finished at {datetime.now()}')
    state.is_working = False
    print(f'Queue is Empty')



@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.queue = TaskQueue()
    app.state.isbusy = False
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/add_task/")
async def add_task_to_queue(request: Request, data: dict):
    if os.path.exists(data['filename']):
        request.app.state.queue.push(QueueNode(data['filename']))
        request.app.state.queue.dump()

        if not request.app.state.isbusy:
            asyncio.create_task(worker(request.app.state))
            request.app.state.isbusy = True
            return {"status":"queued"}
    else:
        return {"Error":"File DNE"}

@app.get("/queue_length")
async def get_queue_length(request: Request):
    return len(request.app.state.queue)