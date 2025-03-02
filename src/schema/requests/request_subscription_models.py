from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class CreateSubscriptionRequest(BaseModel):
    product_id: str = Field(..., description="Product ID from the store")
    platform: str = Field(..., description="Platform (google_play, apple)")
    receipt_data: Optional[Dict[str, Any]] = Field(None, description="Receipt data from store")
    auto_renew: bool = Field(True, description="Auto-renew subscription")

class SubscriptionResponse(BaseModel):
    subscription_id: str
    tier: str
    status: str
    start_date: datetime
    end_date: Optional[datetime]
    auto_renew: bool 