"""
Pydantic models for validating agent results.
"""
from typing import Optional
from pydantic import BaseModel, Field


class VisionResult(BaseModel):
    """Result from Vision Agent."""
    agent: str = Field(default="vision", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="Analysis text output")
    confidence: Optional[str] = Field(default=None, description="Confidence level")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    
    class Config:
        """Pydantic config."""
        frozen = False  # Allow updates for error handling


class OCRResult(BaseModel):
    """Result from OCR Agent."""
    agent: str = Field(default="ocr", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="OCR text output")
    has_text: bool = Field(default=False, description="Whether text was detected")
    confidence: Optional[str] = Field(default=None, description="Confidence level")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    
    class Config:
        """Pydantic config."""
        frozen = False


class DetectionResult(BaseModel):
    """Result from Detection Agent."""
    agent: str = Field(default="detection", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="Detection text output")
    confidence: Optional[str] = Field(default=None, description="Confidence level")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    
    class Config:
        """Pydantic config."""
        frozen = False


class AgentResults(BaseModel):
    """Combined results from all agents."""
    vision: VisionResult
    ocr: OCRResult
    detection: DetectionResult
    
    class Config:
        """Pydantic config."""
        frozen = False


class FinalReport(BaseModel):
    """Final report structure."""
    timestamp: str = Field(description="ISO timestamp")
    status: str = Field(description="Overall status")
    agents: AgentResults = Field(description="Results from all agents")
    
    class Config:
        """Pydantic config."""
        frozen = False

