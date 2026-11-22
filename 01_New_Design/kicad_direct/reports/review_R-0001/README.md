# R-0001 — USBのESD保護をESD321DPYR×2へ変更

ユーザーが承認した方針に従い、D1の2回路品を単素子2個へ置き換えた。回路図の修正・検証は完了し、ユーザーの最終レビューを待つ。実機の保護性能を保証する結果ではない。

- 作業ブランチ: `codex/a2-r0001-esd321`
- 起点: `experiment/A2-schematic-v3-polish`、`778ab8896a4f9b71efba0c45f701cbf2fdfc2cac`
- 共通台帳: mainの`docs/reviews/review_register.md`、詳細`docs/reviews/details/R-0001.md`
- 修正承認の発言: 「それでいこう。回路図の修正をお願い」。修正後のOK判定とは別に扱う。

## 変更内容

| 部品 | 変更前 | 変更後 |
| --- | --- | --- |
| D1 | TPD2EUSB30DRTR、1番D+／2番D−／3番GND | ESD321DPYR、1番D+／2番GND |
| D5 | なし | ESD321DPYR、1番D−／2番GND |

D2～D4の番号・値・配置は維持した。D1のシンボルUUIDを保持し、D5には新しいUUIDを付与した。D1とD5は単方向TVSの極性を表すKiCad標準`Device:D_Zener`を使用し、品種はValue・MPN・Note・データシート欄で明記した。双方向の`Device:D_TVS`は使用していない。DPYの1番IOをカソード、2番GNDをアノードへ割り当てた。[TIデータシートRev. C、§4](https://www.ti.com/lit/ds/symlink/esd321.pdf)

フットプリントはKiCad標準`Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm`を指定した。既存のローカルライブラリは変更していない。USBの主配線は保持し、部品への分岐を2.54 mm、GND引き出しを1.27 mmとした。これは回路図上の長さであり、PCBの寸法や寄生特性ではない。

版番号を`A2-R0001 REVIEW`へ変更し、図中へPCB/BOM未更新・レビュー待ちの注記を入れた。

## 検証結果

| 検査 | 結果 |
| --- | --- |
| KiCadネットリスト | 承認した端子差分だけが発生。その他の部品・端子接続は一致 |
| 実部品数／端子数／ネット数 | 58→59個、207→208端子、58→58ネット |
| ERC | 前後ともエラー0・警告0。既存の除外設定を変更していない |
| D1以外の既存実部品 | XML属性と接続が一致 |
| その他のシンボル | D1と移動したGND表示以外は位置・属性・UUIDを含めて一致 |
| 配線 | 旧分岐・GNDの3線分を削除して4線分を追加。それ以外の配線・接続点・ラベル・NCを保持 |
| 保護ファイル | 回路図を除く既存767ファイルのGit blobが一致 |
| 図面 | 全体図・USB拡大図・修正注記を確認。確認範囲で文字・部品・配線の重なりなし |

今回は電気的な部品変更を含むため、ネットリスト全体の完全一致を合格条件にしていない。期待するD1/D5の変更を明示し、それ以外の一致を検証した。機械検証は`verification.json`の15項目と`preservation.json`の8項目がすべて合格。

## レビュー用成果物

- [修正後PDF](after/schematic.pdf)、[全体PNG](after/schematic.png)、[USB拡大図](after/usb_detail.png)
- [修正前PDF](before/schematic.pdf)、[修正前PNG](before/schematic.png)、[前後比較](comparison_usb.png)
- [接続・属性・ERCの検証](verification.json)、[保全検証](preservation.json)、[保護ファイル一覧](protected_files.csv)
- [修正前ERC](before/erc.json)、[修正後ERC](after/erc.json)
- [修正前ネットリスト](before/netlist.xml)、[修正後ネットリスト](after/netlist.xml)
- [操作ログ](commands.json)、[作業記録](work_log.md)

## 残件

PCB、既存BOM、Gerber、製造データは更新していない。これらには旧D1が残っており、修正回路図との整合は未達。この状態の製造データを修正版として扱わない。PCBへの反映とDRCは今回の依頼範囲に含めていない。

FT232Hの過渡耐性との保護協調、初期オーバーシュート、実装後のESD試験・USB信号品質は未検証。部品の選定・回路修正の承認を、これらの性能承認に読み替えない。発注・メーカーへの連絡は行っていない。

補助スクリプト`change_esd.py`は起点の回路図とのバイト一致を要求し、手編集があれば上書きを拒否する。過去の生成スクリプトは実行していない。今後の編集後に再生成目的で使用しない。`--export-after`は出力と検証だけを行う。修正前の回路図コピーは証跡用で、単独プロジェクトではない。
