from __future__ import annotations

from collections.abc import Callable, Hashable
from typing import Generic, TypeVar

# A max-priority queue of keys (in chapter 4, the variables to color, ordered
# by saturation). `less` compares two KeyWithPosition objects; read the key
# with `.key`. pop() returns the key that is greatest according to `less`.
# After something changes that makes a key greater (a variable's saturation
# grows), call increase_key(key) to move it up in the queue.
#
#     Q: PriorityQueue[Variable] = PriorityQueue(lambda a, b: sat[a.key] < sat[b.key])

K = TypeVar('K', bound=Hashable)   # keys of a PriorityQueue
T = TypeVar('T')                   # elements of a Heap

class PriorityQueue(Generic[K]):
    def __init__(self, less: Callable[[KeyWithPosition[K], KeyWithPosition[K]], bool]) -> None:
        self.heap: Heap[KeyWithPosition[K]] = Heap([], less, update_position)
        self.get_key_and_pos: dict[K, KeyWithPosition[K]] = {}

    def __repr__(self) -> str:
        return repr(self.heap)

    def push(self, key: K) -> None:
        kp = KeyWithPosition(key)
        self.get_key_and_pos[key] = kp
        self.heap.insert(kp)

    def pop(self) -> K:
        return self.heap.extract_max().key

    def increase_key(self, key: K) -> None:
        obj = self.get_key_and_pos[key]
        heap_increase_key(self.heap, obj.position)

    def empty(self) -> bool:
        return self.heap.heap_size == 0

class KeyWithPosition(Generic[K]):
    def __init__(self, k: K) -> None:
        self.key = k
        self.position = -1

    def __repr__(self) -> str:
        return str(self.key) + '@' + repr(self.position)

def update_position(key_with_pos: KeyWithPosition[K], pos: int) -> None:
    key_with_pos.position = pos

class Heap(Generic[T]):
    def __init__(self, data: list[T], less: Callable[[T, T], bool],
                 update: Callable[[T, int], None]) -> None:
        self.data = data
        self.less = less
        self.update = update
        self.heap_size = 0  # set by build_max_heap below
        i = 0
        for obj in self.data:
            self.update(obj, i)
            i += 1
        build_max_heap(self)

    def __repr__(self) -> str:
        return repr(self.data[:self.heap_size])

    def maximum(self) -> T:
        return self.data[0]

    def insert(self, obj: T) -> None:
        self.heap_size += 1
        if len(self.data) < self.heap_size:
            self.data.append(obj)
        else:
            self.data[self.heap_size - 1] = obj
        self.update(obj, self.heap_size - 1)
        heap_increase_key(self, self.heap_size - 1)

    def extract_max(self) -> T:
        assert self.heap_size != 0
        max = self.data[0]
        self.data[0] = self.data[self.heap_size-1]
        self.update(self.data[0], 0)
        self.heap_size -= 1
        max_heapify(self, 0)
        return max

def left(i: int) -> int:
    return 2 * i + 1

def right(i: int) -> int:
    return 2 * (i + 1)

def parent(i: int) -> int:
    return (i-1) // 2

def swap(A: list[T], i: int, j: int) -> None:
    tmp = A[i]
    A[i] = A[j]
    A[j] = tmp

def heap_increase_key(H: Heap[T], i: int) -> None:
    while i > 0 and H.less(H.data[parent(i)], H.data[i]):
        swap(H.data, i, parent(i))
        H.update(H.data[i], i)
        H.update(H.data[parent(i)], parent(i))
        i = parent(i)

def max_heapify(H: Heap[T], i: int) -> None:
    l = left(i)
    r = right(i)
    if l < H.heap_size and H.less(H.data[i], H.data[l]):
        largest = l
    else:
        largest = i
    if r < H.heap_size and H.less(H.data[largest], H.data[r]):
        largest = r
    if largest != i:
        swap(H.data, i, largest)
        H.update(H.data[i], i)
        H.update(H.data[largest], largest)
        max_heapify(H, largest)

def build_max_heap(H: Heap[T]) -> None:
    H.heap_size = len(H.data)
    last_parent = len(H.data) // 2
    for i in range(last_parent, -1, -1):
        max_heapify(H, i)

def heap_sort(H: Heap[T]) -> None:
    build_max_heap(H)
    for i in range(len(H.data)-1, 0, -1):
        swap(H.data, 0, i)
        H.update(H.data[0], 0); H.update(H.data[i], i)
        H.heap_size -= 1
        max_heapify(H, 0)

def less(x: int, y: int) -> bool:
    return x < y

def ignore_update(obj: object, pos: int) -> None:
    pass

if __name__ == "__main__":
    # test Heap build and extract_max
    L = [4,3,5,1,2]
    h = Heap(L, less, ignore_update)
    for i in range(5, 0, -1):
        assert h.extract_max() == i

    # test Heap insert
    L = [4,3,5,1,2]
    for n in L:
        h.insert(n)
    for i in range(5, 0, -1):
        assert h.extract_max() == i

    # test heap_sort
    L = [4,3,5,1,2]
    h = Heap(L, less, ignore_update)
    heap_sort(h)
    for i in range(0, 5):
        assert L[i] == i + 1

    # test PriorityQeueue push and pop
    D = {'a': 4, 'b': 3, 'c':5,'d':1,'e':2}
    def less_by_D(x: KeyWithPosition[str], y: KeyWithPosition[str]) -> bool:
        return D[x.key] < D[y.key]
    Q = PriorityQueue(less_by_D)
    for k, v in D.items():
        Q.push(k)
    P = ['c', 'a', 'b', 'e', 'd']
    for i in range(0, len(P)):
        assert Q.pop() == P[i]

    # test increase_key
    Q = PriorityQueue(less_by_D)
    for k, v in D.items():
        Q.push(k)
    for k, v in D.items():
        D[k] = v + 2
        Q.increase_key(k)
    for i in range(5, 0, -1):
        k = Q.pop()
        assert D[k] == i + 2

    print('passed all tests')
