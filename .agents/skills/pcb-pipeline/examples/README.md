# 実例

このディレクトリのものは、そのまま使う部品ではなく**書き方の見本**。
新しい基板では中身 (座標、ネット名) を入れ替える。基板に依存しない処理は
`scripts/` にあり、基板ごとに書くのは設定ファイルだけ。

| ファイル | 何の見本か |
| --- | --- |
| `Makefile` | 工程全体の繋ぎ方。依存関係と順序。プロジェクトの直下に写して使う |
| `dcdc-4layer/finish.py` | 4 層・内層 GND 面の降圧 DC-DC の `board/finish.py`。パワー段のベタ、固定配線 (F.Cu/B.Cu をビアで渡るゲート、ケルビン線)、配線中だけの禁止領域、GND ファンアウト、表裏のベタとステッチング |
| `dcdc-4layer/draw_schematic.py` | 回路図を描き、描いた接続をネット表と突き合わせて食い違えば失敗する (`scripts/schematic.py` を使う) |
| `electrode-2layer/finish.py` | 2 層・ドーナツ電極の微小電流計の `board/finish.py`。表で書けない形を `pre_hook` / `post_hook` で書く見本。アンテナ下の禁止領域、円環電極のゾーンとレジスト開口、片面だけのベタ |
| `electrode-2layer/gen_ring_electrode.py` | フットプリントとシンボルを生成する。基板外形をフットプリントに持たせる技 |
| `*/finish_board_old.py` | 設定ファイルに分ける前の、基板ごとに書いていた仕上げスクリプト。移行の参照用 |

元の基板は 2 つ。

- `dcdc-4layer/` — DGC 実験用の降圧 DC-DC (80 x 60 mm、4 層)。→ `references/circuits/power.md`
- `electrode-2layer/` — ドーナツ電極の微小電流計 (90 x 115 mm、2 層)。→ `references/circuits/low-current.md`
