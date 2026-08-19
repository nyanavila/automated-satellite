#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import json
import sys

arf_file = sys.argv[1]
tree = ET.parse(arf_file)
root = tree.getroot()

ns12 = 'http://checklists.nist.gov/xccdf/1.2'
ns11 = 'http://checklists.nist.gov/xccdf/1.1'
ns = ns12

rule_results = root.findall('.//{%s}rule-result' % ns12)
if not rule_results:
    rule_results = root.findall('.//{%s}rule-result' % ns11)
    ns = ns11

rule_defs = {}
for rule in root.findall('.//{%s}Rule' % ns):
    rid = rule.get('id', '')
    severity = rule.get('severity', 'unknown')

    title_el = rule.find('{%s}title' % ns)
    title = title_el.text if title_el is not None else rid

    fixes = []
    needs_reboot = False

    for fix in rule.findall('{%s}fix' % ns):
        system = fix.get('system', '')
        if system in ['urn:xccdf:fix:script:ansible', 'urn:redhat:ansible:roles']:
            content = fix.text or ''
            fixes.append(content)
            # Reboot required if no_reboot_needed tag is ABSENT from the snippet
            # The SSG explicitly tags no_reboot_needed when safe — absence means reboot needed
            if 'no_reboot_needed' not in content:
                # Secondary check: reboot_after_patch or reboot handler present
                if any(kw in content for kw in ['reboot_after_patch', 'ansible.builtin.reboot',
                                                  'grub2-mkconfig', 'dracut', 'kernel']):
                    needs_reboot = True

    # Also check XCCDF fix/@disruption and warning text for reboot flag
    for fix in rule.findall('{%s}fix' % ns):
        if fix.get('disruption', '') == 'reboot':
            needs_reboot = True

    rule_defs[rid] = {
        'title': title,
        'severity': severity,
        'ansible_fix': '\n'.join(fixes),
        'needs_reboot': needs_reboot
    }

failed = []
for rr in rule_results:
    result_el = rr.find('{%s}result' % ns)
    if result_el is None or result_el.text.strip() != 'fail':
        continue
    rid = rr.get('idref', '')
    defn = rule_defs.get(rid, {})
    snippet = defn.get('ansible_fix', '')

    failed.append({
        'id': rid,
        'title': defn.get('title', rid),
        'severity': defn.get('severity', 'unknown'),
        'ansible_snippet': snippet,
        'needs_reboot': defn.get('needs_reboot', False),
        'has_snippet': len(snippet.strip()) > 0
    })

order = {'high': 0, 'medium': 1, 'low': 2, 'unknown': 3}
failed.sort(key=lambda r: order.get(r['severity'], 3))
print(json.dumps(failed))
