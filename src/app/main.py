from fastapi import FastAPI, Depends, HTTPException, Request, WebSocket
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from . import models, database
from .database import get_db
from prometheus_fastapi_instrumentator import Instrumentator
from typing import List
import asyncio
import time
import httpx
import threading

app = FastAPI()

# Глобальный счетчик запросов для /items
request_counter = 0
request_counter_lock = threading.Lock()

instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)


@app.on_event("startup")
def startup():
    models.Base.metadata.create_all(bind=database.engine)


class ItemCreateUpdate(BaseModel):
    name: str
    description: str | None = None


class ItemResponse(ItemCreateUpdate):
    id: int

    class Config:
        orm_mode = True


@app.post("/items", response_model=ItemResponse)
def create_item(item: ItemCreateUpdate, db: Session = Depends(get_db)):
    db_item = models.Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.get("/items", response_model=List[ItemResponse])
def read_all_items(db: Session = Depends(get_db)):
    global request_counter
    
    with request_counter_lock:
        request_counter += 1
        current_request = request_counter
    
    # Каждый 100-й запрос будет иметь задержку в 100ms
    if current_request % 100 == 0:
        time.sleep(0.1)  # 100ms задержка для каждого 100-го запроса
    
    return db.query(models.Item).all()


@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id)
    if not item.first():
        raise HTTPException(status_code=404, detail="Item not found")
    item.delete()
    db.commit()
    return {"message": "Item deleted"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


load_test_active = False
load_test_task = None
test_results = {
    "start_time": None,
    "end_time": None,
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "current_rps": 0,
}


active_connections = []


@app.websocket("/loadtest-ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await asyncio.sleep(1)
            await websocket.send_json(
                {
                    **test_results,
                    "duration": (
                        time.time() - test_results["start_time"]
                        if test_results["start_time"]
                        else 0
                    ),
                }
            )
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        active_connections.remove(websocket)


async def broadcast_results():
    if not active_connections:
        return

    data = {
        **test_results,
        "duration": (
            time.time() - test_results["start_time"]
            if test_results["start_time"]
            else 0
        ),
    }

    tasks = [asyncio.create_task(conn.send_json(data)) for conn in active_connections]
    await asyncio.gather(*tasks, return_exceptions=True)


@app.get("/loadtest", response_class=HTMLResponse)
async def load_test_ui(request: Request):
    return f"""
    <html>
        <head>
            <title>Load Test /items Endpoint</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                .container {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #2c3e50; }}
                .form-group {{ margin-bottom: 15px; }}
                label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                input[type="number"] {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }}
                button {{ background-color: #3498db; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; font-size: 16px; }}
                button:hover {{ background-color: #2980b9; }}
                button:disabled {{ background-color: #95a5a6; cursor: not-allowed; }}
                .btn-danger {{ background-color: #e74c3c; }}
                .btn-danger:hover {{ background-color: #c0392b; }}
                .stats {{ margin-top: 20px; padding: 15px; background-color: white; border-radius: 4px; }}
                .metric {{ margin-bottom: 10px; }}
                .metric-value {{ font-weight: bold; }}
                .error {{ color: #e74c3c; }}
            </style>
            <script>
                let testActive = false;
                let resultsSocket = null;
                
                function startTest() {{
                    const rps = document.getElementById('rps').value;
                    if (!rps || rps <= 0) {{
                        alert('Please enter a valid RPS value');
                        return;
                    }}
                    
                    fetch('/start-loadtest?rps=' + rps)
                        .then(response => response.json())
                        .then(data => {{
                            if (data.success) {{
                                testActive = true;
                                updateUI();
                                connectToResults();
                            }} else {{
                                alert('Error: ' + data.message);
                            }}
                        }});
                }}
                
                function stopTest() {{
                    fetch('/stop-loadtest')
                        .then(response => response.json())
                        .then(data => {{
                            if (data.success) {{
                                testActive = false;
                                updateUI();
                                if (resultsSocket) resultsSocket.close();
                            }}
                        }});
                }}
                
                function connectToResults() {{
                    resultsSocket = new WebSocket('ws://' + window.location.host + '/loadtest-ws');
                    
                    resultsSocket.onmessage = function(event) {{
                        const data = JSON.parse(event.data);
                        updateStats(data);
                    }};
                    
                    resultsSocket.onclose = function() {{
                        console.log('WebSocket connection closed');
                    }};
                }}
                
                function updateStats(data) {{
                    document.getElementById('total-requests').textContent = data.total_requests;
                    document.getElementById('successful-requests').textContent = data.successful_requests;
                    document.getElementById('failed-requests').textContent = data.failed_requests;
                    document.getElementById('current-rps').textContent = data.current_rps.toFixed(2);
                    document.getElementById('duration').textContent = data.duration.toFixed(2);
                }}
                
                function updateUI() {{
                    document.getElementById('start-btn').disabled = testActive;
                    document.getElementById('stop-btn').disabled = !testActive;
                }}
                
                // Initialize UI
                document.addEventListener('DOMContentLoaded', function() {{
                    document.getElementById('stop-btn').disabled = true;
                }});
            </script>
        </head>
        <body>
            <div class="container">
                <h1>Load Test /items Endpoint</h1>
                
                <div class="form-group">
                    <label for="rps">Requests Per Second (RPS):</label>
                    <input type="number" id="rps" min="1" max="1000" value="10">
                </div>
                
                <div class="button-group">
                    <button id="start-btn" onclick="startTest()">Start Test</button>
                    <button id="stop-btn" class="btn-danger" onclick="stopTest()">Stop Test</button>
                </div>
                
                <div class="stats">
                    <h2>Test Results</h2>
                    <div class="metric">Total Requests: <span id="total-requests" class="metric-value">0</span></div>
                    <div class="metric">Successful Requests: <span id="successful-requests" class="metric-value">0</span></div>
                    <div class="metric">Failed Requests: <span id="failed-requests" class="metric-value">0</span></div>
                    <div class="metric">Current RPS: <span id="current-rps" class="metric-value">0</span></div>
                    <div class="metric">Test Duration (s): <span id="duration" class="metric-value">0</span></div>
                </div>
            </div>
        </body>
    </html>
    """


@app.get("/start-loadtest")
async def start_loadtest(rps: int):
    global load_test_active, load_test_task

    if load_test_active:
        return {"success": False, "message": "Load test is already running"}

    test_results.update(
        {
            "start_time": time.time(),
            "end_time": None,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "current_rps": 0,
        }
    )

    load_test_active = True
    load_test_task = asyncio.create_task(run_load_test(rps))
    return {"success": True}


@app.get("/stop-loadtest")
async def stop_loadtest():
    global load_test_active, load_test_task

    if not load_test_active:
        return {"success": False, "message": "No active load test"}

    load_test_active = False
    if load_test_task:
        load_test_task.cancel()
        try:
            await load_test_task
        except asyncio.CancelledError:
            pass
        load_test_task = None

    test_results["end_time"] = time.time()
    await broadcast_results()
    return {"success": True}


async def run_load_test(rps: int):
    async with httpx.AsyncClient() as client:
        interval = 1.0 / rps
        request_count = 0
        window_start = time.time()

        while load_test_active:
            start_time = time.time()
            try:
                response = await client.get(f"http://localhost:8000/items")
                if response.status_code == 200:
                    test_results["successful_requests"] += 1
                else:
                    test_results["failed_requests"] += 1
            except (httpx.ConnectError, httpx.TimeoutException):
                test_results["failed_requests"] += 1

            test_results["total_requests"] += 1
            request_count += 1

            current_time = time.time()
            elapsed = current_time - window_start
            if elapsed >= 1.0:
                test_results["current_rps"] = request_count / elapsed
                request_count = 0
                window_start = current_time
                asyncio.create_task(broadcast_results())

            if elapsed >= 0.5:
                asyncio.create_task(broadcast_results())

            processing_time = time.time() - start_time
            sleep_time = max(0, interval - processing_time)
            await asyncio.sleep(sleep_time)

    await broadcast_results()
