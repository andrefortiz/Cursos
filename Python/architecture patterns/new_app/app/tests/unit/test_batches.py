from datetime import date

from domains.model import Batch, OrderLine


def test_allocating_to_a_batch_reduces_the_available_quantity():
    batch, line = make_bath_and_line('SMALL-TABLE', 20, 2)
    batch.allocate(line)
    assert batch.available_quantity == 18


def test_can_allocate_if_avaiable_greater_then_required():
    batch, line = make_bath_and_line('ELEGANTE-LAMP', 20, 2)
    assert batch.can_allocate(line)


def test_cannot_allocate_if_avaiable_smaller_then_required():
    batch, line = make_bath_and_line('ELEGANTE-LAMP', 2, 3)
    assert batch.can_allocate(line) is False


def test_can_allocate_if_avaiable_equal_then_required():
    batch, line = make_bath_and_line('ELEGANTE-LAMP', 2, 2)
    assert batch.can_allocate(line)


def test_can_deallocate_allocated_lines():
    batch_qty = 20
    batch, line = make_bath_and_line('ELEGANTE-LAMP', batch_qty, 2)
    batch.deallocate(line)
    assert batch.available_quantity == batch_qty


def test_cannot_allocate_if_skus_do_not_match():
    batch = Batch('batch-001', 'ELEGANTE-LAMP', qty=2, eta=date.today)
    line = OrderLine('order-123', 'SMALL-TABLE', 2)
    assert batch.can_allocate(line) is False


def test_allocation_is_idempotent():
    batch, line = make_bath_and_line('ANGULAR-DESK', 20, 2)
    batch.allocate(line)
    batch.allocate(line)
    assert batch.available_quantity == 18


def make_bath_and_line(sku, batch_qty, line_qty):
    return (Batch('batch-001', sku, qty=batch_qty, eta=date.today),
            OrderLine('order-123', sku, line_qty))



