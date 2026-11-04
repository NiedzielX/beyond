"""Retrieve one existing masked P9 job log from hosted cloud; no model/data writes."""
import json
import os
import re
import urllib.error
import urllib.request

JOB_ID = 126726008233


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args): return None


def main():
    if os.environ.get('GITHUB_REPOSITORY') != 'NiedzielX/beyond': raise ValueError('Restricted diagnostic repository')
    token = os.environ['GITHUB_TOKEN']; base = 'https://api.github.com/repos/NiedzielX/beyond'
    headers = {'Authorization': 'Bearer '+token, 'Accept': 'application/vnd.github+json', 'User-Agent': 'Beyond-P9-diagnostic'}
    request = urllib.request.Request(base+f'/actions/jobs/{JOB_ID}/logs', headers=headers)
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=25) as response: raw = response.read(2000000)
    except urllib.error.HTTPError as exc:
        if exc.code not in [301,302,303,307,308]: raise
        # Never forward repository credentials to the signed log-storage host.
        with urllib.request.urlopen(urllib.request.Request(exc.headers['Location']), timeout=25) as response:
            raw = response.read(2000000)
    text = raw.decode(errors='replace')
    text = re.sub(r'gh[pousr]_[A-Za-z0-9_]+', '[REDACTED]', text)
    text = re.sub(r'eyJ[A-Za-z0-9_=-]+\.[A-Za-z0-9_=-]+\.[A-Za-z0-9_=-]+', '[REDACTED]', text)
    lines = text.splitlines(); tail = '\n'.join(lines[-130:])[-40000:]
    evidence = {'version': 'p9-existing-job-log-diagnostic-v1', 'job_id': JOB_ID, 'log_bytes_read': len(raw),
                'tail': tail, 'model_changed': False, 'database_writes': False}
    body = {'name': 'p9-existing-job-failure-diagnostic', 'head_sha': os.environ['GITHUB_SHA'], 'status': 'completed',
            'conclusion': 'neutral', 'output': {'title': 'Existing P9 job failure diagnostic',
                'summary': 'Masked existing job log only; no prediction or database operation.', 'text': json.dumps(evidence)}}
    request = urllib.request.Request(base+'/check-runs', data=json.dumps(body).encode(),
        headers={**headers, 'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(request, timeout=25) as response: result = json.load(response)
    print(json.dumps({'check_run_id': result['id'], 'existing_job_id': JOB_ID, 'database_writes': False}))


if __name__ == '__main__': main()
