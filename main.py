from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return{"ahoj kamos, backend funguje :)"}