from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from utils.queue import TaskQueue, QueueNode
from datetime import datetime
from dotenv import load_dotenv
import asyncio
import os
import logging

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"

async def worker(state):
    logger = logging.getLogger("queue_worker")
    state.isbusy = True

    while state.queue.head is not None:
        node = state.queue.pop()
        filename = node.process_name
        logger.info(f'Executing Script:{filename}')
        try:
            process = await asyncio.create_subprocess_exec(
                state.python_path,
                filename, stdout = asyncio.subprocess.PIPE, stdin = asyncio.subprocess.PIPE)
            print(f'Starting {filename} at {datetime.now()}')
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f'Succesfully finished script {filename} with return code 0')
                if stdout:
                    logger.debug(f'[{filename}]  STDOUT]: {stdout.decode()}')
            else:
                logger.error(f'Script {filename} failed with return code {process.returncode}')
                if stderr:
                    logger.error(f'[{filename} ERROR]: {stderr.decode()}')
                    
        except Exception as e:
            logger.exception(
                f"Unexpected exception during execution of {filename}: {e}"
            )
    state.isbusy = False
    logger.info("Task queue is empty. Worker going to sleep.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()    
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler("queue_system.log"),  # Persists logs to a file
            logging.StreamHandler(),  # Standard out to terminal
        ]
    )
    main_logger = logging.getLogger("queue_app")
    main_logger.info("FastAPI Python Task Queue Server Starting Up...")
    python_path = os.getenv('PYTHON_PATH')
    if not python_path:
        main_logger.critical("Failed to start: PYTHON_PATH environment variable is missing!")
        raise RuntimeError("PYTHON_PATH environment variable is missing")
    app.state.python_path = python_path
    app.state.queue = TaskQueue()
    app.state.isbusy = False
    yield
    
    main_logger.info("FastAPI Python Task Queue Server Shutting Down...")

app = FastAPI(lifespan=lifespan)

@app.post("/add_task/")
async def add_task_to_queue(request: Request, data: dict):
    logger = logging.getLogger("queue_app")
    filename = data.get('filename')
    if os.path.exists(filename):
        request.app.state.queue.push(QueueNode(filename))
        logger.info(f'Enqueued new script: {filename}')
        request.app.state.queue.dump()

        if not request.app.state.isbusy:
            logger.info("Worker is idle. Spawning background task.")
            asyncio.create_task(worker(request.app.state))
            return {"status": "executing"}
        
        logger.info("Worker is busy. Task will stay in FIFO order.")
        return {"status":"queued"}
    else:
        logger.warning(f"Rejected task submission. File does not exist: {filename}")
        return {"Error": "File DNE"}

@app.get("/queue_length")
async def get_queue_length(request: Request):
    return len(request.app.state.queue)