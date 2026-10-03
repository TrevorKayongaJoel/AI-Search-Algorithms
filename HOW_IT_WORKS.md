# Makerere Campus Route Finder: How It Works

This guide explains how `route_finder.py` works and where each requirement in `assign1.pdf` is answered, in the code (`route_finder.py`) or in the report (`report.pdf`).

---

## 1. Quick start

```
python route_finder.py           # normal run: graph search (reached table ON)
python route_finder.py --tree    # tree-like search (reached table OFF), used for B4
```

The program lists the 14 schools with numbers, then asks three questions. You can type either a number or the school's name:

```
Valid places (schools) - type the number or the name:
   1. CoCIS
   2. College of Natural Sciences
   3. Margaret Trowell School of Industrial and Fine Art
   4. School of Agricultural Sciences
   5. School of Economics
   6. School of Education
   7. School of Engineering
   8. School of Food Technology, Nutrition and Bioengineering
   9. School of Law
  10. School of Liberal and Performing Arts
  11. School of Social Sciences
  12. School of Statistics and Planning
  13. School of Veterinary Medicine
  14. School of the Built Environment

Source school: 1
Destination school: 11
Algorithm (BFS or DFS): BFS

Algorithm: BFS
Route: CoCIS -> Central Teaching Facility -> Freedom Square -> Main Building -> School of Social Sciences
Cost (hops): 4
Nodes expanded: 13
```

---

## 2. How the program is organised

The file is split into sections that follow the assignment's parts:

| Lines (approx.) | Section | What it contains |
|---|---|---|
| 21–81 | **The campus graph** | `LANDMARKS`, `SCHOOLS`, `EDGES` copied exactly from the PDF, plus `build_graph()` |
| 84–111 | **Problem formulation** | `RouteProblem`: the five components as code |
| 113–145 | **B1. Data structures** | `Node`, `solution()`, `expand()` |
| 147–187 | **Frontiers** | `FIFOQueue` (BFS) and `LIFOStack` (DFS), the only difference between the algorithms |
| 190–246 | **B2. Generic search loop** | `SearchResult`, `search()`, the lecture's seven steps |
| 249–end | **B3. User interface** | input matching, error messages, output format, `main()` |

### 2.1 The graph: `build_graph(EDGES)`

```python
def build_graph(edges):
    graph = {}
    for a, b in edges:
        graph.setdefault(a, set()).add(b)  # connections are two-way,
        graph.setdefault(b, set()).add(a)  # so add both directions
    return {place: sorted(neighbours) for place, neighbours in graph.items()}
```

- Each edge `("A", "B")` is stored **both ways** (A→B and B→A), because the PDF says connections are two-way.
- Each neighbour list is **sorted alphabetically** once, here. That's how the search always considers neighbours in alphabetical order, which the PDF requires for deterministic marking.
- The result is an adjacency list. For example:
  `GRAPH["Main Library"] = ["Freedom Square", "Main Building", "School of Economics", "School of Education"]`

### 2.2 The problem: `RouteProblem`

Each of the five formal components from Part A becomes one piece of code:

| Component | Code | What it does |
|---|---|---|
| Initial state | `self.initial` | The source school |
| Actions(s) | `actions(state)` | Returns `"walk to X"` for every neighbour X in `GRAPH[state]` |
| Result(s, a) | `result(state, action)` | `"walk to X"` → `X` |
| Goal test | `is_goal(state)` | `state == self.goal` |
| Step / path cost | `step_cost(...)` | Always returns `1` |

### 2.3 `Node` and `solution()`: B1

```python
class Node:
    def __init__(self, state, parent=None, action=None, path_cost=0):
        self.state = state          # STATE
        self.parent = parent        # PARENT
        self.action = action        # ACTION
        self.path_cost = path_cost  # PATH-COST
```

A **node** is not a state. A state is just a place. A node is one point in the search tree: *a place reached by a particular path*. The same place can be stored in several nodes with different parents and costs.

```python
def solution(node):
    path = []
    while node is not None:
        path.append(node.state)
        node = node.parent      # follow PARENT pointers to the root
    return list(reversed(path)) # root first
```

`expand(problem, node)` creates one child `Node` for each action, with `path_cost = parent's cost + 1`.

### 2.4 The frontiers: the only BFS/DFS difference

