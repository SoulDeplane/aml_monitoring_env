"""Core AML Monitoring environment implementing MCPEnvironment.
Simulates anti-money laundering transaction monitoring where an agent reviews
alerts, analyzes transactions, identifies suspicious patterns, and makes
disposition decisions (flag, clear, file SAR).
"""

import json
import random
from typing import Any, Dict, List, Optional
from uuid import uuid4
from fastmcp import FastMCP
from openenv.core.env_server.mcp_environment import MCPEnvironment
from openenv.core.env_server.types import Observation, State

try:
    from ..data.scenarios import generate_scenario
    from ..graders.grader_easy import grade_easy
    from ..graders.grader_medium import grade_medium
    from ..graders.grader_hard import grade_hard
except ImportError:
    from data.scenarios import generate_scenario
    from graders.grader_easy import grade_easy
    from graders.grader_medium import grade_medium
    from graders.grader_hard import grade_hard

class AMLMonitoringEnvironment(MCPEnvironment):
    """MCP-based environment for AML transaction monitoring.
    MCP Tools:
    - review_transactions: Get transaction history for an account
    - check_customer_profile: Review KYC and risk profile
    - analyze_pattern: Check for specific suspicious patterns
    - get_network: Map transaction relationships between accounts
    - flag_suspicious: Flag an account as suspicious
    - file_sar: File a Suspicious Activity Report
    - clear_alert: Dismiss an alert as legitimate
    """

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self) -> None:
        mcp = FastMCP("aml_monitoring_env")
        env_ref = self

        @mcp.tool

        def review_transactions(
            account_id: str,
            days: int = 90,
            min_amount: float = 0,
            transaction_type: str = "",
        ) -> str:
            """Review transaction history for a specific account.
            Args:
                account_id: The account ID to review (e.g., 'ACC-0001').
                days: Number of days of history to retrieve (default: 90).
                min_amount: Minimum transaction amount filter.
                transaction_type: Filter by type (wire_transfer, cash_deposit, etc.).
            Returns:
                JSON string with transaction records.
            """

            return env_ref._handle_review_transactions(account_id, days, min_amount, transaction_type)

        @mcp.tool

        def check_customer_profile(account_id: str) -> str:
            """Check KYC/customer profile and risk assessment for an account.
            Args:
                account_id: The account ID to check.
            Returns:
                JSON with customer name, type, country, risk level, KYC status,
                expected volume, PEP status, and previous SAR history.
            """

            return env_ref._handle_check_profile(account_id)

        @mcp.tool

        def analyze_pattern(
            account_id: str,
            pattern_type: str,
        ) -> str:
            """Analyze transactions for a specific suspicious pattern.
            Args:
                account_id: Account to analyze.
                pattern_type: Pattern to check for. One of: 'structuring',
                    'rapid_movement', 'round_tripping', 'layering',
                    'shell_company', 'network_structuring'.
            Returns:
                JSON with pattern analysis results including indicators found.
            """

            return env_ref._handle_analyze_pattern(account_id, pattern_type)

        @mcp.tool

        def get_network(account_id: str) -> str:
            """Map transaction network relationships for an account.
            Args:
                account_id: Account to map network for.
            Returns:
                JSON with connected accounts, shared counterparties,
                and relationship descriptions.
            """

            return env_ref._handle_get_network(account_id)

        @mcp.tool

        def flag_suspicious(
            account_id: str,
            patterns: list,
            evidence: str,
            risk_assessment: str = "high",
        ) -> str:
            """Flag an account as suspicious.
            Args:
                account_id: Account to flag.
                patterns: List of detected patterns (e.g., ['structuring', 'rapid_movement']).
                evidence: Text description of evidence supporting the flag.
                risk_assessment: Risk level ('high', 'critical').
            Returns:
                JSON confirming the flag.
            """

            return env_ref._handle_flag(account_id, patterns, evidence, risk_assessment)

        @mcp.tool

        def file_sar(
            account_id: str,
            patterns: list,
            narrative: str,
            estimated_amount: float = 0,
        ) -> str:
            """File a Suspicious Activity Report (SAR) for an account.
            Use for confirmed money laundering or most egregious cases.
            Args:
                account_id: Account the SAR is for.
                patterns: Detected laundering patterns.
                narrative: Detailed narrative for the SAR filing.
                estimated_amount: Estimated total suspicious amount in USD.
            Returns:
                JSON confirming SAR filing.
            """

            return env_ref._handle_file_sar(account_id, patterns, narrative, estimated_amount)

        @mcp.tool

        def clear_alert(
            account_id: str,
            justification: str,
        ) -> str:
            """Clear/dismiss an alert as a false positive.
            Args:
                account_id: Account whose alert to clear.
                justification: Explanation of why this is not suspicious.
            Returns:
                JSON confirming alert clearance.
            """

            return env_ref._handle_clear(account_id, justification)
        super().__init__(mcp)
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._scenario: Optional[Dict[str, Any]] = None
        self._task_id = "easy"
        self._seed = 42
        self._investigation_log: List[Dict[str, Any]] = []
        self._flags: List[Dict[str, Any]] = []
        self._clears: List[Dict[str, Any]] = []
        self._sars: List[Dict[str, Any]] = []
        self._episode_reward = 0.0
        self._done = False
        self._last_feedback = ""
        self._last_reward = 0.0
        self._repeated_actions: Dict[str, int] = {}

    @property

    def state(self) -> State:
        return self._state

    def reset(self, seed: Optional[int] = None, episode_id: Optional[str] = None, **kwargs) -> Observation:
        """Reset for a new AML investigation episode."""

        self._seed = seed if seed is not None else 42
        self._task_id = kwargs.get("task_id", "easy")
        self._state = State(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
        )
        self._scenario = generate_scenario(self._task_id, self._seed)
        self._investigation_log = []
        self._flags = []
        self._clears = []
        self._sars = []
        self._episode_reward = 0.0
        self._done = False
        self._last_feedback = "AML monitoring session started. Review the pending alerts."
        self._last_reward = 0.0
        self._repeated_actions = {}
        try:
            from ..tasks import task_easy, task_medium, task_hard
        except ImportError:
            from tasks import task_easy, task_medium, task_hard

        task_configs = {
            "easy": task_easy.TASK_CONFIG,
            "medium": task_medium.TASK_CONFIG,
            "hard": task_hard.TASK_CONFIG,
        }
        task_config = task_configs.get(self._task_id, task_configs["easy"])
        return Observation(
            done=False,
            reward=0.0,
            metadata={
                "scenario_id": self._scenario["scenario_id"],
                "title": self._scenario["title"],
                "description": self._scenario["description"],
                "task_description": task_config["description"],
                "alerts": self._scenario["alerts"],
                "review_accounts": self._scenario["review_accounts"],
                "alerts_count": len(self._scenario["alerts"]),
                "feedback": self._last_feedback,
                "investigation_log": [],
            },
        )

    def step(self, action, timeout_s=None, **kwargs) -> Observation:
        """Execute one step."""

        self._state.step_count += 1
        if self._done:
            return self._make_observation(reward=0.0, feedback="Episode already ended.")
        max_steps = self._scenario.get("max_steps", 50) if self._scenario else 50
        if self._state.step_count >= max_steps:
            self._done = True
            self._run_grader()
            return self._make_observation(reward=-0.1, feedback=f"Step limit ({max_steps}) reached.")
        return super().step(action, timeout_s=timeout_s, **kwargs)

    def _step_impl(self, action, timeout_s=None, **kwargs) -> Observation:
        return self._make_observation(
            reward=-0.05,
            feedback="Invalid action. Use the available MCP tools.",
        )

    def _handle_review_transactions(self, account_id: str, days: int, min_amount: float, transaction_type: str) -> str:
        if not self._scenario:
            return json.dumps({"error": "No scenario loaded."})
        action_key = f"review_transactions:{account_id}"
        self._repeated_actions[action_key] = self._repeated_actions.get(action_key, 0) + 1
        reward = 0.05
        if self._repeated_actions[action_key] > 2:
            reward = -0.02
        all_txns = self._scenario.get("all_transactions", self._scenario.get("transactions", {}))
        txns = all_txns.get(account_id, [])
        if not txns:
            feedback = f"No transactions found for account {account_id}."
            reward = 0.01
        else:
            if min_amount > 0:
                txns = [t for t in txns if t["amount"] >= min_amount]
            if transaction_type:
                txns = [t for t in txns if t["type"] == transaction_type]
            feedback = f"Retrieved {len(txns)} transactions for {account_id}."
        clean_txns = []
        for t in txns[:30]:
            clean = {k: v for k, v in t.items() if k not in ("is_suspicious_ground_truth", "pattern_type")}
            clean_txns.append(clean)
        self._investigation_log.append({
            "tool": "review_transactions",
            "account_id": account_id,
            "result_count": len(clean_txns),
        })
        self._last_reward = reward
        self._episode_reward += reward
        self._last_feedback = feedback
        total_credits = sum(t["amount"] for t in txns if t.get("direction") == "credit")
        total_debits = sum(t["amount"] for t in txns if t.get("direction") == "debit")
        cash_deposits = [t for t in txns if t.get("type") == "cash_deposit"]
        return json.dumps({
            "account_id": account_id,
            "transaction_count": len(clean_txns),
            "transactions": clean_txns,
            "summary": {
                "total_credits": round(total_credits, 2),
                "total_debits": round(total_debits, 2),
                "cash_deposit_count": len(cash_deposits),
                "cash_deposit_total": round(sum(t["amount"] for t in cash_deposits), 2),
                "unique_counterparties": len({t.get("counterparty") for t in txns}),
            },
            "feedback": feedback,
        })

    def _handle_check_profile(self, account_id: str) -> str:
        if not self._scenario:
            return json.dumps({"error": "No scenario loaded."})
        profiles = self._scenario.get("all_profiles", self._scenario.get("profiles", {}))
        profile = profiles.get(account_id)
        if not profile:
            return json.dumps({"error": f"Account {account_id} not found."})
        clean = {k: v for k, v in profile.items() if k != "is_suspicious_ground_truth"}
        self._investigation_log.append({
            "tool": "check_customer_profile",
            "account_id": account_id,
        })
        reward = 0.05
        self._last_reward = reward
        self._episode_reward += reward
        self._last_feedback = f"Profile retrieved for {account_id} ({profile['name']})."
        return json.dumps({"profile": clean})

    def _handle_analyze_pattern(self, account_id: str, pattern_type: str) -> str:
        if not self._scenario:
            return json.dumps({"error": "No scenario loaded."})
        valid_patterns = ["structuring", "rapid_movement", "round_tripping", "layering", "shell_company", "network_structuring"]
        if pattern_type not in valid_patterns:
            return json.dumps({"error": f"Invalid pattern_type. Valid: {valid_patterns}"})
        all_txns = self._scenario.get("all_transactions", self._scenario.get("transactions", {}))
        txns = all_txns.get(account_id, [])
        indicators = []
        pattern_txns = [t for t in txns if t.get("pattern_type") == pattern_type]
        if pattern_type == "structuring":
            cash_deps = [t for t in txns if t.get("type") == "cash_deposit" and t["amount"] < 10000 and t["amount"] > 7500]
            if len(cash_deps) >= 3:
                indicators.append(f"Found {len(cash_deps)} cash deposits between $7,500-$9,999")
                indicators.append(f"Total: ${sum(t['amount'] for t in cash_deps):,.2f}")
        elif pattern_type == "rapid_movement":
            wire_in = [t for t in txns if t.get("type") in ("wire_transfer", "foreign_wire") and t.get("direction") == "credit"]
            wire_out = [t for t in txns if t.get("type") in ("wire_transfer", "foreign_wire") and t.get("direction") == "debit"]
            if wire_in and wire_out:
                indicators.append(f"Found {len(wire_in)} incoming and {len(wire_out)} outgoing wire transfers")
                indicators.append("Check timing between deposits and withdrawals for pass-through pattern")
        elif pattern_type == "round_tripping":
            offshore_out = [t for t in txns if t.get("direction") == "debit" and t.get("country_destination") not in ("United States", "")]
            offshore_in = [t for t in txns if t.get("direction") == "credit" and t.get("country_origin") not in ("United States", "")]
            if offshore_out and offshore_in:
                indicators.append(f"Found {len(offshore_out)} outgoing and {len(offshore_in)} incoming international transfers")
                indicators.append("Check if funds sent out return through different entities")
        elif pattern_type == "layering":
            multi_hop = [t for t in txns if t.get("type") in ("wire_transfer", "foreign_wire")]
            unique_counterparties = {t.get("counterparty") for t in multi_hop}
            if len(unique_counterparties) >= 4:
                indicators.append(f"Transactions involve {len(unique_counterparties)} distinct counterparties")
                indicators.append("Multiple jurisdictions and entities suggest layering")
        elif pattern_type == "shell_company":
            try:
                from ..data.customers import SHELL_COMPANY_NAMES
            except ImportError:
                from data.customers import SHELL_COMPANY_NAMES

            shell_txns = [t for t in txns if t.get("counterparty") in SHELL_COMPANY_NAMES]
            if shell_txns:
                shells = {t["counterparty"] for t in shell_txns}
                indicators.append(f"Found {len(shell_txns)} transactions with known offshore entities: {', '.join(shells)}")
        elif pattern_type == "network_structuring":
            sub_threshold = [t for t in txns if t.get("type") == "internal_transfer" and t["amount"] < 10000 and t.get("direction") == "credit"]
            if len(sub_threshold) >= 3:
                senders = {t.get("counterparty") for t in sub_threshold}
                indicators.append(f"Received {len(sub_threshold)} sub-threshold transfers from {len(senders)} accounts")
        detected = len(indicators) > 0
        self._investigation_log.append({
            "tool": "analyze_pattern",
            "account_id": account_id,
            "pattern_type": pattern_type,
            "detected": detected,
        })
        reward = 0.05
        self._last_reward = reward
        self._episode_reward += reward
        self._last_feedback = f"Pattern analysis for {pattern_type} on {account_id}: {'indicators found' if detected else 'no clear indicators'}."
        return json.dumps({
            "account_id": account_id,
            "pattern_type": pattern_type,
            "indicators_found": detected,
            "indicators": indicators,
            "suspicious_transaction_count": len(pattern_txns),
        })

    def _handle_get_network(self, account_id: str) -> str:
        if not self._scenario:
            return json.dumps({"error": "No scenario loaded."})
        network = self._scenario.get("network", {})
        account_network = network.get(account_id)
        all_txns = self._scenario.get("all_transactions", self._scenario.get("transactions", {}))
        txns = all_txns.get(account_id, [])
        counterparties = {}
        for t in txns:
            cp = t.get("counterparty", "")
            if cp and cp != "CASH":
                if cp not in counterparties:
                    counterparties[cp] = {"total_amount": 0, "transaction_count": 0, "directions": set()}
                counterparties[cp]["total_amount"] += t["amount"]
                counterparties[cp]["transaction_count"] += 1
                counterparties[cp]["directions"].add(t.get("direction", ""))
        for cp in counterparties:
            counterparties[cp]["directions"] = list(counterparties[cp]["directions"])
            counterparties[cp]["total_amount"] = round(counterparties[cp]["total_amount"], 2)
        result = {
            "account_id": account_id,
            "counterparty_count": len(counterparties),
            "counterparties": counterparties,
        }
        if account_network:
            result["connected_internal_accounts"] = account_network.get("connected_accounts", [])
            result["shared_counterparties"] = account_network.get("shared_counterparties", [])
            result["relationship_note"] = account_network.get("relationship", "")
        self._investigation_log.append({
            "tool": "get_network",
            "account_id": account_id,
            "counterparty_count": len(counterparties),
        })
        reward = 0.05
        self._last_reward = reward
        self._episode_reward += reward
        self._last_feedback = f"Network map for {account_id}: {len(counterparties)} counterparties found."
        return json.dumps(result)

    def _handle_flag(self, account_id: str, patterns: list, evidence: str, risk_assessment: str) -> str:
        if not self._scenario:
            return json.dumps({"error": "No scenario loaded."})
        flag = {
            "account_id": account_id,
            "patterns": patterns,
            "evidence": evidence,
            "risk_assessment": risk_assessment,
        }
        self._flags.append(flag)
        expected = self._scenario.get("expected", {})
        exp = expected.get(account_id, {})
        is_correct = exp.get("suspicious", False)
        if is_correct:
            reward = 0.20
            feedback = f"Account {account_id} flagged as suspicious. Good catch."
        else:
            reward = -0.15
            feedback = f"Account {account_id} flagged, but this may be a false positive."
        self._investigation_log.append({
            "tool": "flag_suspicious",
            "account_id": account_id,
            "patterns": patterns,
            "correct": is_correct,
        })
        self._last_reward = reward
        self._episode_reward += reward
        self._last_feedback = feedback
        self._check_completion()
        return json.dumps({"flagged": True, "account_id": account_id, "feedback": feedback})

    def _handle_file_sar(self, account_id: str, patterns: list, narrative: str, estimated_amount: float) -> str:
        if not self._scenario:
            return json.dumps({"error": "No scenario loaded."})
        sar = {
            "account_id": account_id,
            "patterns": patterns,
            "narrative": narrative,
            "estimated_amount": estimated_amount,
        }
        self._sars.append(sar)
        expected = self._scenario.get("expected", {})
        exp = expected.get(account_id, {})
        should_sar = exp.get("action") == "file_sar"
        if should_sar:
            reward = 0.30
            feedback = f"SAR filed for {account_id}. Correct — this account requires a SAR."
        elif exp.get("suspicious", False):
            reward = 0.10
            feedback = f"SAR filed for {account_id}. Account is suspicious but a flag would suffice."
        else:
            reward = -0.20
            feedback = f"SAR filed for {account_id}. This appears to be a false positive — filing unnecessary SARs wastes compliance resources."
        self._investigation_log.append({
            "tool": "file_sar",
            "account_id": account_id,
            "patterns": patterns,
            "correct": should_sar,
        })
        self._last_reward = reward
        self._episode_reward += reward
        self._last_feedback = feedback
        self._check_completion()
        return json.dumps({"sar_filed": True, "account_id": account_id, "feedback": feedback})

    def _handle_clear(self, account_id: str, justification: str) -> str:
        if not self._scenario:
            return json.dumps({"error": "No scenario loaded."})
        clear = {
            "account_id": account_id,
            "justification": justification,
        }
        self._clears.append(clear)
        expected = self._scenario.get("expected", {})
        exp = expected.get(account_id, {})
        should_clear = not exp.get("suspicious", True)
        if should_clear:
            reward = 0.15
            feedback = f"Alert for {account_id} cleared. Correct — this was a false positive."
        else:
            reward = -0.25
            feedback = f"Alert for {account_id} cleared. WARNING: This account has genuine suspicious activity that was missed."
        self._investigation_log.append({
            "tool": "clear_alert",
            "account_id": account_id,
            "correct": should_clear,
        })
        self._last_reward = reward
        self._episode_reward += reward
        self._last_feedback = feedback
        self._check_completion()
        return json.dumps({"cleared": True, "account_id": account_id, "feedback": feedback})

    def _check_completion(self):
        """Check if all accounts have been dispositioned."""

        if not self._scenario:
            return
        review_accounts = set(self._scenario.get("review_accounts", []))
        dispositioned = (
            {f["account_id"] for f in self._flags}
            | {s["account_id"] for s in self._sars}
            | {c["account_id"] for c in self._clears}
        )
        if review_accounts and review_accounts <= dispositioned:
            self._done = True
            self._run_grader()

    def _make_observation(self, reward: float = 0.0, feedback: str = "") -> Observation:
        self._last_reward = reward
        self._episode_reward += reward
        if feedback:
            self._last_feedback = feedback
        meta = {}
        if self._scenario:
            review = set(self._scenario.get("review_accounts", []))
            dispositioned = (
                {f["account_id"] for f in self._flags}
                | {s["account_id"] for s in self._sars}
                | {c["account_id"] for c in self._clears}
            )
            remaining = review - dispositioned
            meta = {
                "scenario_id": self._scenario["scenario_id"],
                "title": self._scenario["title"],
                "alerts_count": len(self._scenario.get("alerts", [])),
                "accounts_remaining": list(remaining),
                "accounts_total": len(review),
                "flags_count": len(self._flags),
                "sars_count": len(self._sars),
                "clears_count": len(self._clears),
                "steps_taken": self._state.step_count,
                "max_steps": self._scenario.get("max_steps", 50),
                "feedback": self._last_feedback,
                "investigation_log": self._investigation_log[-10:],
                "episode_reward": round(self._episode_reward, 4),
            }
        return Observation(done=self._done, reward=reward, metadata=meta)

    def _run_grader(self) -> None:
        if not self._scenario:
            return
        graders = {"easy": grade_easy, "medium": grade_medium, "hard": grade_hard}
        grader = graders.get(self._task_id, grade_easy)
        self._grader_result = grader(
            scenario=self._scenario,
            investigation_log=self._investigation_log,
            flags=self._flags,
            clears=self._clears,
            sars=self._sars,
            total_steps=self._state.step_count,
        )

    def close(self) -> None:
        pass
