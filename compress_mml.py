#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compress_mml.py
================
Pyxel MML (Music Macro Language) ファイルを、生の(手作業修正前の)状態から
一括で最小文字数表現へ変換するツールです。

使い方:
    このスクリプトに .txt (MMLファイル) をドラッグ&ドロップしてください。
    (複数ファイルを一度にドロップしても構いません)

    コマンドラインから実行する場合:
        python compress_mml.py MML.txt [MML2.txt ...]
        python compress_mml.py --no-dot MML.txt   (付点音符表現を使わない)

処理内容:
    1. 元ファイルを "元ファイル名.org.txt" にリネーム(退避)します。
    2. 変換後の内容を、元のファイル名 "元ファイル名.txt" として書き出します。

変換ルール:
    - MMLの音符/休符長は 1〜192 の整数で、"N" は「全音符の 1/N の長さ」を表す。
    - "NOTE_N1&N2&N3..." のようなタイ表現は、長さの合計 = 1/N1 + 1/N2 + 1/N3 + ...
    - 長さ指定の無い音符/休符は、直前に出現した L コマンドの値を引き継ぐ
      (Lコマンド未出現の場合は MML既定値の 4 とする)。
    - タイで結ばれた合計長を計算し、以下の優先順で最小表現へ変換する:
        (a) 合計が 1/N (N=1..192) にちょうど一致するなら単独の "N" で表現
        (b) 合計が 3/(2N) (付点音符, N=1..192) にちょうど一致するなら "N." で表現
            (--no-dot 指定時はこのルールを使わず (c) のみで表現)
        (c) それでも表現しきれない場合、2の累乗長 (1,2,4,8,16,...,128) を
            大きい方から貪欲に組み合わせ "N1&N2&..." のタイ表現にする
            (各ステップで再度 (a)(b) を確認し、可能ならその時点で打ち切る)
    さらに、休符(R)は&で繋がれず単体で連続記述されるケースが多いため、
    以下のルールで「&を介さず連続する複数のR」もまとめて最小化します:
        - 数字指定の有無を問わず、R / R数字 が空白区切りで2つ以上連続している
          場合を対象とする(音階名や他のコマンドを挟まず、Rのみが続く区間)。
        - 各Rの長さ(数字省略時は直近のLコマンド値)を合計し、
          decompose() と同じ規則で最小表現の単一のRにまとめる。
        - このルールは音階(C/D/E/F/G/A/B)には適用しない(仕様上、対象は
          休符のみ)。

    最後に、@ENV のスロット集約を行単位(トラック単位)で行います:
        - @ENV<番号>{パラメータ} の「パラメータ」の中身が実際に一致するかどうかで
          スロットを判定する(元の番号表記は信用しない。同じ番号でも内容が違えば
          別スロット、逆に番号が違っても内容が同じなら同一スロットとして扱う)。
        - その行の中で初めて登場した内容には新しいスロット番号(1から順に
          インクリメント)を割り当て、フル定義 @ENV<新番号>{パラメータ} を出力する。
        - 既に同じ内容が登場済みの場合は、2回目以降は @ENV<新番号> とだけ出力し、
          {パラメータ} 部分は省略する。
        - @ENV<番号> のように既に番号だけで参照されている箇所も、元の番号が
          指していた内容を解決した上で、新しいスロット番号に置き換える。
        - 処理は必ず行(トラック)単位で完結させ、他の行の状態は一切参照・
          共有しない。

前処理(圧縮の前に行う下ごしらえ):
    0-a. 末尾の不要行を除去する
        ファイル末尾から見て、空行、または URL 行(http:// / https:// で
        始まる行)が続く限り取り除く(pyxel MML Studio 共有リンクなど、
        MML本体ではない行を末尾から自動的に切り落とす)。
    0-b. 絶対オクターブ指定 O<数字> を、相対オクターブ変更 </> に変換する
        行(トラック)ごとに独立して処理する:
          - その行で最初に出現した O<n> はそのまま残し、これを基準値とする。
          - 以降に出現する O<n> は、基準値との差分 diff = n - 基準値 を求め、
              diff > 0 なら '>' を diff 個
              diff < 0 なら '<' を |diff| 個
              diff == 0 なら何も出力しない(削除)
            に置き換え、基準値を n に更新する。
        (convert_o_to_symbols.py と同一のロジックを内蔵している)
