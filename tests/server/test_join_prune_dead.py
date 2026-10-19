"""prune_dead (#96): counts seats with no token_hash; deletes nothing."""
from __future__ import annotations

from agent_coord.server.records import join as rec_join


def test_prune_dead_counts_and_deletes_nothing():
    class FakeCur:
        def __init__(self):
            self.sqls = []

        def execute(self, sql, args=None):
            self.sqls.append(sql)

        def fetchone(self):
            # first SELECT count dead, second SELECT all seats
            n_sel = sum(1 for s in self.sqls if s.lstrip().upper().startswith("SELECT"))
            if n_sel <= 1:
                return (3,)
            return (5,)

    class FakeCn:
        def __init__(self):
            self.cur = FakeCur()
            self.committed = False

        def cursor(self):
            return self.cur

        def commit(self):
            self.committed = True

    cn = FakeCn()
    out = rec_join.prune_dead(cn)
    assert out["ok"] is True
    assert out["pruned"] == 0
    assert out["dead"] == 3
    assert out["join_left"] == 5
    assert not cn.committed
    assert not any("DELETE" in s.upper() for s in cn.cur.sqls)
