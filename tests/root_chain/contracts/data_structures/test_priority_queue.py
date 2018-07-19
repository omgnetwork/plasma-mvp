import pytest
from ethereum.tools.tester import TransactionFailed


@pytest.fixture
def priority_queue(get_contract):
    return get_contract('PriorityQueue')


def test_priority_queue_get_min_empty_should_fail(priority_queue):
    with pytest.raises(TransactionFailed):
        priority_queue.getMin()


def test_priority_queue_insert(priority_queue):
    extra_value = 12345
    priority_queue.insert(2, extra_value)
    assert priority_queue.getMin() == [2, extra_value]
    assert priority_queue.currentSize() == 1


def test_priority_queue_insert_multiple(priority_queue):
    extra_value = 12345
    priority_queue.insert(2, extra_value)
    priority_queue.insert(5, extra_value)
    assert priority_queue.getMin() == [2, extra_value]
    assert priority_queue.currentSize() == 2


def test_priority_queue_insert_out_of_order(priority_queue):
    extra_value = 12345
    priority_queue.insert(5, extra_value)
    priority_queue.insert(2, extra_value)
    assert priority_queue.getMin() == [2, extra_value]


def test_priority_queue_delete_min(priority_queue):
    extra_value = 12345
    priority_queue.insert(2, extra_value)
    assert priority_queue.delMin() == [2, extra_value]
    assert priority_queue.currentSize() == 0


def test_priority_queue_delete_all(priority_queue):
    extra_value = 12345
    priority_queue.insert(5, extra_value)
    priority_queue.insert(2, extra_value)
    assert priority_queue.delMin() == [2, extra_value]
    assert priority_queue.delMin() == [5, extra_value]
    assert priority_queue.currentSize() == 0
    with pytest.raises(TransactionFailed):
        priority_queue.getMin()


def test_priority_queue_delete_then_insert(priority_queue):
    extra_value = 12345
    priority_queue.insert(2, extra_value)
    assert priority_queue.delMin() == [2, extra_value]
    priority_queue.insert(5, extra_value)
    assert priority_queue.getMin() == [5, extra_value]
