import asyncpg
import fastapi
from nicegui import ui

from .utils import show_header


def install(_: fastapi.FastAPI, db: asyncpg.Pool):
    @ui.page("/about")
    async def about():
        await show_header(db, "About")
        ui.markdown(
            """
# About

I am Rukchad Wongprayoon (aka timelessnesses on [GitHub](https://github.com/timelessnesses) and my [website](https://timelessnesses.me)) and Thanks for using and helping [Folderistic](https://github.com/timelessnesses/folderistic)!  
This project was built by the request of my mother who wants a Google Drive-like web application for her teachers and workers to submit works on online storage for her to see. This project is aimed to solve that.  
With barely any knowledge about full stack web application, I tried to work on this project and this project actually both drive me insane and at the same time happy.
I got to know what algorithm I should salt my password with, database choices, secure backend and more!  
Thanks again for using this project! If you found any bugs, please submit them to issues tab in the Github repository!  
See you! Bye!
                    """
        )
