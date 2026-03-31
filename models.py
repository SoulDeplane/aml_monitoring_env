"""Typed Pydantic models for the AML Monitoring environment."""

from typing import Any, Dict, List, Optional

from pydantic import Field

from openenv.core.env_server.types import Action, Observation, State

class AMLAction(Action):

    """Action for the AML monitoring environment (non-MCP fallback)."""

    action_type: str = Field(

        description="One of: review_transactions, check_profile, flag_suspicious, file_sar, clear_alert, get_network"

    )

    account_id: str = Field(default="", description="Account to act upon")

    parameters: Dict[str, Any] = Field(

        default_factory=dict, description="Action-specific parameters"

    )

class AMLObservation(Observation):

    """Observation returned by the AML monitoring environment."""

    alert_queue: List[Dict[str, Any]] = Field(

        default_factory=list, description="Pending alerts to review"

    )

    current_alert: Dict[str, Any] = Field(

        default_factory=dict, description="Alert currently being investigated"

    )

    investigation_log: List[Dict[str, Any]] = Field(

        default_factory=list, description="History of investigation actions"

    )

    task_description: str = Field(

        default="", description="Task instructions"

    )

    feedback: str = Field(

        default="", description="Feedback from last action"

    )

    accounts_reviewed: int = Field(

        default=0, description="Number of accounts reviewed so far"

    )

    total_accounts: int = Field(

        default=0, description="Total accounts to review"

    )

class AMLState(State):

    """Internal state for the AML monitoring environment."""

    current_task: str = Field(default="easy")

    alerts_processed: int = Field(default=0)

    total_alerts: int = Field(default=0)

    correct_flags: int = Field(default=0)

    false_positives: int = Field(default=0)

    missed_suspicious: int = Field(default=0)

    sars_filed: int = Field(default=0)

