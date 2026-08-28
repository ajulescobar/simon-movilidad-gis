from pydantic import BaseModel, Field

class TelemetryPacket(BaseModel):
    vehicle_id: str = Field(..., min_length=3, max_length=20, examples=["VHC-8472-ABC"])
    latitude: float = Field(..., ge=-90, le=90, description="Latitud en grados decimales")
    longitude: float = Field(..., ge=-180, le=180, description="Longitud en grados decimales")
    speed_kmh: float = Field(..., ge=0, le=300)
    fuel_level: float = Field(..., ge=0, le=100)