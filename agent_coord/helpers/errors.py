"""Errors the mill app and the wall both raise. No SQL."""


class CoordError(Exception):
    """Mill error. sync is the push report that rode with a failed verb.

    envelope, when set, is the full host failure reply (ok/mill/id/result/error/sync)
    so the CLI can print the same object the wire carried.
    """

    def __init__(self, *args, sync: list | None = None, envelope: dict | None = None):
        super().__init__(*args)
        self.sync = sync
        self.envelope = envelope


class HoldHeld(CoordError):
    def __init__(self, resource: str, holder: dict):
        self.resource = resource
        self.holder = holder
        super().__init__(f"{resource} held by {holder.get('owner')}")


LockHeld = HoldHeld
