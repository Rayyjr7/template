#!/usr/bin/env python3

"""Print NOP's IP and current flag IDs for one service."""

import json
import subprocess
import sys


def run_json(*arguments):
    command = ["ecsc2026ad", *arguments, "--json"]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError as error:
        raise RuntimeError("ecsc2026ad is not installed or not in PATH") from error
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"command timed out: {' '.join(command)}") from error

    if result.returncode != 0:
        detail = result.stderr.strip() or f"exit status {result.returncode}"
        raise RuntimeError(detail)

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("ecsc2026ad returned invalid JSON") from error


def find_nop_ip():
    teams = run_json("teams", "--grep", "NOP")
    if not isinstance(teams, list):
        raise RuntimeError("unexpected teams JSON format")

    # Prefer an exact name match, but retain substring/affiliation matches from
    # --grep when there is exactly one unambiguous result.
    exact = [team for team in teams if str(team.get("name", "")).casefold() == "nop"]
    matches = exact or teams
    if not matches:
        raise RuntimeError("could not find the NOP team")
    if len(matches) != 1:
        names = ", ".join(str(team.get("name", "?")) for team in matches)
        raise RuntimeError(f"NOP team lookup is ambiguous: {names}")

    team_ip = matches[0].get("ip")
    if not isinstance(team_ip, str) or not team_ip:
        raise RuntimeError("NOP team entry has no valid IP address")
    return team_ip


def main():
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} service_name", file=sys.stderr)
        return 2

    try:
        nop_ip = find_nop_ip()
        flag_ids = run_json("attack-info", sys.argv[1], nop_ip)
        if not isinstance(flag_ids, list) or not all(
            isinstance(flag_id, str) for flag_id in flag_ids
        ):
            raise RuntimeError("unexpected attack-info JSON format")
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"IP={nop_ip} flag_ids={json.dumps(flag_ids)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
