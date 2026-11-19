# 設計規則とネットクラス

既定のまま流すと、電源も信号も全部 **0.2mm 幅、0.2mm 間隔、ビア 0.6/0.3mm** で
引かれる。atopile はネットクラスを書かないので、指定しない限りこうなる。
今回の基板は電流がほとんど流れなかったので通っただけで、次もそうとは限らない。

## 幅の目安

外層 1oz、温度上昇 10℃ のときの許容電流 (IPC-2221 の式)。

| 幅 | 目安 |
| --- | --- |
| 0.2 mm | 約 0.7 A |
| 0.5 mm | 約 1.4 A |
| 1.0 mm | 約 2.4 A |

内層は放熱が悪いので半分程度に見る。正確な値は KiCad の PCB Calculator で出す。
間隔は電圧で決まる。同一基板上の低電圧なら 0.2mm で足りるが、商用電源が
絡むなら沿面距離の規格に従う。

## ネットクラスの設定

ネットクラスはレイアウトの `.kicad_pro` にある。`net_settings.classes` に
定義を足し、`net_settings.netclass_patterns` でネット名を割り当てる。

```json
{"net_settings": {
  "classes": [
    {"name": "Default", "track_width": 0.2, "clearance": 0.2,
     "via_diameter": 0.6, "via_drill": 0.3},
    {"name": "Power", "track_width": 0.5, "clearance": 0.25,
     "via_diameter": 0.8, "via_drill": 0.4, "priority": 1}
  ],
  "netclass_patterns": [
    {"netclass": "Power", "pattern": "hv"},
    {"netclass": "Power", "pattern": "lv"}
  ]
}}
```

`priority` は小さいほうが優先。パターンはワイルドカードも使える。

## Freerouting に伝わるか

伝わる。DSN の `network` 節にクラスごとの塊として出る。単位は µm。

```
(class Power hv lv
  (circuit (use_via "Via[0-1]_800:400_um"))
  (rule (width 500) (clearance 250)))
```

**DSN を出して `(class` を見れば、意図した幅になっているか確認できる**。
ここに出ていない規則はルータに伝わっていない。

## 4 層にするとき

atopile の `JLCPCB.ato` に JLCPCB の 4 層スタックアップの定義が入っている。
層構成を変えたらレイアウトを作り直す。内層をベタにするなら、配線後に
ゾーンとして流し込む手順は 2 層のときと同じ。
