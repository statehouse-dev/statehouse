# Tutorial 02: Human-in-the-loop Approval Agent

**Level**: Intermediate  
**Time**: 15-20 minutes  
**Repository**: [tutorials/02-human-in-the-loop-agent/](https://github.com/username/statehouse/tree/main/tutorials/02-human-in-the-loop-agent)

Build an auditable, explainable AI workflow with human approval gates.

## What You'll Learn

- Building audit trails for every decision
- Implementing human-in-the-loop approval workflows
- Post-hoc inspection and explainability
- Crash recovery across approval boundaries

## Primary Takeaway

> Every decision can be explained after the fact.

All reasoning, proposals, and decisions are stored in Statehouse. You can always trace back why an action was taken.

## Prerequisites

Before starting:

1. **Complete Tutorial 01** (recommended) - [Resumable Research Agent](./resumable-research-agent)
2. **Python 3.9+** installed
3. **Statehouse daemon** running

### Start the Daemon

```bash
# In-memory mode
STATEHOUSE_USE_MEMORY=1 cargo run --bin statehouse-daemon
```

Wait for: `🏠 Statehouse daemon listening on 0.0.0.0:50051`

### Install Dependencies

```bash
cd tutorials/02-human-in-the-loop-agent
pip install -e ../../python
```

## The Workflow

The agent follows a structured approval workflow:

```
1. REQUEST     → Record incoming request
2. ANALYSIS    → AI analyzes the request
3. PROPOSAL    → Generate action proposal
4. APPROVAL    → Request human approval (GATE)
5. DECISION    → Record human decision
6. ACTION      → Apply or abort based on decision
```

Each step persists exactly one logical event to Statehouse.

## Running the Tutorial

### Process a Refund Request

```bash
./run.sh --refund 150.00
```

When prompted, enter `y` to approve or `n` to reject.

**Sample output:**

```
=== Tutorial 02: Human-in-the-loop Approval Agent ===
Agent ID: approval-agent-1
Request: Customer refund request for $150.00

[STEP 1] Recording request...
[STEP 2] Analyzing request...
  Analysis: Customer refund request
[STEP 3] Generating proposal...
  Proposal: process_refund
[STEP 4] Requesting human approval...
[STEP 5] Waiting for human decision...

============================================================
APPROVAL REQUIRED
============================================================

Proposed Action: process_refund
Risk Level: medium

Parameters:
  customer_id: CUST-12345
  amount: 150.0
  method: original_payment_method

Reversible: Yes

Approve this action? [y/n]: y

  Decision: APPROVED
[STEP 6] Applying final action...
  Result: success

=== Workflow Complete ===
```

### Process an Access Request

```bash
./run.sh --access database-admin
```

## Crash and Resume

### Crash Before Approval

```bash
./run.sh --refund 150.00 --crash-before-approval
```

The agent will crash before the approval step:

```
[STEP 4] Requesting human approval...

💥 CRASH SIMULATION - Before approval
   Run with --resume to continue after restart
```

Resume the workflow:

```bash
./run.sh --resume
```

### Crash After Approval

```bash
./run.sh --reset
./run.sh --refund 150.00 --crash-after-approval
# Approve the request when prompted
```

Resume:

```bash
./run.sh --resume
```

The agent continues from where it left off, without re-prompting for approval.

## Replay and Audit

### View Event History with statehousectl

Use `statehousectl replay --pretty` for human-readable output:

```bash
statehousectl replay approval-agent-1 --pretty
```

**Sample output:**

```
12:31:04Z  agent=approval-agent-1  WRITE  key=request           v=1  {"type":"refund", "amount":150.0...}
12:31:04Z  agent=approval-agent-1  WRITE  key=workflow_state    v=2  {"step":"request", "status":"pen...}
12:31:05Z  agent=approval-agent-1  WRITE  key=analysis          v=3  {"summary":"Customer refund requ...}
12:31:05Z  agent=approval-agent-1  WRITE  key=proposal          v=4  {"action":"process_refund", "ris...}
12:31:06Z  agent=approval-agent-1  WRITE  key=approval_request  v=5  {"proposal_summary":"process_ref...}
12:31:15Z  agent=approval-agent-1  WRITE  key=human_decision    v=6  {"approved":true, "reason":"Cust...}
12:31:15Z  agent=approval-agent-1  WRITE  key=final_action      v=7  {"approved":true, "result":{"sta...}
```

The replay clearly shows:
- **Proposal creation**: `key=proposal` with the action details
- **Approval request**: `key=approval_request` marking the human gate
- **Human decision**: `key=human_decision` with the approval/rejection
- **Final action**: `key=final_action` with the outcome

Or use the built-in replay:

```bash
./run.sh --replay
```

### Explain the Decision

After completing a workflow, explain why the action was taken:

```bash
./run.sh --explain
```

**Output:**

```
=== Explaining Decision for Agent: approval-agent-1 ===

1. ORIGINAL REQUEST:
   Type: refund
   Description: Customer refund request for $150.00

2. AI ANALYSIS:
   Summary: Customer refund request
   Risk Level: medium
   Recommendation: approve
   Factors:
     - Customer history: good standing
     - Product category: electronics
     - Return window: within policy

3. PROPOSED ACTION:
   Action: process_refund
   Justification: Based on analysis: Customer refund request
   Reversible: Yes

4. HUMAN DECISION:
   Approved: Yes
   Decided by: human
   Reason: Customer is in good standing

5. FINAL OUTCOME:
   Status: success
   Confirmation ID: ACT-1707412345

=== End of Explanation ===
```

### Answering "Why Did This Action Happen?"

This explanation is built entirely from stored state - no re-execution required.

The pattern for post-hoc explainability:

```python
def explain_decision(agent_id: str) -> None:
    """Explain why a decision was made, using only stored state."""
    # Load all relevant state - no re-execution needed
    request = client.get_state(agent_id=agent_id, key=KEY_REQUEST)
    analysis = client.get_state(agent_id=agent_id, key=KEY_ANALYSIS)
    proposal = client.get_state(agent_id=agent_id, key=KEY_PROPOSAL)
    decision = client.get_state(agent_id=agent_id, key=KEY_HUMAN_DECISION)
    final = client.get_state(agent_id=agent_id, key=KEY_FINAL_ACTION)
    
    # Build explanation from stored data only
    # The answer to "why?" comes from the stored state
```

Key insight: Because every step is persisted, you can always trace:
1. What was requested
2. How the AI analyzed it
3. What action was proposed and why
4. Who approved (or rejected) and their reason
5. What the final outcome was

This audit trail is critical for compliance, debugging, and trust.

## Using the CLI

```bash
# View workflow state
statehousectl get approval-agent-1 workflow_state --pretty

# Get human decision
statehousectl get approval-agent-1 human_decision --pretty

# List all keys
statehousectl keys approval-agent-1

# Full replay
statehousectl replay approval-agent-1
```

## Non-Interactive Mode

For testing and CI:

```bash
# Auto-approve
APPROVAL_AUTO=approve ./run.sh --refund 100.00

# Auto-reject
APPROVAL_AUTO=reject ./run.sh --refund 100.00
```

## Key Concepts

### Stable Keys

The agent uses these Statehouse keys:

| Key | Description |
|-----|-------------|
| `request` | Original incoming request |
| `analysis` | AI analysis output |
| `proposal` | Generated action proposal |
| `approval_request` | Approval request event |
| `human_decision` | Human decision verbatim |
| `final_action` | Final outcome |
| `workflow_state` | Current workflow state |

### Explainability Pattern

Decisions can be explained using only stored state:

```python
def explain_decision(agent_id: str) -> None:
    request = client.get_state(agent_id=agent_id, key=KEY_REQUEST)
    analysis = client.get_state(agent_id=agent_id, key=KEY_ANALYSIS)
    proposal = client.get_state(agent_id=agent_id, key=KEY_PROPOSAL)
    decision = client.get_state(agent_id=agent_id, key=KEY_HUMAN_DECISION)
    final = client.get_state(agent_id=agent_id, key=KEY_FINAL_ACTION)
    
    # Build explanation from stored data
    # No re-execution needed
```

### Human Decision Preservation

Human input is stored verbatim:

```python
decision_data = {
    "approved": decision.approved,
    "reason": decision.reason,
    "decided_by": decision.decided_by,
    "decided_at": decision.decided_at,
}
```

## Real-World Applications

- **Financial Operations**: Refunds, transfers, large purchases
- **Access Control**: Permission grants, role changes
- **Content Moderation**: Publish/remove decisions
- **Compliance Workflows**: Audit-required approvals
- **Safety-Critical AI**: Human oversight for risky actions

## Common Issues

### Daemon Connection Failed

```bash
STATEHOUSE_USE_MEMORY=1 cargo run --bin statehouse-daemon
```

### Stuck Waiting for Input

Set auto-approval for non-interactive environments:

```bash
APPROVAL_AUTO=approve ./run.sh --resume
```

### Reset State

```bash
./reset.sh
```

## Source Code

Full source code: [tutorials/02-human-in-the-loop-agent/](https://github.com/username/statehouse/tree/main/tutorials/02-human-in-the-loop-agent)

Key files:
- `agent.py` - Main agent implementation
- `human.py` - Human approval module
- `README.md` - Detailed tutorial guide

## Next Steps

- Review the [Python SDK documentation](../python-sdk/overview)
- Explore [production examples](../examples/reference-agent)
- Learn about [operations and monitoring](../operations/logging-and-metrics)
