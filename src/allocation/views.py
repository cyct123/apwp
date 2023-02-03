from allocation.adapters import redis_eventpublisher


def allocations(orderid: str):
    batches = redis_eventpublisher.get_readmodel(orderid)
    return [{"sku": s.decode(), "batchref": b.decode()} for s, b in batches.items()]
