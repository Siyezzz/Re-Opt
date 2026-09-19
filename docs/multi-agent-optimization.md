# Multi-Agent Task Optimization

## 1. Problem Statement

We want a fast and effective way to split a large task among multiple agents.
The constraints include:

- token budget
- wall-clock time
- dependency order
- uncertainty and risk
- quality target
- context-sharing cost
- verification cost

This is itself an optimization problem. Different tasks should produce
different optimal or near-optimal coordination plans.

## 2. Graph Model

Represent a task as a directed graph:

```text
G = (V, E)
```

- `V`: subtasks, decisions, checks, or artifact updates
- `E`: prerequisite relations or required information transfer
- `w_token(v)`: estimated token cost
- `w_time(v)`: estimated duration
- `w_risk(v)`: probability-weighted cost of getting it wrong
- `value(v)`: expected contribution to the final objective
- `context(v)`: information required before execution

The scheduler chooses:

```text
assign(v) -> agent_role
order(V) -> valid topological or partially parallel execution
budget(v) -> token/time allocation
check(v) -> verification method
```

The objective can be written as:

```text
maximize quality - cost - latency - coordination_overhead - risk
```

subject to:

```text
total_tokens <= token_budget
total_time <= deadline
dependencies are respected
required checks pass
```

## 3. Algorithm Analogies

Classical algorithms are useful metaphors, but the multi-agent version needs
adaptive costs because uncertainty changes during execution.

| Algorithm | Useful Idea | Multi-Agent Interpretation |
| --- | --- | --- |
| BFS | Explore shallow layers first | Good for broad discovery when task shape is unclear |
| DFS | Follow one branch deeply | Good for research spikes or when one path is likely decisive |
| Dijkstra | Lowest cumulative cost path | Good when costs are known and non-negative |
| Bellman-Ford | Handles revised edge costs | Good when early assumptions may be wrong |
| A* | Cost plus heuristic distance | Good default when we can estimate remaining effort |
| Critical Path Method | Longest dependency chain controls duration | Good for parallel planning under deadlines |
| Branch and Bound | Prune weak branches early | Good when many possible decompositions compete |
| Monte Carlo Tree Search | Sample promising futures | Good for uncertain creative or research tasks |
| Multi-armed Bandit | Allocate more to winning strategies | Good for learning which role/workflow works per task class |

## 4. Default Agent Roles

The role set should be small enough to reuse across many tasks, but expressive
enough to cover common failure modes.

### Orchestrator

Owns the objective, constraints, task graph, agent assignment, and final
integration. This role decides when to parallelize, when to serialize, and when
to stop.

### Decomposer

Turns a fuzzy task into subtasks, dependencies, unknowns, and candidate paths.
This role is most valuable early, especially when the graph is not obvious.

### Researcher

Gathers external or internal evidence. This role is useful when facts may have
changed, when source attribution matters, or when the task depends on unfamiliar
domains.

### Builder

Executes concrete implementation steps. This role should receive a narrow brief,
clear acceptance criteria, and relevant context only.

### Critic

Looks for bugs, gaps, contradictions, hidden constraints, and missing tests.
This role is not a general editor; it is a risk detector.

### Verifier

Runs checks, tests, simulations, benchmarks, or manual inspection. This role
converts claims into observed evidence.

### Synthesizer

Compresses outputs from other agents into a coherent final artifact. This role
is essential when parallel work creates context fragmentation.

### Memory Curator

Records the run: task features, chosen strategy, constraints, results, failure
points, and lessons. In this project, SEA fills this role.

## 5. A Practical First Scheduler

Use a two-pass strategy:

1. Build a rough task graph.
2. Identify critical path nodes that block many downstream nodes.
3. Assign high-uncertainty discovery nodes to Researcher or Decomposer.
4. Assign independent concrete nodes to Builder in parallel.
5. Put Critic and Verifier after high-risk or user-visible nodes.
6. Use Synthesizer only after enough partial outputs exist.
7. Record outcomes with SEA.

This is close to A* plus Critical Path Method:

```text
priority(v) =
  dependency_blocking_score(v)
  + risk(v)
  + estimated_remaining_value(v)
  - confidence(v)
```

For a constrained run, prioritize tasks with high blocking score and high
information gain. For a generous run, also explore alternative decompositions.

## 6. SEA Self-Evolution Loop

SEA should not merely store conclusions. It should store task-conditioned
evidence.

For each run:

- task type
- graph shape
- constraints
- selected roles
- scheduler strategy
- expected result
- observed result
- surprise or failure
- reusable lesson candidate

Then future runs can ask:

```text
For tasks like this, which decomposition, role assignment, and verification
pattern previously improved quality per token or quality per minute?
```

The system becomes self-evolving when it:

1. predicts which strategy should work
2. runs a reversible experiment
3. records independent outcomes
4. promotes lessons only after repeated evidence
5. demotes lessons when counterexamples appear

## 7. First Hypothesis

For broad task coverage, the strongest default structure is:

```text
Orchestrator -> Decomposer -> parallel Researcher/Builder -> Critic -> Verifier -> Synthesizer -> Memory Curator
```

Prediction:

This will beat a single linear agent flow on large ambiguous tasks because it
reduces uncertainty earlier and catches integration errors before final output.

Counterprediction:

For small tasks, the overhead will make it slower and more token-expensive than
a single agent.

## 8. Open Questions

- How should the scheduler estimate token and time before execution?
- When is an extra critic worth the coordination overhead?
- What task features predict whether DFS-style depth or BFS-style breadth wins?
- Can a memory layer learn role assignment policies without overfitting?
- What is the minimum evidence needed before SEA promotes a strategy?
- How do we represent partial failures so they become useful training signals?
