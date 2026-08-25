# FSI Compliance Playbooks -- v2

Rebuilt from what we actually learned running these live against a real
Satellite 6.18 instance today. See `SURVEYS.md` for how to make each of
these launchable via an AAP Survey instead of hand-edited extra_vars.

## What changed from v1, and why

### 01-create-compliance-policy.yml
**Confirmed working, unchanged in shape.** `POST /api/compliance/policies`
with `scap_content_id`, `scap_content_profile_id`, `deploy_by: ansible`,
`period`, `weekday`, `hostgroup_ids` genuinely succeeds (verified: created
real policies id 3 and id 4). Added: explicit variable validation up front,
proper 422-vs-real-error distinction, and removed the hardcoded PCI-DSS
assumption -- now takes any policy_name/content/profile combination.

**One hard requirement, confirmed by a real error message:** the
`theforeman.foreman_scap_client` Ansible role must be imported into
Satellite before this will work:
```bash
foreman-rake katello:foreman_ansible:import_roles ROLES_NAME='theforeman.foreman_scap_client'
```
Do this once, before the first policy creation attempt.

### 02-assign-hostgroup-to-policy.yml
**Completely rewritten.** The v1 version (`02-assign-hosts-to-policy.yml`)
used `PUT /api/compliance/policies/{id}/hosts/{host_id}` -- **confirmed this
endpoint does not exist** (404, tested live, twice, against real host IDs).
That was an unverified assumption baked into the original playbook.

The new version assigns a **hostgroup** to the policy instead, via
`PUT /api/compliance/policies/{id}` with a `hostgroup_ids` array -- this
matches the policy resource's own confirmed schema (it accepts
`hostgroup_ids` at creation, per the working `01` playbook) and mirrors how
the actual Satellite UI handles this (hostgroups, not per-host assignment,
confirmed by testing in the UI directly).

**You still need hosts to actually be members of the hostgroup** -- that's
a separate, well-established Satellite mechanism (Hosts -> select -> Change
Host Group), not something this playbook does. This playbook only links
the hostgroup to the policy.

### 03-trigger-scan.yml
**Rewritten to discover instead of guess.** v1 hardcoded
`feature: "foreman_openscap.run_scans"` -- **confirmed this does not match
any real job template** ("Template with id '' was not found", tested live).

v2 queries `/api/job_templates` for anything matching scap/compliance/
openscap and uses whatever it finds, rather than a hardcoded name. If your
Satellite instance's real template name is something unexpected, the
playbook's debug output shows you exactly what candidates it found, and you
can override with `-e job_template_name="<exact name>"` to skip discovery
entirely.

**Honest status: not yet confirmed working end-to-end.** We know the old
hardcoded name was wrong; we have not yet confirmed the discovery query
actually finds the right template on your instance. First real run of this
version is the next test, not a confirmed fact.

### 04-parse-arf-and-report.yml / 05-remediate-high-severity.yml
**Minor change only:** `target_policy` now accepts an explicit `policy_name`
override instead of only ever guessing from OS version -- lets you point
these at CIS, HIPAA, or any other policy you create later without editing
the playbook. Otherwise unchanged from the confirmed-authentic
redhat-partner-tech source (04) and the original design (05) -- **neither
has been run against live scan data yet**, since we haven't gotten a
successful scan to complete yet in this session.

## Honest overall status

| Playbook | Confirmed working live | Notes |
|---|---|---|
| 01-create-compliance-policy.yml | Yes | Created real policies id 3, 4 |
| 02-assign-hostgroup-to-policy.yml | No | Rewritten based on schema evidence, not yet tested |
| 03-trigger-scan.yml | No | Rewritten to discover dynamically, not yet tested |
| 04-parse-arf-and-report.yml | No | Blocked on 03 succeeding first (need real scan data) |
| 05-remediate-high-severity.yml | No | Blocked on 04 succeeding first |

**Next actual step**: run `02`, then `03`, in that order, and see what
happens -- these are now built on confirmed API evidence rather than
guesses, but "should work" and "confirmed working" are different claims,
and only the first row of that table has earned the second one.
