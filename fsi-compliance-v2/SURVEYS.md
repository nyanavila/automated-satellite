# AAP Survey Specs

Paste each of these into the corresponding Job Template's Survey config
(Job Template -> Survey tab -> Create Survey, then add questions matching
these variable names exactly).

**Never put secrets in a Survey.** `satellite_password`, `aap_password`,
`anthropic_api_key`, `redhat_offline_token` stay in the Job Template's
Variables field (or better, an AAP Credential), never a Survey field a
person types into at launch time.

## Template: FSI - Create Compliance Policy

| Variable | Question | Type | Required |
|---|---|---|---|
| `policy_name` | Policy name (e.g. fsi-pci-dss-rhel9) | Text | Yes |
| `policy_description` | Policy description | Text | Yes |
| `scap_content_id` | SCAP content ID (look up: GET /api/compliance/scap_contents) | Integer | Yes |
| `scap_content_profile_id` | SCAP profile ID (look up: GET /api/compliance/scap_content_profiles) | Integer | Yes |
| `period` | Scan schedule | Multiple Choice: weekly, monthly, daily | No (defaults to weekly) |
| `weekday` | Day of week (if weekly) | Multiple Choice: sunday...saturday | No (defaults to sunday) |

## Template: FSI - Assign Hostgroup to Policy

| Variable | Question | Type | Required |
|---|---|---|---|
| `policy_name` | Policy to attach to | Text | Yes |
| `hostgroup_name` | Hostgroup to assign | Text | Yes |

## Template: FSI - Trigger Compliance Scan

| Variable | Question | Type | Required |
|---|---|---|---|
| `target_search` | Satellite host search (e.g. hostgroup = fsi-corebanking-rhel9) | Text | Yes |
| `job_template_name` | Override auto-discovered scan template name | Text | No |

## Template: FSI - Parse Compliance Report / FSI - Remediate High Severity

| Variable | Question | Type | Required |
|---|---|---|---|
| `policy_name` | Which policy's results to parse | Text | Yes (else falls back to OS-version guess) |

## Template: FSI - CVE Triage

| Variable | Question | Type | Required |
|---|---|---|---|
| `known_exploit_only` | Only show actively-exploited CVEs? | Multiple Choice: Yes, No | No (defaults to showing all) |
