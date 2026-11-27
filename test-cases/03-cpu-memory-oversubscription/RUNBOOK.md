# CPU and memory sharing: customer walkthrough

**Goal:** compare the same workload with and without other VMs competing for the
host’s CPU and memory. More virtual resources than host capacity is called
*oversubscription*.

**Start with existing VMs.** No new VMs or configuration changes are needed if
[your VMs meet the requirements](ADMIN-GUIDE.md#path-a). Your sheet gives each VM
a role: the **measured VM** runs the workload you compare, and the **competitor
VMs** add the extra demand. Existing VMs keep their names, sizes and hosts; only
the role is new. The administrator
prepares the [results sheet](RESULTS-TEMPLATE.md), tools and graphs first.
[New test VMs](ADMIN-GUIDE.md#prepare) are a fallback.

The CPU and memory walkthroughs were rehearsed on OpenShift 4.22, including three
baseline, loaded and recovery measurements for each comparison. OpenShift 4.21
execution remains unverified; see [verification limits](README.md#walkthrough-verification).
Complete your own results sheet before calling the test passed. A benchmark is
not a production capacity recommendation.

The pictures show the controls and reference output. Private values are covered
with black boxes. Use the VMs, addresses, directory and times on **your results
sheet**; the pictures are not results for your environment.

## 1. Open the VMs and graphs

1. Open **Workloads → Pods** and select the project on your sheet. Then open **Virtualization → VirtualMachines → Virtual machines**. This also works when the VM project filter is disabled.
2. Open the **measured VM**: this runs the workload you will compare. Check its
   **Node** matches the sheet. A node is the physical host running the VM.
3. Open **Console**, use the **VNC console** dropdown to select **Serial console**, wait for connection, click inside the terminal and press **Enter**. Log in with your existing guest account; the optional new test VMs log in automatically. Type commands inside the VM.
4. Open the VM’s **Metrics** tab in another browser tab. Keep the administrator’s
   host CPU, memory and swap graphs open too, filtered to the test node.

   ![Choose Serial console from the console dropdown](images/00-serial-console.png)

   ![VM Metrics: keep CPU and memory graphs open](images/01-vm-metrics.png)

**Expected:** the VMs are Running, their consoles work, and graphs show data.
Keep existing VMs at their current size and location. Start optional new VMs
only when the administrator says they are ready.

Paste **one command at a time** into the guest console, press **Enter**, and wait for
its expected output before continuing. If the existing guest uses a different console,
use the working console the administrator lists on your sheet.

**Every time you log in to a guest** (the measured VM and each competitor), run this
first if your sheet says the helpers are in `~/poc-bin`:

```sh
export PATH="$HOME/poc-bin:$PATH"
command -v poc-sysbench poc-load poc-stats
```

**Expected:** three file paths. A new login does not remember the setting, so repeat it
after every new login. If a path is missing, stop and tell the administrator. Use this PATH line whenever the sheet says helpers are in `~/poc-bin`.
Helpers installed in `/usr/local/bin` need no PATH change.

## 2. Record a baseline

A baseline is the result before adding competing load. Use the measured command
on your sheet. The supplied reference commands are:

```sh
poc-sysbench cpu
poc-sysbench memory
```

- Run the CPU command with no competing load.
- Run memory only when the sheet says **Memory prerequisites approved**. Otherwise
  record **Blocked** and continue with CPU. For new memory fixtures, only the measured
  VM is Running at baseline; existing VMs keep the power states on the sheet.
- Run one command at a time and repeat it three times. If memory uses a different
  measured VM, it needs its own baseline, loaded and recovery measurements.

The default command discards 5 minutes of warm-up, then measures for 15 minutes.
Use the times agreed on your sheet. A shorter example is `poc-sysbench memory 60 300 2`:
60 seconds of warm-up, 300 seconds measured, 2 threads. Keep these values unchanged
in all three phases.

**Expected:** the command finishes and prints `Saved:`. Record the start/end
UTC times, throughput (CPU: events/sec; memory: MiB/sec), and average/95th
percentile/max latency. Higher throughput means more work completed. Lower
latency means less time per operation. Use the same application workload instead
if the sheet specifies one; keep its data size and users unchanged. Scroll up inside the terminal if the throughput
or latency summary is above the visible area.

The helper prints the saved file's path (by default under `/var/tmp`). To read a
result again, replace `SAVED_FILE` below with that printed path:

```sh
grep -E 'events per second|transferred|avg:|max:|95th' SAVED_FILE
```

The reference pictures group saved files into folders such as `~/poc-results/baseline`
for readability. To use that layout, run these before the baseline:

```sh
mkdir -p "$HOME/poc-results/baseline"
export POC_STATE_DIR="$HOME/poc-results/baseline"
```

For later phases, repeat both lines with `loaded` or `recovery` in place of
`baseline`. This changes only where logs are saved. You can also keep the default
folder and use each printed `Saved:` path.

![Reference CPU baseline summary; timestamps redacted](images/02-baseline-result.png)

![Reference memory baseline: three short repeats, with timestamps redacted. Use the warm-up and duration on your sheet](images/14-memory-baseline.png)

With new memory test VMs, keep the competitors Stopped until the loaded phase.

![Memory baseline: the measured VM is Running and its five competitors are Stopped](images/23-memory-baseline-vms.png)

## 3. Add CPU load

1. Check that the **competitor VMs** on your sheet are Running on the **same Node**
   as the measured VM. These VMs provide the extra demand.
2. Open each competitor’s **Serial console**, log in, set the helper path as in
   step 1 if your sheet says so, and run:

   ```sh
   poc-load start cpu 4500
   ```

3. After two minutes, run `poc-load status` in each competitor; expect `RUNNING`.
   Repeat the **CPU** measured command from step 2 three times. Before each repeat,
   check the competitors still report `RUNNING`; otherwise stop and tell the administrator.
   Record its results and the same graph time windows.

   ![Confirm the competitor reports RUNNING](images/03-competitor-running.png)

   ![Compare the same CPU workload under competing load](images/04-loaded-result.png)

4. In each competitor console run `poc-load stop`.

   ![Confirm the competitor has stopped](images/06-competitor-stopped.png)

**Expected:** `Started cpu load` when starting and `Stopped helper-started
processes` when stopping. The load also stops itself after 75 minutes. For each
approved higher load level, repeat this step using the competitors on the sheet.
The measured VM and its command stay unchanged.

## 4. Add memory load

**Only continue when the sheet says “Memory prerequisites approved”.** Otherwise
record **Blocked**. The administrator follows the complete
[memory setup and restore procedure](MEMORY-DENSITY.md); participants do not
change cluster settings. The goal is to compare the measured VM's performance with more
guest RAM assigned than the host has; it does not require any VM to page.

The administrator gives you **one step at a time**. Your sheet lists, for each step, which
VMs hold memory, how many **bytes** each holds (`BYTES`, for example `40G`) and for how many
**seconds** (`SECONDS`). Use exactly those values; do not choose your own. The sheet's
`SECONDS` covers the remaining ramp, settle time and every measured repeat of the step.

Your sheet says which VMs are Running at each phase. Start or stop a VM only when the
sheet or administrator says so. For a competitor, choose **Actions → Control → Start**,
wait for **Running**, and leave the measured VM untouched.

![Reference: all memory VMs are Running before the holds start. Use the VMs and worker recorded on your sheet](images/13-memory-vms-running.png)

Before starting the holds, record the total RAM assigned to the Running VMs and the
host’s physical RAM on the sheet. More assigned than physical RAM confirms memory
overcommit. The administrator’s [assigned-memory graph](ADMIN-GUIDE.md#assigned-memory)
shows how to read it.

1. With CPU load stopped, open each listed VM's serial console. Run this **inside the VM**,
   in the foreground (the prompt does not return until it ends):

   ```sh
   stress-ng --vm 1 --vm-bytes BYTES --vm-hang 0 --timeout SECONDSs --metrics-brief
   ```

   Replace `BYTES` and `SECONDS` with the sheet values and keep the `s` after the number.
   The `--timeout` is mandatory: it ends the load. The command fills that much memory once,
   then holds it without rewriting it, so the host can move idle pages to swap. The
   administrator checks this behaviour on the installed `stress-ng` before the session.
   Leave each console open and untouched while the hold runs. Wait for the administrator
   before adding the next hold.

   ![A reference memory hold has started; the prompt has not returned. The size and timeout come from your sheet](images/15-memory-hold-running.png)

2. Wait the settle time on the sheet. In the measured VM, run the **memory** command from
   step 2 three times while the holds are running. Watch the host memory and swap graphs.
3. **Before each repeat, and again when it ends,** look at each hold's console. The hold is
   active only while `stress-ng` is still running and the prompt has **not** returned. If any
   prompt has returned, tell the administrator; that repeat does not count as loaded.
   `poc-load status` does not show these holds.
4. To stop a hold early press **Ctrl+C** in that console and check the prompt returns. This
   stops only the command you started. Tell the administrator before and after. Ctrl+C did not stop the hold in the rehearsal’s reconnected serial session. If the prompt
   does not return, tell the administrator, who uses the SSH stop procedure; do not keep pressing keys. Participants must not
   stop a VM or use `killall`. Keep every VM that is Running at this phase in that state through
   the holds; a restart or migration of the measured VM makes the comparison invalid.
5. Do the next step on the sheet only when the administrator says so. The administrator
   adds one VM at a time. The administrator stops adding load at the planned safe headroom,
   or when host paging starts, and checks whether a test VM paged. Measure at that level
   when the administrator confirms the load is stable and the agreed limits still hold.
   You do not need paging to measure.

**Abort if a stop limit is reached or the worker becomes Not Ready.** Stop the holds and
tell the administrator. If a console is unreachable or Ctrl+C does not stop the hold, the administrator stops only the
new test VMs. For an existing VM, keep it Running and use the administrator’s
[SSH stop procedure](ADMIN-GUIDE.md#stop-memory-hold). Wait for recovery before doing anything
else; an aborted run does not pass.

**Expected:** every hold stays running through all loaded repeats. On an existing VM,
Ctrl+C, the timeout or the administrator’s SSH stop returns the prompt. On a new competitor,
**Stop** ends the hold and the VM shows **Stopped**. Use the foreground `stress-ng`
command above for this phase.


![Reference memory results under the agreed competing load: three repeats](images/27-memory-loaded-results.png)

**What the numbers mean.** `poc-sysbench memory` is a bandwidth microbenchmark: it measures how
fast a small block moves, not an application's capacity, and its latency is not application
latency. If its throughput **does not change** while the others hold memory, that is a
legitimate result: the measured VM's own pages may not have been swapped. Only the administrator can tell whether the host actually paged (see the
three questions in the [administrator appendix](MEMORY-DENSITY.md)). It does not replace an
application test.

## 5. Check recovery and finish

If the phase was aborted or the worker restarted, record **Fail (aborted)**. The administrator
recovers the worker and restores the settings first. A benchmark after that restart is a
new run, not a recovery result for the failed comparison. **After an abort, stop here and hand off to the administrator.**
The numbered steps below apply only to a comparison that stayed valid.

1. **CPU load:** run `poc-load stop` in each competitor, then check `poc-load status`
   says `NOT running`. **Memory on existing VMs:** press **Ctrl+C** in each hold's
   console and check the prompt returns; keep the VMs Running. `poc-load status`
   does not cover memory holds.
2. **New memory fixtures (Path B):** the administrator can stop the competitor VMs
   to end all their holds. In **VirtualMachines**, select only those competitors,
   then **Actions → Control → Stop**. Wait for **Stopped** and for the administrator
   to confirm the memory is released. Keep the measured VM Running; assigned RAM
   returns to its baseline. Existing VMs (Path A) keep their original power states.
   ![New memory fixtures ready for recovery: five competitors Stopped, measured VM Running](images/29-memory-recovery-vms.png)

3. Wait five minutes after the load is released and the required VMs are Stopped.
   Repeat the measured command three times with the same settings. Complete this
   recovery comparison for each CPU or memory phase that you ran.
4. Record whether throughput and latency returned close to the baseline.

   ![Reference CPU recovery summary after competing load stops](images/09-recovery-result.png)

   ![Reference memory recovery results: all three repeats, including the lower first result](images/28-memory-recovery-results.png)

5. Leave existing VMs as found. Give the sheet to the administrator for
   [cleanup and restoration](ADMIN-GUIDE.md#reset).

   ![Reference: only the newly created test VMs are Stopped and retained for review](images/18-memory-vms-stopped.png)

**Stop the load and contact the administrator** if you see `BLOCKED`, `FAILED`,
`RUN FAILED`, a VM restart, a paused VM, or missing graphs. Keep the error and
time; do not record failed numbers as a successful result. A smaller throughput
result by itself is an observation, not a reason to change the VM.
