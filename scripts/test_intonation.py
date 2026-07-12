#!/usr/bin/env python3
"""
イントネーションテスト用音声生成スクリプト。
3つの読み上げパターンを audio/test/ に生成して聞き比べる。

Usage:
    python3 scripts/test_intonation.py [文字 ...]
    python3 scripts/test_intonation.py          # デフォルト: あ か さ

パターン:
    A: 「文字」。「文字」は、どこかな？  ← 現行
    B: 文字。文字は、どこかな？          ← カギ括弧なし
    C: 文字、どこかな？                  ← シンプル・読点区切り
"""

import json
import os
import subprocess
import sys
import time
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


_host_ip = _windows_host_ip()
HOSTS = (
    [f'http://{_host_ip}:50021', 'http://localhost:50021'] if _host_ip
    else ['http://localhost:50021']
)
OUT_DIR = 'audio/test'

SPEAKER_NAME = 'ずんだもん'
SPEAKER_STYLE = 'あまあま'

SPEED   = 1.05
PITCH   = 0.04
INTON   = 1.2

PATTERNS = {
    'A': lambda c: f'「{c}」。「{c}」は、どこかな？',  # 現行
    'B': lambda c: f'{c}。{c}は、どこかな？',          # カギ括弧なし
    'C': lambda c: f'{c}、どこかな？',                  # シンプル・読点
}

CHAR_ROMAJI = {
    'あ': 'a',  'い': 'i',  'う': 'u',  'え': 'e',  'お': 'o',
    'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
    'さ': 'sa', 'し': 'si', 'す': 'su', 'せ': 'se', 'そ': 'so',
    'た': 'ta', 'ち': 'ti', 'つ': 'tu', 'て': 'te', 'と': 'to',
    'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
    'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
    'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
    'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
    'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
    'わ': 'wa', 'を': 'wo', 'ん': 'n',
}


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


def find_speaker_id(base):
    # type: (str) -> int
    with urllib.request.urlopen(base + '/speakers', timeout=10) as r:
        speakers = json.loads(r.read())
    for spk in speakers:
        if SPEAKER_NAME in spk['name']:
            for style in spk['styles']:
                if SPEAKER_STYLE in style['name']:
                    return style['id']
            return spk['styles'][0]['id']
    raise RuntimeError(f'「{SPEAKER_NAME}」が見つかりません。')


def synthesize(base, text, speaker_id, out_path):
    # type: (str, str, int, str) -> None
    qs = urllib.parse.urlencode({'text': text, 'speaker': speaker_id})
    req = urllib.request.Request(
        f'{base}/audio_query?{qs}', data=b'',
        headers={'Content-Type': 'application/json'}, method='POST',
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        query = json.loads(r.read())

    query['speedScale']       = SPEED
    query['pitchScale']       = PITCH
    query['intonationScale']  = INTON
    query['prePhonemeLength'] = 0.3
    for ap in query['accent_phrases']:
        ap['is_interrogative'] = False

    qs2 = urllib.parse.urlencode({'speaker': speaker_id})
    body = json.dumps(query, ensure_ascii=False).encode('utf-8')
    req2 = urllib.request.Request(
        f'{base}/synthesis?{qs2}', data=body,
        headers={'Content-Type': 'application/json'}, method='POST',
    )
    with urllib.request.urlopen(req2, timeout=30) as r:
        wav = r.read()

    with open(out_path, 'wb') as f:
        f.write(wav)


def show_accent(base, text, speaker_id):
    # type: (str, str, int) -> None
    qs = urllib.parse.urlencode({'text': text, 'speaker': speaker_id})
    req = urllib.request.Request(
        f'{base}/audio_query?{qs}', data=b'',
        headers={'Content-Type': 'application/json'}, method='POST',
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        query = json.loads(r.read())
    for ap in query['accent_phrases']:
        moras = [(m['text'], round(m.get('pitch', 0), 2)) for m in ap['moras']]
        pause = ' [pause]' if ap.get('pause_mora') else ''
        print(f'    accent={ap["accent"]}  {moras}{pause}')


def main():
    # type: () -> None
    chars = sys.argv[1:] if len(sys.argv) > 1 else ['あ', 'か', 'さ']

    # validate
    invalid = [c for c in chars if c not in CHAR_ROMAJI]
    if invalid:
        print(f'ERROR: 未対応文字 {invalid}', file=sys.stderr)
        sys.exit(1)

    base = find_host()
    if not base:
        print('ERROR: VOICEVOX に接続できません。', file=sys.stderr)
        sys.exit(1)

    speaker_id = find_speaker_id(base)
    print(f'話者: {SPEAKER_NAME} {SPEAKER_STYLE} (ID={speaker_id})\n')

    os.makedirs(OUT_DIR, exist_ok=True)

    for char in chars:
        romaji = CHAR_ROMAJI[char]
        print(f'■ 文字: {char}')
        for pat_key in sorted(PATTERNS):
            text = PATTERNS[pat_key](char)
            out_path = os.path.join(OUT_DIR, f'{romaji}_pat{pat_key}.wav')
            print(f'  パターン{pat_key}: {text!r}')
            show_accent(base, text, speaker_id)
            try:
                synthesize(base, text, speaker_id, out_path)
                print(f'    → {out_path}  OK')
            except Exception as e:
                print(f'    → FAILED: {e}')
            time.sleep(0.05)
        print()


if __name__ == '__main__':
    main()