```python
class FIFOQueue:                       # BFS
    def add_all(self, nodes): self.items.extend(nodes)        # add at back
    def remove(self):         return self.items.popleft()     # remove from FRONT

class LIFOStack:                       # DFS
    def add_all(self, nodes): self.items.extend(reversed(nodes))  # push in reverse
    def remove(self):         return self.items.pop()             # remove from BACK

STRATEGIES = {"BFS": FIFOQueue, "DFS": LIFOStack}
```

**Why does the stack push in reverse?** The children come out of `expand()` in alphabetical order, e.g. `[CTF, ENG, SSP]`. A stack returns the **last** item pushed, so pushing them in that order would explore SSP first, the *last* alphabetically. Pushing `[SSP, ENG, CTF]` puts **CTF on top**, so the alphabetically first neighbour is explored first, as the PDF requires.

### 2.5 The generic search loop: B2

```python
def search(problem, strategy, use_reached=True, max_expansions=MAX_EXPANSIONS):
    frontier = STRATEGIES[strategy]()          # Step 1  <- only place the strategy is used
    frontier.add_all([Node(problem.initial)])
    reached = {}
    expanded = 0

    while len(frontier) > 0:                   # Step 2
        node = frontier.remove()               # Step 3
        if problem.is_goal(node.state):        # Step 4: goal test on REMOVAL
            return SearchResult(node, expanded)
        if expanded >= max_expansions:         # safety cap (10,000)
            return SearchResult(None, expanded, cutoff=True)
        expanded += 1                          # Step 5: expand
        children = []
        for child in expand(problem, node):
            if use_reached:                    # Step 6: graph search
                if child.state in reached:
                    continue
                reached[child.state] = child
            children.append(child)
        frontier.add_all(children)
        # Step 7: loop back to step 2
    return SearchResult(None, expanded)        # Step 2: frontier empty -> failure
```

How each lecture step appears in the code:

| Lecture step | Code |
|---|---|
| 1. Initial node on frontier, reached empty | `frontier.add_all([Node(problem.initial)])`, `reached = {}` |
| 2. Frontier empty → failure | `while len(frontier) > 0` … `return SearchResult(None, ...)` |
| 3. Remove a node by the strategy | `frontier.remove()` (FIFO or LIFO) |
| 4. Goal test → solution via PARENT | `if problem.is_goal(...)`, then `solution(node)` via `SearchResult.route` |
| 5. Expand, generate children | `expanded += 1`, `expand(problem, node)` |
| 6. Skip states in reached, else record and add | `if child.state in reached: continue`, `reached[...] = child` |
| 7. Repeat | the `while` loop |

**Counting "nodes expanded":** the counter goes up only *after* the goal test fails and just before the children are generated. A goal node is therefore never counted, which matches the PDF's definition.

### 2.6 Worked example: watching the frontier change (CoCIS → School of the Built Environment)

Notation: `PLACE(path cost)`. The frontier is listed with **the next node to be removed first**.

**BFS (queue, front → back)**

| Step | Removed | Added | Queue afterwards |
|---|---|---|---|
| start | | | CoCIS(0) |
| 1 | CoCIS(0) | CTF(1), ENG(1), SSP(1) | CTF(1), ENG(1), SSP(1) |
| 2 | CTF(1) | CoCIS(2), FS(2) | ENG(1), SSP(1), CoCIS(2), FS(2) |
| 3 | ENG(1) | MT(2), SBE(2) | SSP(1), CoCIS(2), FS(2), MT(2), SBE(2) |
| 4 | SSP(1) | ECON(2) | CoCIS(2), FS(2), MT(2), SBE(2), ECON(2) |
| 5 | CoCIS(2) | nothing (all reached) | FS(2), MT(2), SBE(2), ECON(2) |
| 6 | FS(2) | MB(3), ML(3), LAW(3) | MT(2), SBE(2), ECON(2), MB(3), ML(3), LAW(3) |
| 7 | MT(2) | LPA(3) | SBE(2), ECON(2), MB(3), ML(3), LAW(3), LPA(3) |
| 8 | **SBE(2): goal** | | → route CoCIS → ENG → SBE, **2 hops, 7 expanded** |

**DFS (stack, top → bottom)**

