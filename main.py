from fastapi import FastAPI, Request, UploadFile, File
from contextlib import asynccontextmanager
from utils.queue import TaskQueue, QueueNode
from datetime import datetime
from dotenv import load_dotenv
import asyncio
import os
import logging

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"

async def worker(state):
    '''
        Persistent worker which asyncrhonously enqueues tasks to the queue without race condition
    '''
    
    logger = logging.getLogger("queue_worker")
    
    while True:
        state.queue_event.clear()
        while state.queue.head is None:
            state.isbusy = False
            logger.info(f'Task Queue is Empty. Worker Going to Sleep')
            await state.queue_event.wait()
            state.queue_event.clear()
        
        state.isbusy = True
        node = state.queue.pop()
        filename = node.process_name
        script_text = node.file_bytes.decode('utf-8')
        logger.info(script_text)
        with open('temp.py', 'w', encoding='utf-8') as f:
            f.write(script_text)
        logger.info(f'Executing Script:{filename}')
        try:
            process = await asyncio.create_subprocess_exec(
                state.python_path,
                'temp.py', stdout = asyncio.subprocess.PIPE, stdin = asyncio.subprocess.PIPE)
            logger.info(f'Starting {filename} at {datetime.now()}')
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
    app.state.queue_event = asyncio.Event()
    
    main_worker = asyncio.create_task(worker(app.state))
    
    yield
    
    main_logger.info("FastAPI Python Task Queue Server Shutting Down...")
    main_worker.cancel()

app = FastAPI(lifespan=lifespan)

@app.post("/add_task/")
async def add_task_to_queue(request: Request, file: UploadFile = File(...)):
    logger = logging.getLogger("queue_app")
    print(file.filename)
    filename = file.filename
    file_bytes = await file.read()
    
    request.app.state.queue.push(QueueNode(filename, file_bytes))
    logger.info(f'Enqueued new script: {filename}')
    request.app.state.queue.dump()
    was_busy = request.app.state.isbusy
    request.app.state.queue_event.set()

    if not was_busy:
        return {"status": "executing"}
    return {"status": "queued"}

@app.get("/queue_length")
async def get_queue_length(request: Request):
    return len(request.app.state.queue)