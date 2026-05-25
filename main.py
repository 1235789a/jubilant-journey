from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict
import json
import os

from scraper import RedditScraper
from analyzer import PainpointAnalyzer

app = FastAPI(title="海外痛点挖掘专家")

# 初始化模块
scraper = RedditScraper()
analyzer = PainpointAnalyzer()

# 确保静态文件目录存在
os.makedirs("static", exist_ok=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

class AnalyzeRequest(BaseModel):
    text: str
    title: str = ""
    score: int = 0
    num_comments: int = 0

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r") as f:
        return f.read()

@app.post("/api/analyze")
async def analyze_text(request: AnalyzeRequest):
    """分析单个帖子文本"""
    post = {
        "title": request.title,
        "text": request.text,
        "score": request.score,
        "num_comments": request.num_comments,
        "url": "",
        "subreddit": "manual_input",
        "top_comments": []
    }
    
    result = analyzer.analyze_post(post)
    if result is None:
        return {"status": "IGNORE", "reason": "No valid painpoint detected"}
    return {"status": "success", "data": result}

@app.get("/api/fetch")
async def fetch_and_analyze(subreddits: str = "programming, SaaS, startups"):
    """从 Reddit 抓取并分析帖子"""
    subreddit_list = [s.strip() for s in subreddits.split(",")]
    
    try:
        posts = scraper.fetch_hot_posts(subreddit_list, limit=30)
        painpoints = []
        
        for post in posts:
            result = analyzer.analyze_post(post)
            if result:
                painpoints.append(result)
        
        return {
            "status": "success",
            "total_posts": len(posts),
            "valid_painpoints": len(painpoints),
            "data": painpoints
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
