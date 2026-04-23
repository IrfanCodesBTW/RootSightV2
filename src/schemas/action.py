from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class ActionType(str, Enum):
    JIRA_TICKET = "jira_ticket"
    SLACK_RESPONDER = "slack_responder"
    SLACK_STAKEHOLDER = "slack_stakeholder"
    CONFLUENCE_RCA = "confluence_rca"

class ApprovalStatus(str, Enum):
    PENDING = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"

class ExecutionStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    FAILED = "failed"

class Action(BaseModel):
    action_id: str = Field(min_length=1, max_length=64)
    incident_id: str = Field(min_length=1, max_length=64)
    action_type: ActionType
    destination: str = Field(min_length=1)
    payload_preview: str = Field(min_length=1)
    full_payload: dict = Field(default_factory=dict)
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    execution_status: ExecutionStatus = ExecutionStatus.DRAFT

class ActionList(BaseModel):
    actions: list[Action] = Field(default_factory=list)
