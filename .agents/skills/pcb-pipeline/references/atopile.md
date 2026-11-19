# atopile 0.15.8 の実際

2026年9月末では0.15.8がCLI の最終版。それ以降はWeb版なので、注意して使用する。

```sh
uv tool install "atopile==0.15.8"
ato auth login          # 対話式。これを済ませるまで部品選定が動かない
```

## 書き方で詰まる点

| やりたいこと | 書き方 |
| --- | --- |
| トレイトを子に付ける | `trait <フィールド> <トレイト名><引数...>` |
| トレイトを使う | 使う前に `import <トレイト名>` が要る |
| 名前の無いピンを参照 | `part.1`、`part.2` |
| 直列に挟む | `a ~> resistor ~> b`。`can_bridge` を持つ部品だけ |
| サイズを決める | `.package` ではなく `.lcsc_id` |

複数 import を 1 行に書くと非推奨の警告が出る。1 行 1 つにする。

enum の代入は一部の属性しか受け付けない。`temperature_coefficient`、
`channel_type`、`doping_type`、`fuse_type`、`layer_type`、`material` など。
LED の `color` は受け付けない。ライブラリの使用例には載っているが通らない。

## 部品選定

型からの自動選定 (`is_pickable_by_type`) を持つのは Resistor、Capacitor、
Inductor など。**LED と Diode は持っていない**。持っていない部品は黙って
部品なしのままビルドが通り、フットプリントもネットも付かない。BOM に
現れないことで気づく。

```sh
ato create part -s C2286 -a        # LCSC 番号から実体部品を parts/ に作る
ato create part -s "メーカー:型番"   # メーカー名の表記が合わないと見つからない
```

作られる部品は `is_atomic_part` トレイトを持ち、フットプリント、シンボル、
3D モデルがローカルに入る。ピンは `signal 名前 ~ pin 番号` で定義される。
名前の無いピンは番号で参照する。

`.package` の指定は選定側が無視する。サイズを決めたいなら `lcsc_id` で
型番まで指定する。JLCPCB の基本部品表から選ぶと在庫と価格で有利。

部品 API が返す在庫数は当てにならない。全部品が 0 と返ってくることがある。
発注時に LCSC か JLCPCB で実数を見る。

## ソルバが矛盾と言うとき

`assert (V - Vf) / R within I` のような式は、区間演算で全組み合わせが成立する
必要があるため、素直に書くと矛盾する。抵抗値を直接決めて、式はコメントに残す。

## 基板側で効く指定

```
outline = new RectangularBoardShape
outline.x = 20mm
outline.y = 15mm
outline.corner_radius = 1mm
```

外形が無いと Freerouting は配線できない。原点は外形の中心になる。
矩形以外の外形は、フットプリントに Edge.Cuts を持たせるか、ビルド後の
スクリプトで足す。フットプリントに入れておくと `ato build` で消えない。

## 再生成しないと壊れるもの

**部品を差し替えるとネットが載らないことがある**。`lcsc_id` を変えた、
パッケージが変わった、といった場合に、差し替わった部品だけネットの付かない
フットプリントとして基板に残る。DRC は未接続として報告するが、配線前だと
気づきにくい。部品構成を変えたらレイアウトファイルを退避して作り直す。
配置は別ファイルに書いておいて流し込む。

**fp-lib-table は増える一方**。選定から外れた部品のライブラリ登録が残り、
KiCad がプロジェクトを開くときに警告を出す。`prune_fp_lib_table.py` で掃除する。

**フットプリントは書き直される**。カスタムパッドのプリミティブは消える。
特殊な形状の銅はゾーンとして配線後に足す。

## 値だけでは部品を任せない

`.package` が効かないだけでなく、**抵抗やコンデンサを値と許容差だけで書くと、
選定はパッケージを選ばずに拾う**。0603 のつもりが 2W のリード抵抗や 6mm 角の
チップ、1206 の 630V コンデンサが来た。すべて `lcsc_id` で型番を決める。
C0G が要る所 (発振の CT、スナバ) も型番で決める。

ビルド後に BOM (`build/builds/<build>/<build>.bom.csv`) のフットプリント列を
必ず見る。

## LCSC 番号を探す

jlcsearch の API が使える。`curl` なら通る (Python の `urllib` は User-Agent 無しで 403)。

```sh
curl -s "https://jlcsearch.tscircuit.com/components/list.json?search=INA241"
curl -s "https://jlcsearch.tscircuit.com/resistors/list.json?resistance=4700&package=0603"
```

返る項目は `lcsc` (C を付けて使う)、`mfr`、`package`、`stock`、`is_basic`。
基本部品 (`is_basic`) を優先すると実装費が安い。

## ato create part の癖

- **EasyEDA API が一時的に失敗する**。`Failed to parse response from EasyEDA API` は
  数十秒おいて再実行すれば通る。API 自体は正常なことが多い
- **生成された .ato のピン定義を開いて確かめる**。NC ピン (データシートで GND 接続を
  指定されたもの) が定義されないことがある。直すときは `is_auto_generated` の
  トレイトを消してから書き足す (`GND ~ pin 4`)
- 同じ信号の複数パッド (MOSFET のソース 3 本、裏面パッド) は、たいてい
  `S ~ pin 2` のように束ねて生成されている
- EasyEDA の電解コンデンサはシンボルのピン名が `1`/`2` だけ。
  **シルクの角が面取りされている側が 1 番で +**
- `MountingHole<metric_screw_size="M3", ...>` はテンプレート引数が通らない。
  穴は pcbnew で KiCad 標準ライブラリから足す (`pcbnew.md`)

## ビルドで基板に起きること

- **同じ部品のフットプリントは、パッドの uuid が全部同じになる**。DRC の報告が
  全く別の部品を指すので、`scripts/dedupe_uuids.py` で振り直す
- **pcbnew で足した穴やゾーンは、次のビルドで消えることがある**。配線の固定
  (ロック) も外れる。ビルドの後は、穴・ベタ・固定配線を足すスクリプトを毎回流す
- **`.kicad_pro` は書かれない**。ネットクラスが要るなら自分で置く
  (`design-rules.md`)。最小限の JSON でも KiCad は足りない所を既定で補う

## レイアウトを作り直すと部品番号が変わる

`make fresh` などでレイアウトを捨てて作り直すと、atopile は部品番号 (R30, R34...) を
振り直す。部品を足した後だと番号がずれる。配置表を部品番号で書いていると、
**別の部品がその座標に置かれ、DRC は電気的に正しいので通ってしまう**
(シャント抵抗の場所に 0603 の分圧抵抗が来た)。配置表は main.ato のインスタンス名
(フットプリントの `atopile_address` フィールド) で書く。`scripts/place.py` は両方で引ける。

作り直した後は、名前ごとの座標を前の基板と突き合わせて、全部品が同じ場所にあるかを確かめる。
