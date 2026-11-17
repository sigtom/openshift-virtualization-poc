# Recording outline

Follow the [customer walkthrough](RUNBOOK.md). Aim for roughly 20–30 minutes,
allowing for guest boot and migration time. Use the web console as the main
view; open the walkthrough's CLI panels only when showing an equivalent command.

## Before recording — administrator

- Complete [preparation](ADMIN-GUIDE.md#prepare).
- Start with five Stopped VMs and prepared disks, with no lab labels on workers.
- Agree the shared-descheduler change window and who will restore it.
- Keep the administrator guide open for the Predictive and Automatic checkpoints.
- Hide any environment information that should not appear in the recording.

## Recording order

| Scene | Show | Explain |
| --- | --- | --- |
| 1. Introduce the lab | Five Stopped RHEL VMs in the project | “We will try familiar placement and migration tasks.” |
| 2. Approved host | Add the eligible label to Worker A; start placement-01 there | “The VM can start only on an approved host.” |
| 3. Separation | Label the three-worker pool; start spread-01..03; compare their nodes | “Hard anti-affinity keeps these VMs apart.” Stop them after showing the result. |
| 4. Impossible rule | Start negative-01; show FailedScheduling; stop it | “An impossible must-run rule is refused rather than ignored.” |
| 5. Manual move — optional | Make Worker B eligible; migrate placement-01 to it | “This is a person-requested move, like manual vMotion.” |
| 6. Predictive checkpoint | Administrator confirms the lab profile and HCO health; show Predictive mode | “This reports a proposed move without performing it.” |
| 7. Create a violation | Record guest identity; make TARGET eligible, then remove SOURCE eligibility | “The VM keeps running until something corrects the rule violation.” |
| 8. Show the proposal | Node-affinity dry-run log; VM still on SOURCE | “The descheduler has detected the problem.” |
| 9. Automatic checkpoint | Administrator repeats isolation checks, enables Automatic; migration Succeeded | “The rule violation caused a live migration.” |
| 10. Stop automation | Immediately return to Predictive and verify dry-run mode | “The agreed automatic test window is closed.” |
| 11. Prove continuity | Same guest boot ID, greater uptime and unchanged running-instance ID | “The guest moved without restarting.” |
| 12. Finish | Results sheet; administrator restores shared settings off camera | “We demonstrated rule correction. CPU-load balancing is a separate test.” |

Read SOURCE from the running VM; do not assume its node after the optional
manual move. The walkthrough gives both branches.

Record web-console verification separately from CLI results. Do not call the
manual move a descheduler result, or claim continuous DRS/CPU balancing.

For another take, the administrator uses [reset](ADMIN-GUIDE.md#reset).
For final teardown, use [restore](ADMIN-GUIDE.md#restore) and
[cleanup](ADMIN-GUIDE.md#cleanup).
