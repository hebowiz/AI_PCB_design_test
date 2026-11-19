# KiCad の Python から基板を触る

`kicad-cli` で足りない操作は `pcbnew` を直接呼ぶ。同梱の Python を使う。

```sh
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/*/bin/python3
```

**Python 3.9 系**。`X | None` は書けない。`list[str]` は使える。

## kicad-cli に無くて pcbnew にあるもの

| 操作 | 関数 |
| --- | --- |
| Specctra DSN 書き出し | `pcbnew.ExportSpecctraDSN(board, path)` |
| Specctra SES 取り込み | `pcbnew.ImportSpecctraSES(board, path)` |

KiCad 10 の `kicad-cli pcb export` に specctra は無い。自動配線に出すには
この 2 つを使うしかない。SES 取り込みは配線とビアだけを足すので、
ゾーンや図形は消えない。

## SWIG の罠

**基板を編集すると既存のラッパが死ぬ**。ゾーンを 1 つ `Remove` しただけで、
その後の `board.GetDrawings()` が `'SwigPyObject' object is not iterable` になり、
`GetBoardEdgesBoundingBox()` は `GetLeft` を持たないオブジェクトを返し、
続けるとセグメンテーション違反で落ちる。

対策は 2 つ。

1. 新しく作るものに必要な座標は、**編集を始める前に全部読んで数値にしておく**。
2. 削除対象は**先に集めてから、まとめて消す**。反復しながら消さない。

追加したオブジェクトへの参照は自分で保持しておくと、後で `GetFilledArea()`
などを呼べる。基板から引き直すと死んだラッパが返ってくる。

**`BOX2I` を持ち回らない**。`GetBoundingBox()` の戻り値を `Merge()` で次々につなぐと、
編集をしていなくてもセグメンテーション違反で落ちる。受け取ったらすぐ
`(ToMM(r.GetLeft()), ToMM(r.GetTop()), ToMM(r.GetRight()), ToMM(r.GetBottom()))`
の tuple に写し、合成や重なり判定は Python 側で計算する (`scripts/place_labels.py` の `box`)。

**終了時に落ちる**。ファイルを書き終えた後、インタプリタ終了時の後始末で
セグメンテーション違反になる。Makefile から呼ぶとビルドが失敗扱いになる。

```python
sys.stdout.flush()
os._exit(code)      # 後始末を走らせずに抜ける
```

## API の細かい癖

```python
pts = pcbnew.VECTOR_VECTOR2I()          # VECTOR2I_VECTOR ではない
pts.append(pcbnew.VECTOR2I(x, y))

layers = pcbnew.LSET()                   # LSET([a, b]) は通らない
layers.AddLayer(pcbnew.F_Cu)
layers.AddLayer(pcbnew.B_Cu)

model.m_Filename                         # GetFilename() は無い
```

面積は内部単位の平方。mm² にするには `ToMM` を 2 回かける。

## ゾーンで作る銅

フットプリントに置けない形状は、ゾーンと禁止領域の組み合わせで作る。
円環なら、外径の円ゾーンに内径の円のルールエリア (ゾーン塗り禁止) を重ねる。

両面に素地の銅を出すなら、レジスト層に図形を置く。`SHAPE_T_CIRCLE` を
線幅付きで描けば円環の開口になる。

```python
ring.SetShape(pcbnew.SHAPE_T_CIRCLE)
ring.SetLayer(pcbnew.F_Mask)
ring.SetCenter(...); ring.SetEnd(...)    # 中心と半径
ring.SetWidth(mm(外径 - 内径))
```

作り直しを安全にするには、足したものに名前を付けて次回まとめて消す。
ゾーンは `SetZoneName`、レジストの図形は中心座標で照合する。半径で照合すると
寸法を変えたときに古いものが残る。

最後に `pcbnew.ZONE_FILLER(board).Fill(board.Zones())` を呼ぶ。

## 配置

配置はビルドをまたいで保持される。座標はテキストに書いておいて流し込むと、
レイアウトを作り直しても復元できる。

## 同じプロセスで基板を読み直さない

編集して保存した後に同じプロセスで `pcbnew.LoadBoard` を呼ぶと、戻り値が
`SwigPyObject` になり、`GetBoardEdgesBoundingBox` すら呼べない。
「前回足したものを消す → 足し直す」を 1 本のスクリプトでやるなら、消す段を
`subprocess` で自分自身を別引数で起動して行い、足す段は新しいプロセスで読む。
(`scripts/finish_board.py` の `main()`)

## 向きとパッドの位置

KiCad の角度 θ では、部品原点からの相対座標 (x, y) が
`(x cosθ + y sinθ, −x sinθ + y cosθ)` に移る (y は下向き)。90° なら `(y, −x)`。
2 端子部品 (1 番が左) は **90° で 1 番が下、270° で 1 番が上** になる。
atopile の `a ~> 部品 ~> b` は 1 番パッドが a 側。

