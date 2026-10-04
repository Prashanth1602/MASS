from fastapi import FastAPI

app = FastAPI(
    title="MASS - Modular Application Service Stack",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "MASS - Modular Application Service Stack is running"
    }


@app.post("/build")
def build_application():
    return {
        "message": "Build engine is not implemented yet"
    }