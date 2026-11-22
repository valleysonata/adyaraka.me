"""Fetch GitHub's contribution calendar using authenticated gh; never invent data.

Locally: gh auth login, then py scripts/refresh_github.py.
Actions: GH_TOKEN is supplied by GitHub; credentials never enter the site output.
"""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from sync_layout import sync

ROOT = Path(__file__).resolve().parents[1]
QUERY = '''query { user(login: "valleysonata") {
  contributionsCollection { contributionCalendar {
    totalContributions weeks { contributionDays {
      contributionCount date contributionLevel weekday
    } }
  } }
} }'''


def refresh():
    result = subprocess.run(['gh', 'api', 'graphql', '--input', '-'],
                            input=json.dumps({'query': QUERY}), text=True,
                            capture_output=True, check=True)
    response = json.loads(result.stdout)
    if response.get('errors'):
        raise ValueError('GitHub did not return a complete calendar')
    data = response['data']['user']['contributionsCollection']['contributionCalendar']
    days = [day for week in data['weeks'] for day in week['contributionDays']]
    assert 350 <= len(days) <= 372
    assert len({day['date'] for day in days}) == len(days)
    assert all(isinstance(day['contributionCount'], int) and day['contributionCount'] >= 0 for day in days)
    assert sum(day['contributionCount'] for day in days) == data['totalContributions']
    data.update(username='valleysonata', source='https://api.github.com/graphql',
                updated_at=datetime.now(timezone.utc).isoformat())
    # Validate first. On API failure the last successful dated snapshot survives.
    (ROOT/'assets/github-contributions.json').write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
    sync()
    print(f"Fetched {data['totalContributions']} real contributions across {len(days)} days")


if __name__ == '__main__':
    refresh()
