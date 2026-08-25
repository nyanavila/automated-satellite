#!/usr/bin/env python3
"""
Parses an OpenSCAP ARF (Asset Reporting Format) XML file and emits JSON
describing every failed rule: id, title, severity, whether a remediation
fix (bash/ansible) snippet is available, and whether it needs a reboot.

Usage: parse_arf.py /path/to/report.xml
"""
import sys
import json
import xml.etree.ElementTree as ET

NS = {
    "xccdf": "http://checklists.nist.gov/xccdf/1.2",
    "arf": "http://scap.nist.gov/schema/asset-reporting-format/1.1",
}

REBOOT_KEYWORDS = ("kernel", "grub", "reboot", "fips", "crypto-policy")


def find_test_result(root):
    for tr in root.iter("{http://checklists.nist.gov/xccdf/1.2}TestResult"):
        return tr
    return None


def main():
    if len(sys.argv) != 2:
        print("Usage: parse_arf.py <arf.xml>", file=sys.stderr)
        sys.exit(1)

    tree = ET.parse(sys.argv[1])
    root = tree.getroot()

    test_result = find_test_result(root)
    if test_result is None:
        print(json.dumps([]))
        return

    # Build a lookup of rule id -> (title, severity) from the Benchmark section
    rule_meta = {}
    for rule in root.iter("{http://checklists.nist.gov/xccdf/1.2}Rule"):
        rule_id = rule.get("id")
        severity = rule.get("severity", "unknown")
        title_el = rule.find("{http://checklists.nist.gov/xccdf/1.2}title")
        title = title_el.text if title_el is not None else rule_id
        has_fix = rule.find("{http://checklists.nist.gov/xccdf/1.2}fix") is not None
        rule_meta[rule_id] = {
            "title": title,
            "severity": severity,
            "has_snippet": has_fix,
        }

    failed = []
    for result in test_result.findall("{http://checklists.nist.gov/xccdf/1.2}rule-result"):
        if result.get("result", result.findtext(
            "{http://checklists.nist.gov/xccdf/1.2}result", default=""
        )) not in ("fail",):
            # some ARF variants put result as a child element instead of attribute
            result_el = result.find("{http://checklists.nist.gov/xccdf/1.2}result")
            status = result_el.text if result_el is not None else None
            if status != "fail":
                continue

        rule_id = result.get("idref")
        meta = rule_meta.get(rule_id, {"title": rule_id, "severity": "unknown", "has_snippet": False})
        title_lower = meta["title"].lower()
        needs_reboot = any(k in title_lower or k in (rule_id or "").lower() for k in REBOOT_KEYWORDS)

        failed.append({
            "id": rule_id,
            "title": meta["title"],
            "severity": meta["severity"],
            "has_snippet": meta["has_snippet"],
            "needs_reboot": needs_reboot,
        })

    print(json.dumps(failed))


if __name__ == "__main__":
    main()
