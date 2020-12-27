import uvicorn
from fastapi import FastAPI
from libs.c19lite_backend import download_districts

app = FastAPI(docs_url=None, redoc_url=None)


@app.get("/json/")
async def read_item(lang='sv'):
    if lang in ['sv', 'en', 'fi']:
        return download_districts(lang)


if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0')
