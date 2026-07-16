from fastapi import FastAPI

app = FastAPI(title="FastAPI Authentication System")

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI Authentication System"}
