import pytest

@pytest.fixture
def priority_queue(get_contract):
    return get_contract('DataStructures/PriorityQueue.sol')

def test_priority_queue(t, priority_queue):
    priority_queue.insert(2)
    priority_queue.insert(5)
    priority_queue.insert(3)
    assert priority_queue.getMin() == 2
    priority_queue.insert(1)
    assert priority_queue.getMin() == 1
    assert priority_queue.delMin() == 1
    assert priority_queue.delMin() == 2
    assert priority_queue.getMin() == 3
    assert priority_queue.delMin() == 3
    assert priority_queue.delMin() == 5
