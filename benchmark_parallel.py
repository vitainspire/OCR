import asyncio
import base64
import time
import json
import os
import sqlite3
from pathlib import Path
import aiohttp
from PIL import Image
import io

SERVER_IP = "13.62.96.5"
DOOR_1_URL = f"http://{SERVER_IP}:8000/v1/chat/completions"
DOOR_2_URL = f"http://{SERVER_IP}:8001/v1/chat/completions"

IMAGE_DIR = r"E:\Downloads\images-for-testing"

# ======================================================================
# The Ultimate Two-Door Parallel Benchmark (Crash-Proof Edition)
# ======================================================================

def init_db():
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS jobs
                 (id TEXT PRIMARY KEY, type TEXT, input TEXT, status TEXT, result_text TEXT, time REAL, tokens INTEGER, tps REAL)''')
    conn.commit()
    return conn

def save_result(task_id, result_text, elapsed, tokens, tps):
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute("UPDATE jobs SET status='COMPLETED', result_text=?, time=?, tokens=?, tps=? WHERE id=?", 
              (result_text, elapsed, tokens, tps, task_id))
    conn.commit()
    conn.close()

def encode_image(image_path):
    with Image.open(image_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        max_size = 1024
        if img.width > max_size:
            ratio = max_size / img.width
            new_size = (max_size, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=85)
        return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

async def process_ocr(session, image_path, task_id):
    """Sends Image to Door 1 (OCR)"""
    b64_img = encode_image(image_path)
    filename = Path(image_path).name
    
    payload = {
        "model": "ocr-engine",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}},
                {"type": "text", "text": "Extract all text from this image exactly as written."}
            ]
        }],
        "max_tokens": 1024,
        "temperature": 0.0
    }
    
    start_time = time.time()
    try:
        async with session.post(DOOR_1_URL, json=payload, timeout=300) as response:
            result = await response.json()
            elapsed = time.time() - start_time
            text = result["choices"][0]["message"]["content"].strip()
            tokens = result.get("usage", {}).get("completion_tokens", 0)
            tps = tokens / elapsed if elapsed > 0 else 0
            print(f"[Door 1] Task {task_id} Completed in {elapsed:.2f} seconds! ({tps:.1f} tokens/sec)")
            save_result(task_id, text, elapsed, tokens, tps)
            return {"type": "OCR", "id": task_id, "time": elapsed, "text": text, "tokens": tokens, "tps": tps}
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[Door 1] Task {task_id} FAILED after {elapsed:.2f}s: {e}")
        return None

async def process_text(session, prompt, task_id):
    """Sends Lesson Plan Query to Door 2 (Text)"""
    payload = {
        "model": "text-engine",
        "messages": [
            {"role": "system", "content": "You are a creative brainstorming assistant for a veteran 5th-grade science teacher. The teacher already knows the science facts. Your ONLY job is to give them wildly creative, out-of-the-box teaching ideas to captivate students."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4096,
        "temperature": 0.7
    }
    
    start_time = time.time()
    try:
        async with session.post(DOOR_2_URL, json=payload, timeout=300) as response:
            result = await response.json()
            elapsed = time.time() - start_time
            text = result["choices"][0]["message"]["content"].strip()
            tokens = result.get("usage", {}).get("completion_tokens", 0)
            tps = tokens / elapsed if elapsed > 0 else 0
            print(f"[Door 2] Task {task_id} Completed in {elapsed:.2f} seconds! ({tps:.1f} tokens/sec)")
            save_result(task_id, text, elapsed, tokens, tps)
            return {"type": "TEXT", "id": task_id, "time": elapsed, "text": text, "tokens": tokens, "tps": tps}
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[Door 2] Task {task_id} FAILED after {elapsed:.2f}s: {e}")
        return None

async def main():
    print(f"Starting Crash-Proof Parallel Benchmark on AWS Server {SERVER_IP}...")
    print("------------------------------------------------------------------")
    
    # 1. Initialize DB and Grab files
    conn = init_db()
    c = conn.cursor()
    
    image_paths = [os.path.join(IMAGE_DIR, f) for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    print(f"Found {len(image_paths)} images for Door 1.")
    
    text_queries = [
        "Brainstorm a 45-minute lesson for Motion (Physics). DO NOT explain the basic science facts, I already know them. I want a beautifully formatted, highly detailed lesson plan that contains ALL of the following: 1) A crazy 'Hook'. 2) A captivating short story. 3) Multiple real-life examples of the subtopics. 4) A unique hands-on physical experiment. 5) A fun interactive activity. 6) A high-energy physical game. NO SCREENS OR VIDEOS. Properly write and structure the content.",
        
        "Brainstorm a 45-minute lesson for the History of India, specifically the Maurya Empire. DO NOT explain the basic history facts, I already know them. I want a beautifully formatted, highly detailed lesson plan that contains ALL of the following: 1) A crazy 'Hook'. 2) A captivating short story. 3) Multiple real-life examples of the subtopics. 4) A unique hands-on physical experiment. 5) A fun interactive activity. 6) A high-energy physical game. NO SCREENS OR VIDEOS. Properly write and structure the content.",

        "Brainstorm a 45-minute lesson for Photosynthesis (Biology). DO NOT explain the basic science facts, I already know them. I want a beautifully formatted, highly detailed lesson plan that contains ALL of the following: 1) A crazy 'Hook'. 2) A captivating short story. 3) Multiple real-life examples of the subtopics. 4) A unique hands-on physical experiment. 5) A fun interactive activity. 6) A high-energy physical game. NO SCREENS OR VIDEOS. Properly write and structure the content."
    ]
    print(f"Found {len(text_queries)} complex lesson plans for Door 2.")
    
    # 2. Seed database
    for img_path in image_paths:
        task_id = f"OCR_{Path(img_path).name}"
        c.execute("INSERT OR IGNORE INTO jobs (id, type, input, status) VALUES (?, 'OCR', ?, 'PENDING')", (task_id, img_path))
        
    for i, prompt in enumerate(text_queries):
        task_id = f"TEXT_{i+1}"
        c.execute("INSERT OR IGNORE INTO jobs (id, type, input, status) VALUES (?, 'TEXT', ?, 'PENDING')", (task_id, prompt))
    conn.commit()
    
    # 3. Check for pending tasks
    c.execute("SELECT COUNT(*) FROM jobs WHERE status = 'COMPLETED'")
    completed_count = c.fetchone()[0]
    
    c.execute("SELECT id, type, input FROM jobs WHERE status = 'PENDING'")
    pending_tasks = c.fetchall()
    conn.close()
    
    if completed_count > 0:
        print(f"\n[INFO] Found {completed_count} previously completed tasks in database. Skipping them!")
    
    if not pending_tasks:
        print("\n[✔] All tasks are already completed! Check tasks.db for results.")
        return
        
    print(f"\nFIRING {len(pending_tasks)} PENDING REQUESTS SIMULTANEOUSLY... PLEASE WAIT!\n")
    
    global_start = time.time()
    
    # 4. Fire pending requests
    async with aiohttp.ClientSession() as session:
        tasks = []
        for task_id, t_type, t_input in pending_tasks:
            if t_type == 'OCR':
                tasks.append(process_ocr(session, t_input, task_id))
            elif t_type == 'TEXT':
                tasks.append(process_text(session, t_input, task_id))
            
        results = await asyncio.gather(*tasks)
        
    global_time = time.time() - global_start
    
    print("==================================================================")
    print(f"BENCHMARK COMPLETE in {global_time:.2f} seconds!")
    print("==================================================================")
    print("All results are safely stored in 'tasks.db'.")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
