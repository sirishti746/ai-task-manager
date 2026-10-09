from pydantic import BaseModel, ConfigDict, Field
class GenerateDescriptionRequest(BaseModel):
    """Body of POST /api/tasks/generate-description."""

    model_config = ConfigDict(str_strip_whitespace=True)

    # Same max as the task title column. The cap also limits cost and abuse.
    title: str = Field(min_length=1, max_length=200)
class GenerateDescriptionResponse(BaseModel):
    description: str