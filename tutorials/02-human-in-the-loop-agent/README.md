# Tutorial 02: Human-in-the-loop Approval Agent

**Level**: Intermediate  
**Duration**: 15-20 minutes  
**Prerequisites**: Statehouse daemon running, Tutorial 01 completed (recommended)

## What You'll Learn

This tutorial demonstrates how to build an auditable, explainable AI workflow with human approval gates. You'll learn:

1. **Audit trails** - Every decision is recorded and can be explained
2. **Human-in-the-loop workflows** - Require approval before taking actions
3. **Post-hoc inspection** - Answer "why did this happen?" using stored state
4. **Crash recovery** - Resume workflows after restarts

## Target Audience

Engineers building AI workflows with:
- Compliance requirements
- Safety-critical decisions
- Regulatory audit needs
- Human oversight requirements

## Primary Takeaway

> "Every decision can be explained after the fact."

All reasoning, proposals, and decisions are stored in Statehouse. You can always trace back why an action was taken.

## Prerequisites

### 1. Start Statehouse Daemon

```bash
# In-memory mode (recommended for tutorials)
STATEHOUSE_USE_MEMORY=1 statehoused

# Verify
statehousectl health
```

### 2. Install Dependencies

```bash
cd tutorials/02-human-in-the-loop-agent

# Install the Statehouse Python SDK
pip install -e ../../python

# Optional: Copy and customize environment file
cp env.example .env
```

## Quick Start

### Process a Refund Request

```bash
./run.sh --refund 150.00
```

**Expected output:**

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

Justification: Based on analysis: Customer refund request

Reversible: Yes

------------------------------------------------------------

Approve this action? [y/n]: y
Approval reason (optional, press Enter to skip): Customer is in good standing

  Decision: APPROVED
[STEP 6] Applying final action...
  Result: success

=== Workflow Complete ===
```

### Process an Access Request

```bash
./run.sh --access database-admin
```

## The Workflow

The agent follows a structured workflow:

```
1. REQUEST     → Record incoming request
2. ANALYSIS    → AI analyzes the request (mock LLM)
3. PROPOSAL    → Generate action proposal
4. APPROVAL    → Request human approval (GATE)
5. DECISION    → Record human decision verbatim
6. ACTION      → Apply or abort based on decision
```

Each step persists exactly one logical event to Statehouse.

## Hands-On Exercises

### Exercise 1: Complete Workflow

Run a refund request and approve it:

```bash
./run.sh --refund 250.00
# When prompted, enter 'y' to approve
```

### Exercise 2: Reject a Request

Run a request and reject it:

```bash
./run.sh --refund 1000.00
# When prompted, enter 'n' to reject
# Provide a reason: "Amount exceeds daily limit"
```

### Exercise 3: Crash Before Approval

Simulate a crash before the human approval step:

```bash
./run.sh --refund 150.00 --crash-before-approval
```

Output:
```
[STEP 4] Requesting human approval...

💥 CRASH SIMULATION - Before approval
   Run with --resume to continue after restart
```

Resume the workflow:

```bash
./run.sh --resume
```

The agent will continue from where it left off.

### Exercise 4: Crash After Approval

Simulate a crash after approval but before action:

```bash
./run.sh --reset  # Start fresh
./run.sh --refund 150.00 --crash-after-approval
# Approve the request
```

Resume:

```bash
./run.sh --resume
```

### Exercise 5: Explain the Decision

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

### Exercise 6: Replay the Workflow

View the complete event history:

```bash
./run.sh --replay
```

Or with verbose output:

```bash
./run.sh --replay --verbose
```

**Sample output:**

```
=== Replay: approval-agent-1 ===

Replaying 7 events:

12:31:04Z  agent=approval-agent-1  WRITE   key=request              {"type":"refund", "amount":150.0...}
12:31:04Z  agent=approval-agent-1  WRITE   key=workflow_state       {"step":"request", "status":"pending"...}
12:31:05Z  agent=approval-agent-1  WRITE   key=analysis             {"summary":"Customer refund request"...}
12:31:05Z  agent=approval-agent-1  WRITE   key=proposal             {"action":"process_refund"...}
12:31:06Z  agent=approval-agent-1  WRITE   key=approval_request     {"proposal_summary":"process_refund"...}
12:31:15Z  agent=approval-agent-1  WRITE   key=human_decision       {"approved":true, "reason":"Custo..."}
12:31:15Z  agent=approval-agent-1  WRITE   key=final_action         {"approved":true, "result":{...}}
```

### Exercise 7: Use CLI for Inspection

```bash
# View current workflow state
statehousectl get approval-agent-1 workflow_state --pretty

# List all keys
statehousectl keys approval-agent-1

# Get the human decision
statehousectl get approval-agent-1 human_decision --pretty

# Full replay with pretty output (human-first format)
statehousectl replay approval-agent-1 --pretty
```

**Sample `statehousectl replay --pretty` output:**

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
- **Proposal creation**: `key=proposal` with `action:process_refund`
- **Approval request**: `key=approval_request` marking the human gate
- **Human decision**: `key=human_decision` with `approved:true`
- **Final action**: `key=final_action` with the outcome

For JSON output:
```bash
statehousectl replay approval-agent-1 --json
```

### Exercise 8: Non-Interactive Mode

For testing and CI, use auto-approval:

```bash
# Auto-approve
APPROVAL_AUTO=approve ./run.sh --refund 100.00

