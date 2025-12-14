from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"ok": True}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api/v1/test")
def test():
    return {"test": "ok"}

@app.post("/api/v1/fbo-postings")
def fbo():
    return {"mock": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)