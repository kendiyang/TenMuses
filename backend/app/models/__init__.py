from app.core.database import Base
from app.models.user import User
from app.models.workflow import Workflow, WorkflowRun
from app.models.knowledge import KBDocument, KBChunk
from app.models.llm_config import LLMConfig  # 旧模型，保留向后兼容
from app.models.llm_provider import LLMProvider  # 新：供应商表
from app.models.llm_model import LLMModel  # 新：模型表

__all__ = [
    "Base", 
    "User", 
    "Workflow", 
    "WorkflowRun", 
    "KBDocument", 
    "KBChunk", 
    "LLMConfig",  # 旧模型（待迁移后废弃）
    "LLMProvider",  # 新模型
    "LLMModel",  # 新模型
]
