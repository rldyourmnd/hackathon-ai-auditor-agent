from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from .common import ClientType


class PromptDto(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Prompt text content to analyze",
        example="Write a Python function that calculates fibonacci numbers",
    )
    format_type: str = Field(
        default="auto",
        pattern="^(auto|text|markdown|xml)$",
        description="Prompt format type detection",
        example="auto",
    )
    language: str = Field(
        default="auto",
        description="Prompt language (auto-detected if not specified)",
        example="en",
    )


class ClientInfo(BaseModel):
    type: ClientType = Field(default=ClientType.BROWSER, description="Client type")
    name: str = Field(..., description="Client name/identifier", example="chatgpt-extension")
    version: str = Field(default="1.0.0", description="Client version", example="1.2.3")
    user_agent: Optional[str] = Field(None, description="Browser user agent")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional client metadata")


class AnalyzeRequest(BaseModel):
    """Request for prompt analysis"""

    prompt: PromptDto = Field(..., description="Prompt to analyze")
    client_info: Optional[ClientInfo] = Field(None, description="Client information")
    save_result: bool = Field(default=True, description="Whether to save analysis result")

    model_config = {
        "json_schema_extra": {
            "example": {
                "prompt": {
                    "content": "Write a Python function that calculates fibonacci numbers",
                    "format_type": "auto",
                    "language": "en",
                },
                "client_info": {
                    "type": "browser",
                    "name": "chatgpt-extension",
                    "version": "1.0.0",
                },
                "save_result": True,
            }
        }
    }


class ClarifyAnswer(BaseModel):
    question_id: str = Field(..., description="ID of the question being answered")
    answer: str = Field(..., description="User's answer to the clarification question")


class ClarifyRequest(BaseModel):
    """Request for clarification cycle"""

    analysis_id: str = Field(..., description="ID of the analysis to clarify")
    answers: List[ClarifyAnswer] = Field(..., description="Answers to clarification questions")


class ApplyRequest(BaseModel):
    """Request to apply patches"""

    analysis_id: str = Field(..., description="ID of the analysis")
    patch_ids: List[str] = Field(..., description="IDs of patches to apply")
    apply_safe_all: bool = Field(default=False, description="Apply all safe patches automatically")
