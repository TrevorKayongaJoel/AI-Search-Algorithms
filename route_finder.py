"""
CSC 2114 Artificial Intelligence - Practical 1
Makerere Campus Route Finder (BFS and DFS)

A single generic best-first-style search loop (the lecture's seven steps)
is parameterised by the frontier discipline:
    BFS -> queue (FIFO), remove from the front
    DFS -> stack (LIFO), remove from the back

Every hop costs 1, so the path cost of a route is its number of hops.
Standard library only.

Usage:
    python route_finder.py              # interactive, graph search (uses reached)
    python route_finder.py --tree       # interactive, tree-like search (no reached)
"""

import sys
from collections import deque

# ---------------------------------------------------------------------------
# The campus graph (given - do not change)
# ---------------------------------------------------------------------------

LANDMARKS = [
    "Main Building", "Freedom Square", "Main Library", "Central Teaching Facility",
]

SCHOOLS = [
    "CoCIS",
    "School of Engineering",
    "School of the Built Environment",
    "Margaret Trowell School of Industrial and Fine Art",
    "School of Law",
    "School of Education",
    "School of Social Sciences",
    "School of Liberal and Performing Arts",
    "School of Economics",
    "School of Statistics and Planning",
    "College of Natural Sciences",
    "School of Food Technology, Nutrition and Bioengineering",
    "School of Agricultural Sciences",
    "School of Veterinary Medicine",
]

EDGES = [
    ("Main Building", "Freedom Square"), ("Main Building", "Main Library"),
    ("Main Building", "School of Social Sciences"),
    ("Main Building", "School of Liberal and Performing Arts"),
    ("Freedom Square", "Main Library"), ("Freedom Square", "School of Law"),
    ("Freedom Square", "Central Teaching Facility"),
    ("Main Library", "School of Education"), ("Main Library", "School of Economics"),
    ("Central Teaching Facility", "CoCIS"),
    ("Central Teaching Facility", "School of Statistics and Planning"),
    ("CoCIS", "School of Statistics and Planning"), ("CoCIS", "School of Engineering"),
    ("School of Engineering", "School of the Built Environment"),
    ("School of Engineering", "Margaret Trowell School of Industrial and Fine Art"),
    ("School of the Built Environment", "Margaret Trowell School of Industrial and Fine Art"),
    ("Margaret Trowell School of Industrial and Fine Art", "School of Liberal and Performing Arts"),
    ("School of Education", "School of Social Sciences"),
    ("School of Education", "College of Natural Sciences"),
    ("College of Natural Sciences", "School of Food Technology, Nutrition and Bioengineering"),
    ("School of Food Technology, Nutrition and Bioengineering", "School of Agricultural Sciences"),
    ("School of Agricultural Sciences", "School of Veterinary Medicine"),
    ("School of Statistics and Planning", "School of Economics"),
    ("School of Economics", "School of Law"),
]

MAX_EXPANSIONS = 10_000  # safety cap so tree-like search always terminates


def build_graph(edges):
    """Adjacency list for an undirected graph; neighbours sorted alphabetically."""
    graph = {}
    for a, b in edges:
        graph.setdefault(a, set()).add(b)  # connections are two-way,
        graph.setdefault(b, set()).add(a)  # so add both directions
    return {place: sorted(neighbours) for place, neighbours in graph.items()}


GRAPH = build_graph(EDGES)


# ---------------------------------------------------------------------------
# Problem formulation
# ---------------------------------------------------------------------------

class RouteProblem:
    """The five components: initial state, Actions, Result, goal test, path cost."""

    def __init__(self, initial, goal, graph=GRAPH):
        self.initial = initial
        self.goal = goal
        self.graph = graph

    def actions(self, state):
        """Actions(s): one 'walk to X' action per neighbour X, in alphabetical order."""
        return [f"walk to {n}" for n in self.graph.get(state, [])]

    def result(self, state, action):
        """Result(s, a): walking to X puts the agent at X."""
        return action[len("walk to "):]

    def is_goal(self, state):
        """Goal test: are we at the destination?"""
        return state == self.goal

    def step_cost(self, state, action, next_state):
        """Every hop costs exactly 1."""
        return 1


# ---------------------------------------------------------------------------
# B1. Data structures
# ---------------------------------------------------------------------------

class Node:
    """A node in the search tree (not the same thing as a state)."""

    def __init__(self, state, parent=None, action=None, path_cost=0):
        self.state = state            # STATE: the place this node stands for
        self.parent = parent          # PARENT: the node that generated this one
        self.action = action          # ACTION: the action applied to the parent
        self.path_cost = path_cost    # PATH-COST: g(n), hops from the root

    def __repr__(self):
        return f"Node({self.state!r}, cost={self.path_cost})"


def solution(node):
    """Follow PARENT pointers back to the root; return the places in order."""
    path = []
    while node is not None:
        path.append(node.state)
        node = node.parent
    return list(reversed(path))


def expand(problem, node):
    """Generate the child nodes of `node`, in alphabetical order of state."""
    for action in problem.actions(node.state):
        child_state = problem.result(node.state, action)
        cost = node.path_cost + problem.step_cost(node.state, action, child_state)
        yield Node(child_state, node, action, cost)


# ---------------------------------------------------------------------------
# Frontiers: the ONLY difference between BFS and DFS
# ---------------------------------------------------------------------------

class FIFOQueue:
    """BFS frontier: add at the back, remove from the front."""

    def __init__(self):
        self.items = deque()

    def add_all(self, nodes):
        self.items.extend(nodes)

    def remove(self):
        return self.items.popleft()

    def __len__(self):
        return len(self.items)