# Auto-reject
APPROVAL_AUTO=reject ./run.sh --refund 100.00
```

## Domain Model

### Core Concepts

The workflow is built on these domain concepts:

**Request** (input to the agent):
The initial input that triggers the workflow. Contains the type of action requested (e.g., refund, access grant), relevant parameters, and any context needed for analysis.

**Analysis** (agent reasoning output):
The AI's assessment of the request. Includes a summary, risk level, recommendation, and the factors that influenced the analysis. This captures the "why" behind subsequent decisions.

**Proposal** (action proposed by agent):
The specific action the agent proposes to take, based on the analysis. Includes the action type, parameters, justification, and whether the action is reversible.

**Approval Request** (gate event):
A formal request for human approval. Records when approval was requested and the proposal summary. This creates an audit trail of the human gate.

**Human Decision** (approve/reject):
The verbatim human response, stored exactly as provided. Includes whether approved, the reason given, who decided, and when. This is the key accountability record.

**Final Action** (outcome):
The result of executing (or aborting) the action. Records whether it was approved, the execution result, and completion timestamp.

### Statehouse Keys

The agent uses these stable keys:

| Key | Description |
|-----|-------------|
| `request` | Original incoming request |
| `analysis` | AI analysis output |
| `proposal` | Generated action proposal |
| `approval_request` | Approval request event |
| `human_decision` | Human decision (approve/reject) |
| `final_action` | Final outcome |
| `workflow_state` | Current workflow state |

## Key Patterns

### Pattern 1: Explicit Step Tracking

Each step updates the workflow state:

```python
def _persist_analysis(self, analysis: dict) -> None:
    state = self._load_workflow_state()
    new_state = state.advance("analysis", "pending")
    with self.client.begin_transaction() as tx:
        tx.write(agent_id=self.agent_id, key=KEY_ANALYSIS, value=analysis)
        tx.write(agent_id=self.agent_id, key=KEY_WORKFLOW_STATE, value=new_state.to_dict())
```

### Pattern 2: Human Decision Preservation

Human input is stored verbatim:

```python
decision_data = {
    "approved": decision.approved,
    "reason": decision.reason,
    "decided_by": decision.decided_by,
    "decided_at": decision.decided_at,
}
tx.write(agent_id=self.agent_id, key=KEY_HUMAN_DECISION, value=decision_data)
```

### Pattern 3: Post-hoc Explainability

Explain decisions using only stored state:

```python
def explain_decision(agent_id: str) -> None:
    """Explain why a decision was made, using only stored state."""
    request = client.get_state(agent_id=agent_id, key=KEY_REQUEST)
    analysis = client.get_state(agent_id=agent_id, key=KEY_ANALYSIS)
    proposal = client.get_state(agent_id=agent_id, key=KEY_PROPOSAL)
    decision = client.get_state(agent_id=agent_id, key=KEY_HUMAN_DECISION)
    # Build explanation from stored data - no re-execution needed
```

## Crash Recovery

The agent can resume from any step:

| Crash Point | Resume Behavior |
|-------------|-----------------|
| Before analysis | Re-analyze request |
| Before proposal | Generate proposal |
| Before approval | Wait for approval |
| After approval | Apply action |
| After completion | Show existing result |

No duplicate events are written on resume.

## Real-World Applications

This pattern is useful for:

1. **Financial Operations** - Refunds, transfers, large purchases
2. **Access Control** - Permission grants, role changes
3. **Content Moderation** - Publish/remove decisions
4. **Compliance Workflows** - Audit-required approvals
5. **Safety-Critical AI** - Human oversight for risky actions

## Comparison with Tutorial 01

| Tutorial 01 | Tutorial 02 |
|-------------|-------------|
| Research task | Approval workflow |
| Crash recovery | Crash recovery + human gates |
| Replay for debugging | Replay for audit/compliance |
| Tool calls | AI analysis + proposals |
| Single agent | Human-agent collaboration |

## Troubleshooting

### Daemon Not Running

```
Error: Connection failed
```

Solution:
```bash
STATEHOUSE_USE_MEMORY=1 statehoused
```

### Agent Stuck Waiting

If running non-interactively without `APPROVAL_AUTO`:

```bash
# Set auto mode
APPROVAL_AUTO=approve ./run.sh --resume
```

### State Corruption

Reset and start fresh:

```bash
./reset.sh
./run.sh --refund 150.00
```

## Summary

You've learned:

- How to build auditable AI workflows
- How to implement human approval gates
- How to explain decisions after the fact
- How to resume workflows after crashes
- How to use Statehouse for compliance

## Next Steps

- **Tutorial 01**: Resumable Research Agent (if not completed)
- **Examples**: See `examples/agent_research/` for production patterns
- **Operations**: Learn about logging and monitoring

## Further Reading

- [Replay Semantics](../../docs/replay_semantics.md)
- [Python SDK](../../python/README.md)
- [FAQ](../../docs/faq.md)
