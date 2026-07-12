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

# filename (without .wav) → (text, speedScale, pitchScale, intonationScale)
# 数え上げは短くテンポよく(speed高め)、それ以外は標準
PHRASE_FILES = {  # type: Dict[str, tuple]
    'count_1':  ('いち',                   1.15, 0.05, 1.2),
    'count_2':  ('に',                     1.15, 0.05, 1.2),
    'count_3':  ('さん',                   1.15, 0.05, 1.2),
    'count_4':  ('し',                     1.15, 0.05, 1.2),
    'count_5':  ('ご',                     1.15, 0.05, 1.2),
    'count_6':  ('ろく',                   1.15, 0.05, 1.2),
    'count_7':  ('しち',                   1.15, 0.05, 1.2),
    'count_8':  ('はち',                   1.15, 0.05, 1.2),
    'count_9':  ('きゅう',                 1.15, 0.05, 1.2),
    'count_10': ('じゅう',                 1.15, 0.05, 1.2),
    'question': ('ぜんぶで いくつかな',     1.05, 0.04, 1.2),
    'praise_1': ('できたね',               1.05, 0.04, 1.2),
    'praise_2': ('すごい',                 1.05, 0.04, 1.2),
    'praise_3': ('やったね',               1.05, 0.04, 1.2),
    'hint':     ('もういちど かぞえてみよう', 1.05, 0.04, 1.2),
    'clear':    ('ぜんぶ できたね',         1.05, 0.04, 1.2),
}


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


def synthesize(base, text, speaker_id, out_path, speed=1.05, pitch=0.04, inton=1.2):
    qs = urllib.parse.urlencode({'text': text, 'speaker': speaker_id})
    req = urllib.request.Request(
        f'{base}/audio_query?{qs}',
        data=b'',
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        query = json.loads(r.read())

    query['speedScale']       = speed
    query['pitchScale']       = pitch
    query['intonationScale']  = inton
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
    for i, (name, (text, speed, pitch, inton)) in enumerate(PHRASE_FILES.items(), 1):
        out = os.path.join(OUT_DIR, f'{name}.wav')
        print(f'[{i:2d}/{total}] {name}.wav  "{text}"', end=' ', flush=True)
        try:
            synthesize(base, text, speaker_id, out, speed, pitch, inton)
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
