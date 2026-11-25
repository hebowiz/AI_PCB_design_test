# 既存A-2レビュー成果物の整理計画

状態：計画のみ。2026-11-25の依頼では過去ファイルの移動・統合・削除、CAD変更、固定Workspace更新を行わない。

## 調査基準と規模

管理文書の基準はmain `666bf16c21e9d40d8a3ad13c718a291a158f82e3`、最新設計は`codex/a2-r0035-usb-edge`の`ca191ab2a900714d53f7ab0eb8984b58f3af7ef8`。Git追跡ファイルを`git ls-tree -rl`で数えた。ローカル一時ファイルやGit内部の容量は含まない。

| 対象 | フォルダ・ファイル | Git上の展開サイズ |
| --- | --- | --- |
| 設計側`reports/` | 直下20フォルダ、合計1,467ファイル | 137,788,988 bytes |
| main側`docs/reviews/` | 110ファイル。details 13、batches 22、evidence 71、その他4 | 4,554,705 bytes |

設計側はJSON 540、PNG 360、Python 247ファイルを含む。旧設計のコピー、最終成果物、試行結果が同じreports以下にある。全ファイルの技術的価値を査定した数ではない。

## 生成処理の調査結果

| 処理 | 現在の振る舞い | 今後の扱い |
| --- | --- | --- |
| `scripts/export.ps1` | reports直下へERC/DRC/ネットリスト/PDFを出力し、同時にGerber・穴・実装座標・BOMも更新 | 旧生成処理は保持。レビュー用途では個別CLIコマンドを使い、製造出力と分離 |
| `scripts/generate.py`、`finalize.py` | CAD生成とmanifest/BOM出力が結び付いている | 保存方式変更のためには再実行しない |
| `scripts/verify.py`、`preview.py`等 | reports直下の固定名へ出力、旧ネットリストの場所にも依存 | 次回必要時に読み取り検査・描画部分を共通ツールへ抽出し、明示引数化 |
| `reports/usb_edge/scripts/common.py` | レビュー名のOUT、候補CAD、特定Worktree名をハードコード。`drc(name)`で試行別JSONを生成 | 旧ファイルは保持。コピーの試行先をローカル一時領域へ向ける |
| `reports/header_layout/scripts/common.py`、`pcb_power_polish/scripts/common.py` | 上記と類似した専用コードの複製 | 配線変更処理と再利用可能な読み取り検査を分離してから抽出 |
| `quality_audit.py`、`verify_integrity.py`、`export_views.py`、`write_report.py`等 | JSON/画像を多数生成。旧レポート依存やmainログへの追記を持つものもある | 中間結果は一時保存。最終集計・合成画像だけ固定名へ。mainへの自動追記は分離 |

今回はこれらの旧スクリプトを変更・実行していない。新規の保存方式は[共通規約](review_artifacts.md)を正本とする。

## 整理対象と移行順序

| 既存のまとまり | 統合案・保護条件 |
| --- | --- |
| `schematic`、`schematic_v2`、`schematic_v3`、`schematic_v3_refine`、`schematic_v3_polish` | V0/V1/V2/V3の比較実験の意義を保持。比較レポートに各固定SHAを記録し、画像の復元を確認してから通常フォルダからの撤去を検討 |
| `review_R-0001`、`review_batch1`、`review_batch2`、`review_capacitors`、`review_drawing`、`review_reset_flags`、`review_usb5v_jumper` | R-0001〜R-0016の技術履歴・承認・接続検証を固定履歴の対応節へ統合。全IDの台帳と照合 |
| `pcb_sync`、`pcb_review_batch1`、`pcb_quality_revision`、`pcb_power_polish` | 同期・局所撤去承認・配線検査の例外・未検証条件を保持。採用結果と試行結果を区別し、再利用する検査だけ抽出 |
| `3d_models`、`header_layout`、`header_alignment_fix`、`usb_edge` | モデルの出典・利用条件、生成コード、J2補正の再試行、J1のメーカー寸法根拠を保護。モデルREADME等からの参照も調査 |
| reports直下48ファイル | BOMや旧製造証跡も混在。最終判定の根拠と再生成可能な中間物を個別分類 |
| `docs/reviews/details/`、`batches/`、`evidence/` | 技術履歴を固定履歴へ統合し、旧リンクを固定SHA付きに置換して検証。判定・日時・当時の状態を変えない |

実施する場合の順序は次のとおり。

1. ユーザーの整理承認後、対象ブランチ・基準SHA・対象一覧・各ハッシュを固定する。mainと設計の整理は別コミットで扱う。
2. 新規方式を次回レビューで一度運用し、固定成果物から検証内容を追えるか確認する。
3. 共通ツールへ抽出する検査を同一入力で旧処理と比較する。単発の部品移動や特定UUIDの撤去コードは汎用化しない。
4. 技術履歴・主要証拠を固定ファイルへ統合する。全レビューID、判定者・日時・判定、修正SHA、未検証事項を前後比較する。
5. 旧パスの被参照を検索し、固定GitHubリンクまたは固定履歴アンカーへ置換する。CADの3Dモデル参照、生成依存、メーカー資産の配布条件も確認する。
6. GitHubの保存済みSHAから代表的なCAD・検証・画像・モデルを一時領域へ復元して照合する。全体のファイル一覧・ハッシュも一致させる。Git未管理・公開不可の資産は別途保全し、Gitで復元できると見なさない。
7. 承認した範囲だけ通常フォルダから撤去する。Git履歴の書換えやforce pushはしない。固定Workspaceへの適用は別途安全な更新として扱う。

既存ディレクトリを別の`archive/`へ丸ごと移すだけでは、ファイル増加の問題は解決しない。目標は固定成果物・固定履歴・機能別共通ツールに絞ること。ただし履歴ファイルの本文とGit容量は増える。今回は旧ファイルを残すため、すぐに既存1,467ファイルが減るわけではない。
