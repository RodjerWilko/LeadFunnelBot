# handlers/__init__.py
from handlers.start import router as start_router
from handlers.segments import router as segments_router
from handlers.funnel import router as funnel_router
from handlers.lead import router as lead_router

__all__ = ["start_router", "segments_router", "funnel_router", "lead_router"]
