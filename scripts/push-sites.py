#!/usr/bin/env python3
"""Push a committed source tree using a short-lived Sites credential on stdin.

Fallback for environments without the packaged Sites workflow helper. The
credential is used only in process memory and is never written to Git config,
files, command arguments or logs. Ordinary GitHub pushes use `origin` instead.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

root = Path(__file__).resolve().parents[1]
credential = json.loads(sys.stdin.readline())
token = credential['token']
remote = credential['remote_url']
branch = credential['branch']
if credential.get('auth_mode') != 'http_extra_header':
    raise SystemExit('Unsupported source authentication mode.')
parsed = urlsplit(remote)
if parsed.scheme != 'https' or parsed.username or parsed.password:
    raise SystemExit('A credential-free HTTPS source remote is required.')
subprocess.run(['git', 'check-ref-format', '--branch', branch], cwd=root, check=True, stdout=subprocess.DEVNULL)
env = os.environ.copy()
env.update({'GIT_CONFIG_COUNT': '2', 'GIT_CONFIG_KEY_0': 'http.extraHeader',
            'GIT_CONFIG_VALUE_0': f'Authorization: Bearer {token}',
            'GIT_CONFIG_KEY_1': 'credential.helper', 'GIT_CONFIG_VALUE_1': '',
            'GIT_TERMINAL_PROMPT': '0'})
for name in list(env):
    if name.startswith('GIT_TRACE') or name == 'GIT_CURL_VERBOSE':
        env.pop(name)
result = subprocess.run(['git', 'push', remote, f'HEAD:refs/heads/{branch}'], cwd=root,
                        env=env, capture_output=True, text=True)
print((result.stdout + result.stderr).replace(token, '[REDACTED]'))
raise SystemExit(result.returncode)