| Step | Removed | Added | Stack afterwards |
|---|---|---|---|
| start | | | CoCIS(0) |
| 1 | CoCIS(0) | CTF(1), ENG(1), SSP(1) | CTF(1), ENG(1), SSP(1) |
| 2 | CTF(1) | CoCIS(2), FS(2) | CoCIS(2), FS(2), ENG(1), SSP(1) |
| 3 | CoCIS(2) | nothing (all reached) | FS(2), ENG(1), SSP(1) |
| 4 | FS(2) | MB(3), ML(3), LAW(3) | MB(3), ML(3), LAW(3), ENG(1), SSP(1) |
| 5 | MB(3) | LPA(4), SSS(4) | LPA(4), SSS(4), ML(3), LAW(3), ENG(1), SSP(1) |
| 6 | LPA(4) | MT(5) | MT(5), SSS(4), ML(3), LAW(3), ENG(1), SSP(1) |
| 7 | MT(5) | SBE(6) | SBE(6), SSS(4), ML(3), LAW(3), ENG(1), SSP(1) |
| 8 | **SBE(6): goal** | | → route CoCIS → CTF → FS → MB → LPA → MT → SBE, **6 hops, 7 expanded** |

What to notice:
- **BFS** works through all the cost-1 nodes before any cost-2 node, so the first goal it removes is the closest one.
- **DFS** always continues from the newest node. ENG(1), one step from the goal, stays at the bottom of the stack the whole time, so DFS takes a 6-hop detour.
- CoCIS appears **twice** (cost 0 and cost 2). That's because the lecture says `reached` *starts empty*, so the start state isn't recorded until it is generated again as a child. It is a good real example of **one state appearing in two different nodes** (Part A).

(Abbreviations: CTF Central Teaching Facility, ENG Engineering, SSP Statistics and Planning, FS Freedom Square, MT Margaret Trowell, SBE Built Environment, ECON Economics, MB Main Building, ML Main Library, LAW Law, LPA Liberal and Performing Arts, SSS Social Sciences.)

### 2.7 The user interface: B3

| Function | Job |
|---|---|
| `list_schools()` | Prints the 14 schools numbered 1–14 (alphabetical) |
| `match_school(text)` | Accepts a number **or** a name. Names are matched after `strip()` + `casefold()`, so case and extra spaces don't matter |
| `parse_algorithm(text)` | Accepts `bfs`/`BFS`/` Dfs ` etc. |
| `ask(prompt, parse)` | Keeps asking until the input is valid, and exits cleanly on Ctrl+C or end of input instead of crashing |
| `format_result()` | Prints the exact output format from the PDF |
| `main()` | Reads the `--tree` flag, asks the three questions and prints the result |

---

## 3. How each part of `assign1.pdf` is answered

### Section 1: The Problem

| Requirement | Where | How |
|---|---|---|
| User supplies source school, destination school and algorithm | `main()` | Three interactive prompts |
| Program prints the route | `format_result()` | `Route: A -> B -> ...` |
| Every hop costs 1; cost = number of hops | `RouteProblem.step_cost()` returns 1; `expand()` adds it | `Cost (hops)` = the goal node's `path_cost` |

### Section 2: The Campus Graph

| Requirement | Where | How |
|---|---|---|
| 14 schools, 4 landmarks | `SCHOOLS`, `LANDMARKS` | Copied from the PDF |
| 24 edges, unchanged | `EDGES` | Copied exactly from the PDF |
| Connections are two-way | `build_graph()` | Adds each edge in both directions |
| Landmarks can be walked through but are not schools | `match_school()` | Routes may pass through landmarks, but a landmark is rejected as a source or destination with a clear message |

### Part A: Formulate (report, section 1)

| Requirement | Answer in the report |
|---|---|
| 1. Initial state (+ type) | s₀ ∈ S, the source school. **Type:** one element of the set S (S = the 18 places) |
| 2. Actions(s) (+ how read off the graph) | Actions(s) = { Go(x) : {s, x} ∈ E }: every edge containing s **in either position**; the other end is a legal move. **Type:** function S → set of actions. Example: Actions(Main Library) |
| 3. Result(s, a) | Result(s, Go(x)) = x. **Type:** function S × A → S |
| 4. Goal test | IsGoal(s) = (s = g). **Type:** Boolean test |
| 5. Path cost, and why step cost is 1 | Sum of step costs, each 1, so cost = hops. Step cost is 1 because the model measures routes by number of walks between adjacent places and deliberately ignores distance. **Type:** function path → integer |
| Abstraction: 3 ignored details, valid and useful | Ignores distance/walking time, terrain/slope/stairs, weather/crowds/traffic/time of day. *Valid*: every abstract step is a real walkable link. *Useful*: shrinks the world to 18 states and 24 edges |
| State vs node example | Main Library reached by MB→ML (parent MB, cost 1) and by MB→FS→ML (parent FS, cost 2): same state, two nodes. The program also shows CoCIS appearing as two nodes (see §2.6) |

