# Storage IOPS: customer walkthrough

**Goal:** run one agreed read workload in an existing VM and see its IOPS, throughput and
latency in the guest and in the OpenShift console.

The administrator [prepares and approves](ADMIN-GUIDE.md#prepare) first and gives you the
[results sheet](RESULTS-TEMPLATE.md): VM, project, **directory to use**, graph links and
times. Do not resize, restart, snapshot or migrate the VM. Client console verification is pending.

## 1. Open the VM and the graphs

1. **Virtualization → VirtualMachines**, pick the project and VM on your sheet.
2. **Overview**: confirm **Running**. **Metrics** tab → **Storage**: keep it open, set the
   time range to cover your run. If no storage graph appears, tell the administrator
   (they use **Observe → Metrics** instead).
3. **Console** tab: log in with your existing guest account. Type the commands below there.

**Expected:** VM Running, console prompt. Keep the VM's current workload as it is.

## 2. Find the disk under test

```sh
findmnt -T /APPROVED/DIRECTORY -o SOURCE,TARGET,FSTYPE
lsblk -o NAME,SERIAL,SIZE,TYPE,MOUNTPOINTS
```

**Expected:** a device such as `vda1` or `vdb1` mounted where your directory lives. Write
down the device name and **SERIAL**. The administrator maps it to the VM disk name; if the
sheet says the mapping is unclear, stop (do not guess). The
**root disk** also carries the operating system's own I/O, so its numbers include background noise.

## 3. Record an idle baseline

Do nothing for **at least 2 minutes** (longer if the sheet says so). Write the UTC time: `date -u +%FT%TZ`.

**Expected:** the VM storage graph is flat near zero (or at the existing workload's normal level).

## 4. Measure

**Option A (no installation): the existing approved workload.** Run it exactly as the
sheet says. Record start/end UTC. Skip to step 5.

**Option B: reference workload with `poc-fio`.** If `poc-fio` or `fio` is missing, the
administrator supplies them ([how](ADMIN-GUIDE.md#tools)); no VM restart is needed.

```sh
poc-fio prepare --dir /APPROVED/DIRECTORY
poc-fio status
poc-fio run
```

- `prepare` **writes one new 256 MiB file once** in a fresh hidden folder. It never touches
  existing files. Expected: `Prepared 256 MiB fixture`.
- `run` does 4 KiB random **reads**, one job, queue depth 8, capped at 100 IOPS: **30 s
  warm-up (not counted) + 180 s measured, three times** (about 11 minutes).
- Expected lines like
  `repeat 1  <UTC start> -> <UTC end>  IOPS 99.x  KiB/s 39x  clat mean/p95/p99 ms ...`
  then `Saved:` with a folder name. IOPS near 100 means the cap, not the disk, set the rate.
- Stop early with **Ctrl-C**: only the test process stops; partial results are kept.

## 5. Read the console graphs

For each measured window on your sheet, in **Metrics → Storage** note read/write IOPS,
throughput and latency. Take them from the same UTC window as `poc-fio`. If a graph is missing,
write **not available**; never write 0.

**Expected:** the graphs rise when the workload starts and fall when it ends, at the same times as
your guest figures. The numbers need not match: each layer counts differently (merged or split I/O,
background I/O, caches). Console latency is a virtual-disk average, not the guest's p95/p99.

## 6. Recovery and cleanup

Wait at least 2 minutes idle; note the graph returns to baseline. If you used Option B:

```sh
poc-fio cleanup
```

**Expected:** `Removed the helper-created fixture. Result files were kept.` Give the sheet
and the printed results folder name to the administrator.

## Stop and call the administrator if

- a command prints `ERROR` (read it out; do not retry in a loop),
- the VM restarts, pauses, shows disk errors, or the existing application slows noticeably,
- graphs are missing entirely, or `prepare` says the free space is too low.

Do not record failed runs as results.
