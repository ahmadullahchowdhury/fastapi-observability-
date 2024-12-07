from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import logging
import random
import time
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, multiprocess
from prometheus_fastapi_instrumentator import Instrumentator
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create metrics
REQUESTS = Counter(
    "fastapi_requests_total",
    "Total count of requests by method and path",
    ["method", "path", "status"]
)

LATENCY = Histogram(
    "fastapi_requests_latency_seconds",
    "Request latency by method and path",
    ["method", "path"]
)

# Define startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up FastAPI application")
    yield
    # Shutdown
    logger.info("Shutting down FastAPI application")

app = FastAPI(lifespan=lifespan)

# Initialize Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

# Example data store
todos: List[Dict] = []

@app.get("/")
async def read_root():
    REQUESTS.labels(method="GET", path="/", status=200).inc()
    logger.info("Root endpoint accessed")
    return {"status": "healthy"}

@app.get("/todos")
async def get_todos():
    start_time = time.time()
    logger.info("Fetching all todos")
    
    # Simulate random latency
    time.sleep(random.uniform(0.1, 0.5))
    
    REQUESTS.labels(method="GET", path="/todos", status=200).inc()
    LATENCY.labels(method="GET", path="/todos").observe(time.time() - start_time)
    
    return todos

@app.post("/todos")
async def create_todo(title: str):
    start_time = time.time()
    logger.info(f"Creating new todo: {title}")
    
    if not title:
        REQUESTS.labels(method="POST", path="/todos", status=400).inc()
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    todo = {"id": len(todos) + 1, "title": title, "completed": False}
    todos.append(todo)
    
    REQUESTS.labels(method="POST", path="/todos", status=201).inc()
    LATENCY.labels(method="POST", path="/todos").observe(time.time() - start_time)
    
    return todo

@app.get("/metrics")
async def metrics():
    return generate_latest()

@app.get("/error")
async def trigger_error():
    logger.error("Simulated error endpoint accessed")
    REQUESTS.labels(method="GET", path="/error", status=500).inc()
    raise HTTPException(status_code=500, detail="Simulated error")