"""

import sys
import os
import re
import shutil
from fractions import Fraction

# 2の累乗の標準音長 (全音符=1 から 128分音符まで)
POWERS_OF_TWO = [1, 2, 4, 8, 16, 32, 64, 128]
MAX_LEN = 192  # MML仕様上の長さの最大値

# L コマンド、または「音名/休符 + 任意の数字 + 1個以上の &数字(タイ)」にマッチ
TIE_RE = re.compile(
    r'(?P<lcmd>L(?P<lval>\d+))'
    r'|(?P<name>[A-G][+\-]?|R)(?P<num>\d*)(?P<ties>(?:&\d+)+)'
)

# L コマンド、または「Rのみが空白区切りで2つ以上連続する区間」にマッチ
# (改行はまたがない = トラック行をまたいで結合しない)
REST_RUN_RE = re.compile(
    r'(?P<lcmd>L(?P<lval>\d+))'
    r'|(?P<rrun>R\d*(?:[ \t]+R\d*)+)'
)

# @ENV<番号> または @ENV<番号>{パラメータ} にマッチ
ENV_RE = re.compile(r'@ENV(?P<origslot>\d+)(?:\{(?P<content>[^}]*)\})?')

# 絶対オクターブ指定 O<数字> にマッチ (convert_o_to_symbols.py と同一)
OCTAVE_RE = re.compile(r'O(\d+)')

# 末尾除去の対象とみなす URL 行 (http:// または https:// で始まる行)
URL_LINE_RE = re.compile(r'^\s*https?://')


def decompose(total: Fraction, use_dot: bool = True) -> str:
    """全音符を1とした長さ total (Fraction) を、
    MMLの長さ表現として最小文字数になるよう文字列化する。"""
    terms = []
    remaining = total
    while remaining > 0:
        # (a) 単独の N でちょうど表現できるか
        if remaining.numerator == 1 and 1 <= remaining.denominator <= MAX_LEN:
            terms.append(str(remaining.denominator))
            break

        # (b) 付点音符 N. (= 3/(2N)) でちょうど表現できるか
        if use_dot:
            q = Fraction(3, 2) / remaining
            if q.denominator == 1 and 1 <= q.numerator <= MAX_LEN:
                terms.append(f"{q.numerator}.")
                break

        # (c) 2の累乗の中で、remaining を超えない最大の長さを貪欲に選ぶ
        picked = None
        for n in POWERS_OF_TWO:
            if Fraction(1, n) <= remaining:
                picked = n
                break
        if picked is None:
            # remaining が 1/128 未満の極小値だった場合のフォールバック
            picked = POWERS_OF_TWO[-1]
        terms.append(str(picked))
        remaining -= Fraction(1, picked)

    return "&".join(terms)


def strip_trailing_junk(text: str) -> str:
    """段階0-a: ファイル末尾の空行・URL行を取り除く。
    末尾から見て、空行または URL 行が続く限り削除し、
    それ以外の行(MML本体)に達したら止める。"""
    lines = text.splitlines(keepends=True)

    while lines:
        last = lines[-1]
        stripped = last.strip("\r\n")
        if stripped == "" or URL_LINE_RE.match(stripped):
            lines.pop()
        else:
            break

    text = "".join(lines)
    return text


def convert_octave_line(line: str) -> str:
    """段階0-b: 1行内の絶対オクターブ O<n> を相対オクターブ </> に変換する。
    (convert_o_to_symbols.py の convert_line と同一ロジック)"""
    matches = list(OCTAVE_RE.finditer(line))
    if not matches:
        return line

    current = None
    result = []
    last_end = 0

    for idx, m in enumerate(matches):
        n = int(m.group(1))
        result.append(line[last_end:m.start()])

        if idx == 0:
            # 基準値: そのまま残す
            result.append(m.group(0))
            current = n
        else:
            diff = n - current
            if diff == 0:
                replacement = ''
            elif diff > 0:
                replacement = '>' * diff
            else:
                replacement = '<' * abs(diff)
            result.append(replacement)
            current = n

        last_end = m.end()

    result.append(line[last_end:])
    return ''.join(result)


def convert_octave(text: str) -> str:
    """行(トラック)単位で絶対オクターブ表記を相対表記に変換する。"""
    lines = text.splitlines(keepends=True)
    return "".join(convert_octave_line(line) for line in lines)


def compress_ties(text: str, use_dot: bool = True) -> str:
    """段階1: '音名/休符 + &数字...' のタイ表現を最小化する。"""
    current_L = [4]  # MML既定値

    def repl(m: "re.Match") -> str:
        if m.group('lcmd'):
            current_L[0] = int(m.group('lval'))
            return m.group(0)

        name = m.group('name')
        num = m.group('num')
        ties = m.group('ties')

        nums = [int(x) for x in re.findall(r'&(\d+)', ties)]
        first = int(num) if num else current_L[0]
        nums = [first] + nums

        total = sum((Fraction(1, n) for n in nums), Fraction(0))
        return name + decompose(total, use_dot=use_dot)

    return TIE_RE.sub(repl, text)


def compress_rest_runs(text: str, use_dot: bool = True) -> str:
    """段階2: &で繋がれずに連続する単体のRコマンド群をまとめて最小化する。"""
    current_L = [4]  # MML既定値

    def repl(m: "re.Match") -> str:
        if m.group('lcmd'):
            current_L[0] = int(m.group('lval'))
            return m.group(0)

        run = m.group('rrun')
        tokens = re.findall(r'R(\d*)', run)
        nums = [int(t) if t else current_L[0] for t in tokens]

        total = sum((Fraction(1, n) for n in nums), Fraction(0))
        return "R" + decompose(total, use_dot=use_dot)

    return REST_RUN_RE.sub(repl, text)


def compress_env_line(line: str) -> str:
    """1行(1トラック)内の @ENV スロットを、内容の一致に基づいて
    集約する。内容が同じなら同一スロット番号を再利用し、フル定義は
    その行内での初出時のみ行う。他の行の状態は一切参照しない。"""

    content_to_slot: dict = {}
    orig_slot_content: dict = {}
    next_slot = [1]

    def repl(m: "re.Match") -> str:
        origslot = m.group('origslot')
        content = m.group('content')

        if content is not None:
            # フル定義: @ENV<番号>{パラメータ}
            orig_slot_content[origslot] = content
            if content in content_to_slot:
                slot = content_to_slot[content]
                return f"@ENV{slot}"
            else:
                slot = next_slot[0]
                next_slot[0] += 1
                content_to_slot[content] = slot
                return f"@ENV{slot}{{{content}}}"
        else:
            # 番号のみの参照: @ENV<番号>
            ref_content = orig_slot_content.get(origslot)
            if ref_content is not None and ref_content in content_to_slot:
                slot = content_to_slot[ref_content]
                return f"@ENV{slot}"
            # 対応するフル定義が見つからない場合は変更せず維持する
            return m.group(0)

    return ENV_RE.sub(repl, line)


def compress_env(text: str) -> str:
    """行(トラック)単位で @ENV スロット集約を適用する。"""
    lines = text.splitlines(keepends=True)
    return "".join(compress_env_line(line) for line in lines)


def convert(text: str, use_dot: bool = True) -> str:
    """MMLテキスト全体を走査し、前処理(末尾除去・オクターブ変換)を行った上で
    タイ表現・連続休符・@ENVスロットを最小化する。"""
    text = strip_trailing_junk(text)
    text = convert_octave(text)
    text = compress_ties(text, use_dot=use_dot)
    text = compress_rest_runs(text, use_dot=use_dot)
    text = compress_env(text)
    return text


def process_file(path: str, use_dot: bool = True) -> None:
    if not os.path.isfile(path):
        print(f"[SKIP] ファイルが見つかりません: {path}")
        return

    base, ext = os.path.splitext(path)
    if not ext:
        ext = ".txt"
        base = path
    org_path = f"{base}.org{ext}"

    if os.path.abspath(org_path) == os.path.abspath(path):
        print(f"[SKIP] 既に .org{ext} ファイルです（変換済みの可能性）: {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        original = f.read()

    converted = convert(original, use_dot=use_dot)

    # 元ファイルを .org.txt にリネーム（退避）
    if os.path.exists(org_path):
        print(f"[WARN] {org_path} は既に存在します。上書きします。")
    shutil.move(path, org_path)

    # 変換後の内容を元のファイル名で書き出す
    with open(path, "w", encoding="utf-8") as f:
        f.write(converted)

    orig_len = len(original)
    new_len = len(converted)
    reduction = orig_len - new_len
    pct = (reduction / orig_len * 100) if orig_len else 0

    print(f"[OK] {os.path.basename(path)}")
    print(f"     退避 : {os.path.basename(org_path)}")
    print(f"     出力 : {os.path.basename(path)}")
    print(f"     文字数: {orig_len} -> {new_len}  ({reduction:+d}, {pct:.1f}% 削減)")


def main():
    args = sys.argv[1:]
    use_dot = True
    if "--no-dot" in args:
        use_dot = False
        args = [a for a in args if a != "--no-dot"]

    if not args:
        print("MML の .txt ファイルをこのスクリプトにドラッグ&ドロップしてください。")
        print("(コマンドラインの場合: python compress_mml.py file.txt [--no-dot])")
        input("Enterキーで終了...")
        return

    for path in args:
        try:
            process_file(path, use_dot=use_dot)
        except Exception as e:
            print(f"[ERROR] {path}: {e}")

    input("Enterキーで終了...")


if __name__ == "__main__":
    main()