計算を信じずに、置いた後でパッドの座標とネットを読んで確かめる。

```python
for p in fp.Pads():
    bb = p.GetBoundingBox()
    print(p.GetNumber(), p.GetNetname(), pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()))
```

## ゾーンまわり

```python
z.SetLocalClearance(pcbnew.FromMM(0.2))        # 既定の 0.5mm はネットクラスとずれる
z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
z.HitTestFilledArea(layer, pos)                # 塗られた所か
polys = z.GetFilledPolysList(layer)            # 塗りの島ごとの輪郭
polys.Outline(i).PointInside(pos)
```

- **SES を取り込んだら必ず塗り直す**。古い塗りのまま DRC を回すと、新しい配線と
  ぶつかった違反が大量に出る
- **ベタの塗りは同じネットの穴を避けない**。ステッチングビアを格子に打つと、
  端子の GND 穴や既存の GND ビアのすぐ隣に来て、穴間隔違反になる。打つ前に
  既存の穴 (ビアと PTH パッド) との距離を見る
- **ビアの届かない島**は DRC が未接続にする。島ごとにビアかパッドがあるかを
  `GetFilledPolysList` で確かめ、無ければ島の中に 1 本打つか捨てる

## 層と穴

```python
board.SetCopperLayerCount(4)
board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)   # DSN で (type power)、ルータは信号を引かない
fp = pcbnew.FootprintLoad(".../footprints/MountingHole.pretty", "MountingHole_3.2mm_M3_DIN965")
fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM
                 | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_BOARD_ONLY)
```

KiCad 同梱のライブラリは
`/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/`。

## DRC の JSON を読むとき

- **ゾーンの違反や未接続の位置は、ゾーンの最初の頂点が書かれる**。場所の手掛かりに
  ならないので、ゾーンの島は pcbnew で直接調べる
- **uuid が重複していると、違反の相手が別の部品として報告される**。
  atopile の出力はそうなっている (`atopile.md`)。先に `scripts/dedupe_uuids.py`
- `--severity-error` を付けないと、シルクの重なり警告が数百件混ざる

## 画像で見る

3D レンダは部品の干渉を見るのに、層ごとの SVG は配線とベタの形を見るのに使う。

```sh
kicad-cli pcb export svg --layers F.Cu,Edge.Cuts --mode-single --fit-page-to-board \
  --exclude-drawing-sheet -o out/F.svg board.kicad_pcb
rsvg-convert -w 1600 -b white out/F.svg -o out/F.png     # 拡大は -w を増やして magick で切り出す
```

座標を読み取るときは、出力幅 ÷ 基板幅 (mm) が 1mm あたりのピクセル数。

**3D レンダの `--zoom` と `--pan` は当てにしない**。付けると真っ白な画像が出ることがある。
全体を高解像度で出してから切り抜く。KiCad 同梱の Python にも系統の python3 にも
PIL が無いことが多いので、macOS なら `sips` を使う。

```sh
kicad-cli pcb render --side top -w 2400 -h 1800 --quality high -o out/top.png board.kicad_pcb
sips -c 440 480 --cropOffset 220 620 out/top.png --out out/crop.png   # 高さ 幅 / 上 左
```

**3D で部品がずれて見えたら、配置より先にモデルのオフセットを疑う**。パッドの
位置が正しくても、EasyEDA のモデルが数 mm ずれていることがある。
→ `scripts/check_models.py`

## シルクの部品番号

EasyEDA のフットプリントは部品番号を外形のすぐ上か下に置く。部品が詰まると
隣の部品の本体の下に入り、実装後に読めない。DRC は部品の本体を知らないので
これを検出しない (`silk_overlap` は外形線どうしの重なりしか見ない)。
`scripts/place_labels.py` が高さ 1.0mm に揃えて空いた位置へ動かし、置けないものを
F.Fab に移して名前を出す。配線とベタには触らないので post の後に何度流してもよい。

- 部品番号の寸法は `SetHorizJustify(GR_TEXT_H_ALIGN_CENTER)` と
  `SetVertJustify(GR_TEXT_V_ALIGN_CENTER)`、`SetTextAngleDegrees(0)` にしてから
  `GetBoundingBox()` で測る。中央揃えにしておけば、位置 = 矩形の中心になる
- フットプリントの文字の角度は基板に対する絶対角。部品の回転を足さなくてよい

## 部品の干渉

`ato create part` の EasyEDA 由来フットプリントにはコートヤードが無く、
KiCad の DRC は部品どうしの干渉を検出しない。`scripts/check_overlap.py` で
外形の重なりを出し、大きいものは実寸で確かめる。見落としやすいのは、
端子台の本体の下に入った部品と、電解コンデンサの台座の下に入った部品。