### Part B1: Data structures (15 marks)

| Requirement | Where |
|---|---|
| `Node` with STATE, PARENT, ACTION, PATH-COST | `class Node` |
| `solution(node)` following PARENT pointers | `def solution(node)` |
| `reached` dictionary state → node | `reached = {}` inside `search()` |

### Part B2: Generic search loop (20 + 15 marks)

| Requirement | Where / how |
|---|---|
| **One** search function, the seven steps, strategy as a parameter | `search(problem, strategy, ...)`; see the table in §2.5 |
| BFS and DFS differ **only** in frontier discipline | `STRATEGIES[strategy]` is the only line that uses the strategy; the rest is shared |
| BFS = queue (FIFO), remove from front | `FIFOQueue.remove()` → `popleft()` |
| DFS = stack (LIFO), remove from back | `LIFOStack.remove()` → `pop()` |
| Goal test when a node is **removed** | Step 4, right after `frontier.remove()` |
| "Nodes expanded" = removed, not goal, children generated | `expanded += 1` is placed after the goal test |
| Neighbours in **alphabetical order** | `build_graph()` sorts the lists |
| DFS explores the alphabetically first neighbour first | `LIFOStack.add_all()` pushes in reverse |
| Switch to turn `reached` off | `use_reached=False` argument / `--tree` flag |
| Safety cap of 10,000 expansions | `MAX_EXPANSIONS = 10_000`; checked every loop |
| No `networkx` or search library | Only `sys` and `collections.deque` are imported |

### Part B3: User interface (10 marks)

| Requirement | How it is met | Example |
|---|---|---|
| Interactive prompts for source, destination, algorithm | `ask(...)` ×3 in `main()` | |
| Exact output format | `format_result()` | `Algorithm:` / `Route:` / `Cost (hops):` / `Nodes expanded:` |
| Case-insensitive, ignore leading/trailing spaces | `normalise()` = `strip().casefold()` | `"  cocis "` → CoCIS |
| Unknown place → clear message + list valid places, no crash | `match_school()` | `Unknown place: 'hogwarts'.` then the list |
| Unknown algorithm → clear message, no crash | `parse_algorithm()` | `Unknown algorithm: 'astar'. Please enter BFS or DFS.` |
| Source = destination → one-place route, cost 0 | Falls out naturally: the root passes the goal test immediately | `Route: CoCIS`, `Cost (hops): 0`, `Nodes expanded: 0` |
| No route → `No route found.` | `format_result()` when `result.node is None` | (The campus graph is connected, so this only happens in `--tree` mode at the cap, or on a test graph) |
| Extra | Number input 1–14; landmark-as-school message; clean exit on Ctrl+C | |

### Part B4: Verify the reached table (5 marks; report, section 2)

Run DFS CoCIS → School of Law in both modes:

| Mode | Result |
|---|---|
| `python route_finder.py` | Route CoCIS → CTF → FS → Law, 3 hops, 16 expanded |
| `python route_finder.py --tree` | `No route found.`, stopped at the 10,000 cap, and the stack had grown to 20,001 nodes |

**Why:** CoCIS's first neighbour (alphabetically) is CTF, and CTF's first neighbour is CoCIS. Without `reached`, DFS keeps regenerating them and walks CoCIS → CTF → CoCIS → CTF → … forever. The cycle makes the search tree infinite even though there are only 18 states. **With `reached`**, each state enters the frontier at most once (the start state at most twice), so the loop is impossible.

### Part C: Results table (5 marks; report, section 3)

The report has 10 pairs × 2 algorithms = 20 rows. Required conditions:

| Condition | Pairs in the table |
|---|---|
| ≥ 2 pairs where BFS and DFS give **different routes** | Pairs 5–10 (six pairs) |
| ≥ 1 pair of **directly connected** schools | Pair 1 (Economics–Law), Pair 2 (CoCIS–Engineering) |
| ≥ 1 pair **at least 6 hops** apart | Pair 9 (6 hops), Pair 10 (9 hops) |

