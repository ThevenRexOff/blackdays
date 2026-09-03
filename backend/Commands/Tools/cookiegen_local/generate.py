#!/usr/bin/env python3
"""
CookieGen API worker — invoked by cookiegen_api.php via shell_exec.
Reads a base64-encoded JSON payload from argv[1]: {"country": "US", "proxy": null}
Prints a JSON result to stdout (same shape AmazonAccountCreator.processRegistration()
already returns) so the PHP bridge can pass it straight through unchanged.
"""
import sys, os, json, base64, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))


def _load_env_file(file_path):
    if not file_path.exists() or not file_path.is_file():
        return
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if len(line) == 0 or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and os.getenv(key) is None:
                os.environ[key] = value


_load_env_file(pathlib.Path(__file__).resolve().parent / 'config.env')


def main():
    try:
        payload = json.loads(base64.b64decode(sys.argv[1]).decode('utf-8'))
    except Exception as e:
        print(json.dumps({'status': False, 'message': f'Bad payload: {e}'}))
        return

    country = str(payload.get('country', 'US')).upper()
    proxy   = payload.get('proxy') or None

    raw_domains = os.getenv('MAIL_DOMAINS', '')
    mail_domains = [d.strip() for d in raw_domains.split(',') if d.strip()]

    from account_creator import AmazonAccountCreator

    try:
        creator = AmazonAccountCreator(
            country     = country,
            proxy       = proxy,
            verbose     = False,
            clearScreen = False,
            mailDomains = mail_domains,
        )
        result = creator.processRegistration()
    except Exception as e:
        result = {'status': False, 'message': f'{type(e).__name__}: {e}'}

    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
