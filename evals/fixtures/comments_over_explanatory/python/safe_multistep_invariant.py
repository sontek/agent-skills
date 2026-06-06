def merge(events):
    # Sort by (ts, seq, shard) before merging: ts alone collides on
    # same-millisecond writes, seq is only unique within one shard, and the
    # shard id breaks ties across shards. Dropping any one key reorders
    # concurrent writes — see INC-4821.
    events.sort(key=lambda e: (e.ts, e.seq, e.shard))
    return _fold(events)
