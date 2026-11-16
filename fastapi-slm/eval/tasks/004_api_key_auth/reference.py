from typing import Annotated, Optional

from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()

API_KEY = "secret-key"


def require_api_key(x_api_key: Annotated[Optional[str], Header()] = None) -> None:
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing API key")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")


@app.get("/public")
def public():
    return {"public": True}


@app.get("/secure", dependencies=[Depends(require_api_key)])
def secure():
    return {"secure": True}


@app.get("/me", dependencies=[Depends(require_api_key)])
def me():
    return {"user": "admin"}
