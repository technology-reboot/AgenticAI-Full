import json
from dataclasses import asdict

from agents.orchestrator import AdvisoryWorkflow


def to_json(workflow: AdvisoryWorkflow) -> str:
    return json.dumps(asdict(workflow), default=lambda value: value.value if hasattr(value, "value") else value, indent=2)


def to_markdown(workflow: AdvisoryWorkflow) -> str:
    lines = ["# Portfolio Advisory Report", "", f"Risk profile: **{workflow.risk.profile.value}**", ""]
    lines.append("## Recommendations")
    for item in workflow.report.recommendations:
        lines.append(f"- **{item.action.title()} {item.asset_class.value}**: ${item.amount:,.2f}. {item.reason}")
    lines.extend(["", "## Stress scenarios"])
    for scenario in workflow.scenarios:
        lines.append(f"- **{scenario.name}**: {scenario.portfolio_change:+,.2f} ({scenario.description})")
    lines.extend(["", "## Narrative", workflow.narrative.text, "", "## QA", f"Approved: {workflow.qa.approved}"])
    lines.extend(f"- {check}" for check in workflow.qa.checks)
    return "\n".join(lines)