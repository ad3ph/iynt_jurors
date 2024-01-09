from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from config.config import Settings
settings = Settings()
from src.utils import get_last_state
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# info endpoint
@app.get("/info")
def info():
    return {"title": "About application",
            "author": "Artem Golomolzin, Siberia",
            "contact_info": "a.golomolzin@g.nsu.ru",
            "used_at": "IYNT 2023 Bobek",
            "version": "1.0.1 (Aug 27, 2023)",
            "input_folders": ",".join([settings.fights_folder, settings.jurors_file, settings.state_folder]),
            "output_folder": settings.output_folder
            }

@app.get("/")
def home(request: Request):
    last_mode, last_fight_num = get_last_state()
    available_fights = sorted([{"fight_num": int(fight_file.stem[5:])} for fight_file in settings.fights_folder.glob('fight*.csv')],
                              key=lambda x: x["fight_num"])
    return templates.TemplateResponse("home.html", {"request": request,
                                                    "last_mode": last_mode,
                                                    "last_fight_num": last_fight_num,
                                                    "fights": available_fights})

@app.get("/run")
def run(request: Request):
    return {'test_field': 1}
    #return templates.TemplateResponse("result.html", {"request": request})

if __name__ == "main":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)