class LIFOStack:
    """DFS frontier: add at the back, remove from the back.

    Children are pushed in REVERSE order so that the alphabetically first
    child ends up on top of the stack and is explored first.
    """

    def __init__(self):
        self.items = []

    def add_all(self, nodes):
        self.items.extend(reversed(nodes))

    def remove(self):
        return self.items.pop()

    def __len__(self):
        return len(self.items)


STRATEGIES = {"BFS": FIFOQueue, "DFS": LIFOStack}


# ---------------------------------------------------------------------------
# B2. The generic search loop (the lecture's seven steps)
# ---------------------------------------------------------------------------

class SearchResult:
    def __init__(self, node, expanded, cutoff=False):
        self.node = node          # goal node, or None on failure
        self.expanded = expanded  # nodes removed, not the goal, children generated
        self.cutoff = cutoff      # True if the expansion cap was hit

    @property
    def route(self):
        return solution(self.node) if self.node else None

    @property
    def cost(self):
        return self.node.path_cost if self.node else None


def search(problem, strategy, use_reached=True, max_expansions=MAX_EXPANSIONS):
    """Generic search. `strategy` is 'BFS' or 'DFS' and only selects the frontier.

    use_reached=True  -> graph search (repeated states are pruned)
    use_reached=False -> tree-like search (no repeated-state check)
    """
    # Step 1: a node for the initial state on the frontier; reached starts empty.
    frontier = STRATEGIES[strategy]()
    frontier.add_all([Node(problem.initial)])
    reached = {}
    expanded = 0

    # Step 2: if the frontier is empty, return failure (loop exit below).
    while len(frontier) > 0:
        # Step 3: remove a node according to the strategy.
        node = frontier.remove()

        # Step 4: goal test on REMOVAL; return the solution via PARENT pointers.
        if problem.is_goal(node.state):
            return SearchResult(node, expanded)

        if expanded >= max_expansions:
            return SearchResult(None, expanded, cutoff=True)

        # Step 5: expand the node and generate its children.
        expanded += 1
        children = []
        for child in expand(problem, node):
            # Step 6: graph search skips states already in reached; else record them.
            if use_reached:
                if child.state in reached:
                    continue
                reached[child.state] = child
            children.append(child)
        frontier.add_all(children)
        # Step 7: repeat from step 2.

    return SearchResult(None, expanded)


# ---------------------------------------------------------------------------
# B3. User interface
# ---------------------------------------------------------------------------

def normalise(text):
    return text.strip().casefold()


SCHOOL_LOOKUP = {normalise(s): s for s in SCHOOLS}
LANDMARK_LOOKUP = {normalise(p): p for p in LANDMARKS}
NUMBERED_SCHOOLS = sorted(SCHOOLS)  # menu numbers 1..14, in alphabetical order


def list_schools():
    print("Valid places (schools) - type the number or the name:")
    for number, school in enumerate(NUMBERED_SCHOOLS, start=1):
        print(f"  {number:>2}. {school}")


def match_school(text):
    """Return the canonical school name, or None after printing a clear message.

    Accepts either a menu number (1-14) or a school name.
    """
    key = normalise(text)
    if key.isdigit() and 1 <= int(key) <= len(NUMBERED_SCHOOLS):
        return NUMBERED_SCHOOLS[int(key) - 1]
    if key in SCHOOL_LOOKUP:
        return SCHOOL_LOOKUP[key]
    if key.isdigit():
        print(f"There is no school number {key}. Please choose 1-{len(NUMBERED_SCHOOLS)}.")
    elif key in LANDMARK_LOOKUP:
        print(f"'{text.strip()}' is a landmark, not a school. "
              "Landmarks can be walked through but cannot be a source or destination.")
    else:
        print(f"Unknown place: '{text.strip()}'.")
    list_schools()
    return None


def ask(prompt, parse):
    """Keep prompting until `parse` accepts the input. Returns None on EOF."""
    while True:
        try:
            text = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        value = parse(text)
        if value is not None:
            return value


def parse_algorithm(text):
    algorithm = text.strip().upper()
    if algorithm in STRATEGIES:
        return algorithm
    print(f"Unknown algorithm: '{text.strip()}'. Please enter BFS or DFS.")
    return None


def format_result(algorithm, result):
    """The required output format."""
    lines = [f"Algorithm: {algorithm}"]
    if result.node is None:
        lines.append("No route found.")
        if result.cutoff:
            lines.append(f"(Search stopped at the safety cap of {MAX_EXPANSIONS:,} expansions.)")
    else:
        lines.append("Route: " + " -> ".join(result.route))
        lines.append(f"Cost (hops): {result.cost}")
    lines.append(f"Nodes expanded: {result.expanded}")
    return "\n".join(lines)


def find_route(source, destination, algorithm, use_reached=True):
    return search(RouteProblem(source, destination), algorithm, use_reached)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    use_reached = "--tree" not in argv

    print("Makerere Campus Route Finder")
    print("Mode: " + ("graph search (reached table ON)" if use_reached
                      else "tree-like search (reached table OFF)"))
    list_schools()
    print()

    source = ask("Source school: ", match_school)
    if source is None:
        return
    destination = ask("Destination school: ", match_school)
    if destination is None:
        return
    algorithm = ask("Algorithm (BFS or DFS): ", parse_algorithm)
    if algorithm is None:
        return

    print()
    print(format_result(algorithm, find_route(source, destination, algorithm, use_reached)))


if __name__ == "__main__":
    main()
