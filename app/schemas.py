from pydantic import BaseModel, ConfigDict


class SnapshotSchema(BaseModel):
    id: int
    company_id: int
    industry_score: str

    model_config = ConfigDict(from_attributes=True)
