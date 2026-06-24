import base64, requests

API = 'https://api.github.com'

def headers(token):
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json',
    }

def test_connection(token, repo):
    r = requests.get(f'{API}/repos/{repo}', headers=headers(token))
    return r.ok, r.status_code

def get_file_contents(token, repo, path):
    r = requests.get(f'{API}/repos/{repo}/contents/{path}', headers=headers(token))
    if not r.ok:
        return None, None, f'Error {r.status_code}: {r.json().get("message", "")}'
    data = r.json()
    content = base64.b64decode(data['content']).decode('utf-8')
    return content, data['sha'], None

def put_file_contents(token, repo, path, content, message):
    existing, sha, err = get_file_contents(token, repo, path)
    if err and '404' not in err:
        return False, err
    body = {
        'message': message,
        'content': base64.b64encode(content.encode('utf-8')).decode('utf-8'),
    }
    if sha:
        body['sha'] = sha
    r = requests.put(f'{API}/repos/{repo}/contents/{path}', json=body, headers=headers(token))
    if r.ok:
        return True, None
    return False, f'Error {r.status_code}: {r.json().get("message", "")}'

def delete_file(token, repo, path, message):
    """Delete a file from the repo."""
    content, sha, err = get_file_contents(token, repo, path)
    if err:
        return False, err
    r = requests.delete(f'{API}/repos/{repo}/contents/{path}', json={
        'message': message,
        'sha': sha,
    }, headers=headers(token))
    if r.ok:
        return True, None
    return False, f'Error {r.status_code}: {r.json().get("message", "")}'

def list_files_in_dir(token, repo, dir_path):
    """List files in a directory in the repo."""
    r = requests.get(f'{API}/repos/{repo}/contents/{dir_path}', headers=headers(token))
    if not r.ok:
        return None, f'Error {r.status_code}: {r.json().get("message", "")}'
    return r.json(), None
