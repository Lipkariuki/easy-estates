from typing import Optional

from pydantic import BaseModel, Field


class PaginationQuery(BaseModel):
    limit: int = Field(default=20, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    order: Optional[str] = Field(default=None, pattern=r"^(asc|desc)$")
