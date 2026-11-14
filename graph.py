from __future__ import annotations

from collections import deque
from collections.abc import Callable, Hashable, Iterable, Iterator, KeysView
from typing import Any, Generic, TypeVar

# The graphs are generic in their vertex type V. In chapter 4 the vertices of
# the interference graph are locations (Variable and Reg from x86_ast); in
# chapter 5 the control-flow graph's vertices are block labels (str).
# Vertices are dictionary keys, so they must be hashable.
#
#     graph: UndirectedAdjList[location] = UndirectedAdjList()
V = TypeVar('V', bound=Hashable)

class Edge(Generic[V]):
    def __init__(self, src: V, tgt: V) -> None:
        self.source = src
        self.target = tgt

    def raw(self) -> tuple[V, V]:
        return (self.source, self.target)

    def flip(self) -> Edge[V]:
        return Edge(self.target, self.source)

    def __repr__(self) -> str:
        return repr(self.raw())

    def __hash__(self) -> int:
        return hash(self.raw())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Edge):
            return NotImplemented
        return self.raw() == other.raw()

################################################################################
# Directed Adjacency List
################################################################################

class DirectedAdjList(Generic[V]):
    def __init__(self, edge_list: Iterable[Edge[V] | tuple[V, V]] = [],
                 vertex_label: Callable[[V], str] | None = None,
                 vertex_text: Callable[[V], str] | None = None,
                 edge_label: Callable[[Edge[V]], str] | None = None,
                 edge_color: Callable[[Edge[V]], str] | None = None) -> None:
        self.out: dict[V, list[V]] = {}
        self.ins: dict[V, list[V]] = {}
        self.vertex_label = vertex_label
        self.vertex_text: Callable[[V], str]
        if vertex_text:
            self.vertex_text = vertex_text
        elif vertex_label:
            self.vertex_text = vertex_label
        else:
            self.vertex_text = lambda v: str(v)
        self.edge_label = edge_label
        self.edge_color = edge_color
        self.edge_set: set[Edge[V]] = set()
        for e in edge_list:
          if isinstance(e, Edge):
            self.add_edge(e.source, e.target)
          else:
            self.add_edge(e[0], e[1])

    def edges(self) -> set[Edge[V]]:
        return self.edge_set

    def vertices(self) -> KeysView[V]:
        #return range(0, self.num_vertices())
        return self.out.keys()

    def num_vertices(self) -> int:
        return len(self.out)

    def adjacent(self, u: V) -> list[V]:
        self.add_vertex(u)
        return self.out[u]

    def add_vertex(self, u: V) -> None:
        if u not in self.out:
            self.out[u] = []
            self.ins[u] = []

    def add_edge(self, u: V, v: V) -> Edge[V]:
        self.add_vertex(u)
        self.add_vertex(v)
        self.out[u].append(v)
        self.ins[v].append(u)
        edge = Edge(u,v)
        self.edge_set.add(edge)
        return edge

    def out_edges(self, u: V) -> Iterator[Edge[V]]:
        for v in self.out[u]:
            yield Edge(u, v)

    def in_edges(self, v: V) -> Iterator[Edge[V]]:
        for u in self.ins[v]:
            yield Edge(u, v)

    def has_edge(self, u: V, v: V) -> bool:
        return Edge(u,v) in self.edge_set

    def remove_edge(self, u: V, v: V) -> None:
        self.out[u].remove(v)
        self.ins[v].remove(u)
        self.edge_set.remove(Edge(u,v))

    def name(self, u: V) -> str:
        if self.vertex_label:
            return self.vertex_label(u)
        else:
            return str(u)

    def named_edge(self, e: Edge[V]) -> tuple[str, str]:
        return (self.name(e.source), self.name(e.target))

    def label(self, e: Edge[V]) -> str:
        if self.edge_label:
            return self.edge_label(e)
        else:
            return ""

    def color(self, e: Edge[V]) -> str:
        if self.edge_color:
            return self.edge_color(e)
        else:
            return "black"

    # Draws the graph with the optional graphviz package (returns a
    # graphviz.Digraph, which displays itself in a notebook).
    def show(self, engine: str = 'neato') -> Any:
      from graphviz import Digraph
      dot = Digraph(engine=engine)
      for u in self.vertices():
          dot.node(self.name(u), self.vertex_text(u))
      for e in self.edges():
          dot.edge(self.name(e.source), self.name(e.target), label=self.label(e),
                   color=self.color(e), len='1.5')
      return dot

class UEdge(Edge[V]):
    # An undirected edge has no direction, so its raw form is a set:
    # UEdge(u, v) == UEdge(v, u). That differs from Edge.raw's tuple, which
    # mypy reports as an incompatible override.
    def raw(self) -> set[V]:  # type: ignore[override]
        return set([self.source, self.target])

    def __hash__(self) -> int:
        return hash(self.source) + hash(self.target)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UEdge):
            return NotImplemented
        return self.raw() == other.raw()


################################################################################
# Undirected Adjacency List
################################################################################

class UndirectedAdjList(DirectedAdjList[V]):

    def add_edge(self, u: V, v: V) -> UEdge[V]:
        self.add_vertex(u)
        self.add_vertex(v)
        self.out[u].append(v)
        self.out[v].append(u)
        edge = UEdge(u,v)
        self.edge_set.add(edge)
        return edge

    def remove_edge(self, u: V, v: V) -> None:
        self.out[u] = [w for w in self.out[u] if w != v]
        self.out[v] = [w for w in self.out[v] if w != u]
        self.edge_set.remove(UEdge(u,v))

    def out_edges(self, u: V) -> Iterator[UEdge[V]]:
        for v in self.out[u]:
            yield UEdge(u, v)

    def in_edges(self, v: V) -> Iterator[UEdge[V]]:
        for u in self.out[v]:
            yield UEdge(u,v)

    def has_edge(self, u: V, v: V) -> bool:
        return UEdge(u,v) in self.edge_set

    # Draws the graph with the optional graphviz package (returns a
    # graphviz.Graph). The engine parameter matches DirectedAdjList.show.
    def show(self, engine: str = 'neato') -> Any:
      from graphviz import Graph
      dot = Graph(engine=engine)
      for u in self.vertices():
        dot.node(self.name(u))
      for e in self.edges():
        dot.edge(self.name(e.source), self.name(e.target), len='1.5')
      return dot


################################################################################
# Topological Sort
################################################################################

def topological_sort(G: DirectedAdjList[V]) -> list[V]:
    in_degree = {u: 0 for u in G.vertices()}
    for e in G.edges():
        in_degree[e.target] += 1
    queue: deque[V] = deque()
    for u in G.vertices():
        if in_degree[u] == 0:
            queue.append(u)
    topo = []
    while queue:
        u = queue.pop()
        topo.append(u)
        for v in G.adjacent(u):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
    return topo

def transpose(G: DirectedAdjList[V]) -> DirectedAdjList[V]:
    G_t: DirectedAdjList[V] = DirectedAdjList()
    for v in G.vertices():
        G_t.add_vertex(v)
    for e in G.edges():
        G_t.add_edge(e.target, e.source)
    return G_t
