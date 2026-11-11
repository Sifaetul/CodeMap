from fastapi import FastAPI

app = FastAPI(title="CodeAtlas Analyzer")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "analyzer"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
