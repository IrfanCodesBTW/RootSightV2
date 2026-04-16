"""
RootSight — Action Payload Schemas

Models for generated follow-up actions: Jira tickets, Slack messages,
mitigation steps, and diagnostic checks.
Produced by the Action Agent.
"""

from __future__ import annotations
from pydantic import BaseModel, Field


class MitigationAction(BaseModel):
    """A single mitigation action with risk assessment."""
    action: str = Field(..., description="Action description")
    risk_level: str = Field(default="medium", description="low, medium, or high")
    approval_required: bool = Field(default=True)
    reason: str = Field(default="")


class JiraTicket(BaseModel):
    """Draft Jira ticket payload."""
    project: str = Field(default="INCIDENT")
    summary: str = Field(default="")
    description: str = Field(default="")
    priority: str = Field(default="High")
    labels: list[str] = Field(default_factory=list)
    assignee_suggestion: str = Field(default="")


class SlackMessage(BaseModel):
    """Draft Slack message payload."""
    channel: str = Field(default="#incidents")
    text: str = Field(default="")


class ActionPayloads(BaseModel):
    """
    Complete set of follow-up action drafts.
    Produced by the Action Agent.
    """
    incident_id: str
    immediate_checks: list[str] = Field(default_factory=list)
    mitigation: list[MitigationAction] = Field(default_factory=list)
    jira_ticket: JiraTicket = Field(default_factory=JiraTicket)
    slack_message: SlackMessage = Field(default_factory=SlackMessage)
    follow_up: list[str] = Field(default_factory=list)
