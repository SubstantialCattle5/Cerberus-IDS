from typing import Union

from fastapi import FastAPI
from app.routes.IpLocationRouter import router as location_router
from app.routes.PointBuilderRouter import router as point_builder_router

app = FastAPI()

app.include_router(location_router, prefix="/location_tracker", tags=["Location Tracker"]) 
app.include_router(point_builder_router, prefix="/point_builder", tags=["Point Builder"])  