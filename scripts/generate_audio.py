#!/usr/bin/env python3
"""
Generate VOICEVOX audio files for いくつあるかな.
話者: ずんだもん (あまあまスタイル)

Usage (run from project root):
    python3 scripts/generate_audio.py

VOICEVOX must be running on Windows.
WSL: the Windows host IP is resolved dynamically via `ip route show`.
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional


def _windows_host_ip():
    # type: () -> str
    try:
        out = subprocess.check_output(['ip', 'route', 'show'], text=True)
        for line in out.splitlines():
            if line.startswith('default'):
                return line.split()[2]
    except Exception:
        pass
    return ''


# --- Config -----------------------------------------------------------
_host_ip = _windows_host_ip()
HOSTS = (
    [f'http://{_host_ip}:50021', 'http://localhost:50021'] if _host_ip
    else ['http://localhost:50021']
)
OUT_DIR = 'audio'

# filename (without .wav) → text to synthesize
PHRASE_FILES = {  # type: Dict[str, str]
    'count_1':  'いち',
    'count_2':  'に',
    'count_3':  'さん',
    'count_4':  'し',
    'count_5':  'ご',
    'count_6':  'ろく',
    'count_7':  'しち',
    'count_8':  'はち',
    'count_9':  'きゅう',
    'count_10': 'じゅう',
    'question': 'いくつ あるかな',
    'praise_1': 'できたね！',
    'praise_2': 'すごい！',
    'praise_3': 'やったね！',
    'hint':     'もういちど かぞえてみよう',
    'clear':    'ぜんぶ できたね！',
}

# Prosody tweaks
SPEED = 1.05
PITCH = 0.04
INTON = 1.2


# --- VOICEVOX API helpers ---------------------------------------------

def find_host():
    # type: () -> Optional[str]
    for host in HOSTS:
        try:
            with urllib.request.urlopen(host + '/version', timeout=5) as r:
                ver = r.read().decode().strip().strip('"')
            print(f'VOICEVOX {ver} @ {host}')
            return host
        except Exception:
            continue
    return None


def api_get(base, path):
    with urllib.request.urlopen(base + path, timeout=10) as r:
        return json.loads(r.read())


def find_speaker_id(base):
    speakers = api_get(base, '/speakers')
    for spk in speakers:
        if 'ずんだもん' in spk['name']:
            for style in spk['styles']:
                if 'あまあま' in style['name']:
                    return style['id']
            return spk['styles'][0]['id']
    raise RuntimeError('「ずんだもん」が見つかりません。VOICEVOXのバージョンを確認してください。')


def synthesize(base, text, speaker_id, out_path):
    qs = urllib.parse.urlencode({'text': text, 'speaker': speaker_id})
    req = urllib.request.Request(
        f'{base}/audio_query?{qs}',
        data=b'',
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        query = json.loads(r.read())

    query['speedScale']       = SPEED
    query['pitchScale']       = PITCH
    query['intonationScale']  = INTON
    query['prePhonemeLength'] = 0.3   # 頭切れ対策

    for ap in query['accent_phrases']:
        ap['is_interrogative'] = False  # 語尾上がり防止

    # 先頭フレーズ後の読点ポーズ
    first = query['accent_phrases'][0]
    if first.get('pause_mora'):
        first['pause_mora']['vowel_length'] = 0.70

    qs2 = urllib.parse.urlencode({'speaker': speaker_id})
    body = json.dumps(query, ensure_ascii=False).encode('utf-8')
    req2 = urllib.request.Request(
        f'{base}/synthesis?{qs2}',
        data=body,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urllib.request.urlopen(req2, timeout=30) as r:
        wav = r.read()

    with open(out_path, 'wb') as f:
        f.write(wav)


# --- Main -------------------------------------------------------------

def main() -> None:
    base = find_host()
    if not base:
        print('ERROR: VOICEVOX に接続できません。', file=sys.stderr)
        print('・VOICEVOXアプリが起動しているか確認してください。', file=sys.stderr)
        print('・Windowsファイアウォールでポート50021を許可してください。', file=sys.stderr)
        sys.exit(1)

    speaker_id = find_speaker_id(base)
    print(f'話者ID (ずんだもん あまあま): {speaker_id}\n')

    os.makedirs(OUT_DIR, exist_ok=True)

    errors = []  # type: List[str]
    total = len(PHRASE_FILES)
    for i, (name, text) in enumerate(PHRASE_FILES.items(), 1):
        out = os.path.join(OUT_DIR, f'{name}.wav')
        print(f'[{i:2d}/{total}] {name}.wav  "{text}"', end=' ', flush=True)
        try:
            synthesize(base, text, speaker_id, out)
            print('OK')
        except Exception as e:
            print(f'FAILED: {e}')
            errors.append(name)
        time.sleep(0.05)

    print(f'\n完了: {total - len(errors)}/{total} ファイル → {OUT_DIR}/')
    if errors:
        print(f'失敗したファイル: {errors}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
