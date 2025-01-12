from fastapi import FastAPI
from app.routes.IpLocationRouter import router as location_router
from app.routes.PointBuilderRouter import router as point_builder_router
from app.routes.ReputationManagerRouter import app as reputation_manager_router

app = FastAPI()

# Location based ids
app.include_router(location_router, prefix="/location_tracker", tags=["Location Tracker"]) 
app.include_router(point_builder_router, prefix="/point_builder", tags=["Point Builder"]) 

#! route sucks 
app.include_router(reputation_manager_router, prefix="/reputation_manager", tags=["Reputation Manager"])  


# signature based ids
