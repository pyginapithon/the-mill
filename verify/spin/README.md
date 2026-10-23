# SPIN models of the mill coordination design

Small models of two parts of the mill, written in the `spin` input language
and checked with the `spin` model checker (from the 1991 book on designing and
validating computer protocols that introduced it).
A test checks the cases someone wrote down. A model check tries every order
in which the steps of the model can interleave, inside the stated bounds.

| File | What it models |
| :--- | :--- |
| `wake.pml` | the wake path: push queue, webhook POST, the 120 s window, the trailing POST (#669), the one immediate retry, connect sync, the seat rule (supersede, `-r` 4409); plus card 827's proposed backoff retry and two proposed fixes, behind switches |
| `holds.pml` | `mill hold` / `mill drop` (refuse at once, no TTL, only the owner drops), with three desk policies for what to do after a refusal |
| `run.sh` | runs every check with fixed flags, compares each result with its expectation, exits nonzero on any difference or tool error (`--strict`: on any violation) |
| `SKILL.md` | how the next agent tells whether a change touches the modelled code, reruns the checks, and updates the models |

Run: `verify/spin/run.sh` (about one minute; needs `spin` 6.5.x and a C
compiler). One check with its trail: `verify/spin/run.sh W07`.

All searches are exhaustive (no `-DBITSTATE`, no depth cut). Liveness checks
run with weak fairness (`pan -a -f`): every process that can always move
eventually moves. The receiver's choice to fail a POST is not covered by
fairness; it is bounded by `MAXFAIL`, the most POSTs in a row it may fail.

## Properties and results (models at commit 4234463)

Wake path, one desk, two or three items:

| Property | Result |
| :--- | :--- |
| One wake per window: a second wake starts only after 120 s or a connect | proved (W01-W03); fails on a mutation that splits the gate take (M01) |
| No invalid end state (deadlock) | proved (W01-W03) |
| No queued item is taken off the queue without reaching the desk | proved with one connect at a time (W04) and with `-r` (W06); **violated** when a new connect supersedes an old one between its take and its send (W05) |
| Every item is eventually delivered | **violated** even with a receiver that never fails (W07); **violated** when both POSTs of a wake fail (W08); proved with no loss and no races (W09) |
| Card 827 retry, bounded at 2 retries (6 POSTs) | proved when at most 5 POSTs in a row fail (W12, W16); violated at 6 (W13) and for a receiver down forever (W17) |

Holds, two or three desks each needing two locks in a cycle:

| Property | Result |
| :--- | :--- |
| Mutual exclusion | proved (H01, H02); fails without `FOR UPDATE` (M03) |
| The mill itself never blocks (no invalid end state) | proved (H03): `mill hold` refuses, it never waits |
| No deadlock as a busy loop, keep-and-retry policy | **violated** (H04, H05) |
| No livelock, drop-all-and-retry policy | **violated** (H06) |
| No deadlock or livelock, one global lock order | proved (H07, H08) |
| No starvation | **violated** (H09): no queue, a desk can lose every race; proved for finite work (H10) |
| A dead desk's holds | **violated** (H11): no TTL and only the owner can drop |

## Findings in the code's words

1. **Row queued after the wake (W07).** `emit` and `fanout` read
   `HUB.rooms`, call `post_desk`, and only then `rec_push.put`
   (push.py 565-587, 453-489). A woken run can connect and sync in between
   (likely when the first POST times out after the receiver got it, and the
   immediate retry takes up to 8 s more). Its sync finds no row, clears the
   window, and the row lands after it: no later POST, the desk never hears of
   the item until something else connects it.
2. **Sitting read vs. leave (W07 with `PUTFIRST`).** An item that finds the
   desk sitting gets no POST; if the desk's last socket leaves before the
   broadcast or the desk's next sync, the row waits with no wake.
   `PUTFIRST` + `RING_ON_LEAVE` (queue first; when the last socket leaves and
   rows wait, ring as for a new item) close both races (W14-W16).
3. **Take before send (W05).** `connect_sync_frame` deletes the rows
   (`mill_push_take`) and the handler sends the frame after (asgi.py 609-616).
   A newer connect of the same desk supersedes the old socket in between; the
   old send fails and those rows are gone. Any failed send after the take
   does the same; a command reply (asgi.py 633-636) has the same order.
   sync.md says "A deleted list is not sent again"; connect.md says
   "Nothing is lost".
4. **A failed wake is two back-to-back POSTs, then nothing (W08).** The window
   is taken before the POST (wake.py 636), so after a failure only a trailing
   POST can follow, and only if another item arrives inside the window. The
   docs (connect.md, wake.py docstring) say "a burst is never left asleep".
5. **Card 827 needs a job id (M02).** A retry must stop only its own chain;
   otherwise a late success of an old retry cancels the chain of a newer
   failed wake. Bounded retries prove delivery only under a bounded-loss
   assumption: fewer lost POSTs in a row than the budget has POSTs.
6. **Wall restart (W11).** `_GATE`, `_TRAIL` and the timer threads are memory
   only: a restart can send a second POST inside 120 s, and drops a pending
   trailing POST (rows survive in `push_queue`).
7. **Receipts never ring (W10).** By design (push.py 573); a receipt waits
   for the desk's next connect.
8. **Holds.** No TTL, no break by anyone but the owner; reset seat, retire
   and a superseded connect leave holds held. No queue: starvation possible.
   Agents that need two locks must take them in one global order, and must
   not spin on a refused hold.

## What is not modelled

- Time beyond "the window has ended or not"; the 30-day expiry sweep.
- A crash between a commit and its `after_commit` pokes (push.py 421, 550):
  the row is never queued.
- The client's 256-frame sit buffer and `note_drop` put-back.
- `--wake-on addressed` (room-only items skip the POST), refused or
  non-public URLs (no window taken), the join test POST (never takes a window).
- InnoDB. Two first-time holds of a new resource can deadlock on gap locks
  (1213); #818 retries once (records/db.py 193-199, 498-520) and the unique
  `idx_hold` keeps one owner. The model treats each stored procedure as one step.
- A receiver that answers 2xx is assumed to start a run that connects.