All the numbers came from running the program. To reproduce any row, run the program with that pair.

### Section 4: Report

| Report section | Where | Key points |
|---|---|---|
| 1. Problem formulation | report §1 | Part A, as above |
| 2. Design + diagram/pseudocode | report §2 | Node, reached, frontier classes; pseudocode of the loop; B4 table |
| 3. Results table | report §3 | 20 rows with an abbreviation key |
| 4a. Why BFS is optimal; condition | report §4.1 | FIFO removes nodes in order of depth. **Condition: all actions have the same cost.** Checked on all 182 ordered pairs: BFS optimal in 182/182 |
| 4b. DFS longer than BFS: draw both routes and explain | report §4.2 | CoCIS → Built Environment: 2 vs 6 hops, with a graph figure. DFS follows CTF first (alphabetical), and ENG stays buried in the stack |
| 4c. Is DFS always cheaper in nodes expanded? | report §4.3 | **No.** Economics → Law: DFS 17 vs BFS 2. Over 182 pairs DFS expanded more in 53 |
| 4d. Memory trade-off | report §4.4 | Hubs (MB, FS, ML have degree 4) and cycles widen BFS's frontier. Tree-like BFS Engineering → Vet held 18,435 nodes at once. Memory fills before time runs out |
| 4e. Limitation of equal costs; which algorithm | report §4.5 | Hops ≠ metres. Use **uniform-cost search** (best-first, f(n) = g(n)) |
| 5. Reflection | report §5 | Use measured walking times, including slope (uphill ≠ downhill) |

### Section 5: Marking scheme checklist

| Component | Marks | Covered by |
|---|---|---|
| Part A formulation, abstraction, state vs node | 15 | report §1 |
| Node, solution(), reached | 15 | `Node`, `solution()`, `reached` |
| Single generic loop; BFS/DFS differ only in frontier | 20 | `search()` + `STRATEGIES` |
| Correct routes, costs, expansion counts (alphabetical) | 15 | Sorted adjacency + reversed stack push. Matches the lecturer's worked example (Law → Margaret Trowell: BFS 4 hops, DFS 5 hops) |
| Interface, output format, error handling | 10 | `main()`, `match_school()`, `parse_algorithm()`, `format_result()` |
| Tree-like vs graph demonstration (B4) | 5 | `--tree` flag + report §2 |
| Results table meets Part C conditions | 5 | report §3 |
| Analysis quality and evidence | 12 | report §4 |
| Code clarity, comments, presentation | 3 | Sectioned, commented code; formatted report |
| **Deductions avoided** | | No hard-coded routes; no graph or search library |

### Section 6: Notes

| Note | Status |
|---|---|
| Distances/coordinates must not influence the algorithms | None are used; every hop costs 1 |
| DFS's route is never cheaper than BFS's | Confirmed on all 182 pairs |
| File naming | **To do:** rename to `<StudentNo>_route_finder.py` and `<StudentNo>_report.pdf` |

---

## 4. Design decisions to be ready to explain

1. **`reached` starts empty** (lecture step 1). As a result the start state can be generated once more as a grandchild and expanded twice (see CoCIS in §2.6). This follows the lecture literally. The textbook version adds the start state to `reached` at the beginning, which would lower some expansion counts by one.
2. **`reached` is updated when a child is *generated***, not when it is expanded (lecture step 6). BFS stays optimal because, in FIFO order, a state is first generated at its smallest depth.
3. **Landmarks are rejected as source/destination**, because the PDF asks for a source and destination *school*. To allow them, return `LANDMARK_LOOKUP[key]` in `match_school()`.
4. **The cap is checked in both modes.** With `reached` on, it is never reached (at most ~19 expansions on this graph).

---

## 5. Before submitting

- [ ] Fill in your name and student number at the top of `report.html`, then regenerate `report.pdf` (open it in Edge → Ctrl+P → Save as PDF, with headers and footers off).
- [ ] Rename the files to `<StudentNo>_route_finder.py` and `<StudentNo>_report.pdf`.
- [ ] Run the program a few times yourself, including `--tree`, so you can explain the results.
- [ ] Submit **only** those two files on MUELE.
