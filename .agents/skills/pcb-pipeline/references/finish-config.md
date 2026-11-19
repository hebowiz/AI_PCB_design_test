# 基板ごとの設定: 配置表と finish.py

スクリプトは基板に依存しない。基板ごとの事情は 2 つのファイルに書く。

## 配置表 `board/placement_<build>.txt`

```
# 原点は基板中心。単位 mm、角度は度 (KiCad の向き)
j_in=-36,-17,270     # 入力端子。上 VIN / 下 GND
q=-20,-21,0          # ドレイン上 (VIN)、ソース下 (SW)
c_in1=-14.8,-23.6,0  # 10uF。左 VIN (ドレインの隣) / 右 GND
```

- 左辺は atopile のインスタンス名 (フットプリントの `atopile_address`)。部品番号でも
  引けるが、レイアウトを作り直すと振り直されるので使わない
- **なぜそこに置いたかをコメントに書く**。ホットループ、帰路、熱、コネクタの向きなど。
  次に配置を変える人 (自分を含む) が壊さないため
- 裏面に置く部品は KiCad で一度反転してから座標を書く (`place.py` は面を変えない)
- 回転したときのパッドの位置は `references/pcbnew.md` の「向きとパッドの位置」

配置を変えたら `finish.py` の座標 (ZONES, TRACKS, VIAS) も必ず見直す。

## `board/finish.py`

`scripts/finish_board.py` が読む Python の設定ファイル。どの名前も省略できる。
層は名前で書く (`"F.Cu"`, `"In1.Cu"`, `"In2.Cu"`, ..., `"B.Cu"`)。

```sh
$(scripts/kicad_python.sh) scripts/finish_board.py board.kicad_pcb pre  board/finish.py
$(scripts/kicad_python.sh) scripts/finish_board.py board.kicad_pcb post board/finish.py
```

### pre (配線の前)

| 名前 | 型 | 意味 |
| --- | --- | --- |
| `LAYERS` | int | 銅層の数 (2, 4, 6, ...)。省くと基板のまま |
| `PLANES` | {層: ネット} | 内層を電源層にして全面のゾーンを置く。ルータはその層に信号を引かない |
| `MOUNTING_HOLES` | [(x, y)] | 取付穴の位置。部品番号は MH1, MH2, ... |
| `HOLE_FOOTPRINT` | str | KiCad 同梱 `MountingHole.pretty` の名前。既定 `MountingHole_3.2mm_M3_DIN965` |
| `ZONES` | [dict] | 配線の前に置く銅。`net`, `points`, `layer` (既定 F.Cu), `priority` (既定 5), `thermal` (既定 False), `name`, `block_routing` (既定 True: 配線の間だけ同じ輪郭の禁止領域を重ねる) |
| `KEEPOUTS` | [dict] | 残し続ける禁止領域。`name`, `points`, `layers` (既定 全銅層), `tracks`, `vias`, `fills` (既定 すべて True) |
| `TRACKS` | [(ネット, 幅, [点], 層)] | 固定配線。ロックする |
| `VIAS` | [(ネット, x, y)] | 固定ビア。ロックする |
| `FANOUT` | dict | `net` の SMD パッドごとに直近へビアを打つ。`layers` (既定 [F.Cu])、`clearance`。そのネットの面が `PLANES` に要る |
| `ROUTE_KEEPOUTS` | [dict] | 配線の間だけの禁止領域。`name`, `points`, `layers` (既定 [F.Cu]) |
| `EDGE_KEEPOUT` | float | 基板の縁に沿った配線の間だけの禁止領域の幅。既定 0.6。0 で置かない |
| `pre_hook(ctx)` | 関数 | 表で書けないものを足す。文字列を返すとログに出る |

### post (SES を取り込んだ後)

| 名前 | 型 | 意味 |
| --- | --- | --- |
| `POURS` | [dict] | ベタ。`net`, `layers` (既定 表裏), `points` (既定 外形から 0.5mm 内側), `priority`。島はビアが無ければ捨てる |
| `STITCH` | dict | `net` のベタが全層で埋まっている格子点にビアを打つ。`pitch` (既定 3.0)。ビアの届かない島にも 1 本打つ |
| `post_hook(ctx)` | 関数 | 特殊な銅 (電極、マスク開口) などを足す |

post は最初に、配線用の禁止領域を外し、前回のベタとステッチングを消し、ルータの
出力を掃除する (重複片、行き止まり、`PLANES` と `STITCH` のネットの穴間隔違反のビア)。

### 何度流してもよい

pre も post も、前回足したものを消してから足し直す。見分けはゾーンの名前の頭。

| 頭 | 置く段 | 消す段 |
| --- | --- | --- |
| `auto-pcb-pre-` | pre (ZONES, PLANES) | pre |
| `auto-pcb-keep-` | pre (KEEPOUTS) | pre |
| `auto-pcb-route-` | pre (配線の間の禁止領域) | pre, post |
| `auto-pcb-post-` | post (POURS, フック) | pre, post, unroute |

**pre はロックした配線をすべて消す**。KiCad で手で引いてロックした線も消える。
固定したい線は `TRACKS` に書く (`ato build` もロックを外すので、どのみち書いておく)。
フットプリントの外のマスク層の図形 (露出銅の開口) も pre と post が消す。

### フックの書き方

```python
import pcbkit

def post_hook(ctx):
    c = next(f for f in ctx.board.GetFootprints() if f.GetReference() == "E1").GetPosition()
    cx, cy = pcbkit.to_mm(c.x), pcbkit.to_mm(c.y)
    ctx.zone("ELECTRODE", "F.Cu", pcbkit.circle(cx, cy, 40), pcbkit.POST + "electrode-F.Cu", 10)
    ctx.mask_ring(cx, cy, 15.5, 40)
    return "electrode added"
```

`ctx` (`pcbkit.Ctx`) の主なもの。

| 名前 | 中身 |
| --- | --- |
| `ctx.board` | pcbnew の BOARD。**読むのは編集の前だけ** (`references/pcbnew.md`) |
| `ctx.edges` | 外形の (左, 上, 右, 下) mm |
| `ctx.copper` | 銅層の名前 (表から裏) |
| `ctx.pads` | パッドの表 (部品番号、ネット、矩形、SMD か、穴) |
| `ctx.zone()`, `ctx.keepout()`, `ctx.track()`, `ctx.via()`, `ctx.pour()` | 足す。名前は上の表の頭を付ける |
| `ctx.mask_ring()`, `ctx.mask_opening()` | ソルダマスクの開口 |
| `pcbkit.rect()`, `pcbkit.circle()`, `ctx.inset(d)` | 輪郭の点列 |

足したものは `ctx` が Python の表に控え、ファンアウトなどの障害物判定に使う。
フックで基板から読み直さない。

## 見本

- `examples/dcdc-4layer/finish.py` — 4 層、内層 2 枚を GND 面、パワー段のベタ、
  ケルビン線とゲートの固定配線、GND ファンアウト、表裏の GND ベタとステッチング
- `examples/electrode-2layer/finish.py` — 2 層、アンテナ下の禁止領域をモジュールの
  形から求める `pre_hook`、円環電極と露出銅の `post_hook`、片面だけの GND ベタ
