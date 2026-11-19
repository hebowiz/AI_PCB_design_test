# 2026-11-19 リモート環境レポートのレビューと対応方針

対象リポジトリ: `hebowiz/AI_PCB_design_test`
レビュー対象コミット: `936c279edff5503133ce6fb789f927a90a8f99df`

## 重要な区別

この文書は**リモートに記録された実施結果のレビュー**。ここで新しく提案する修正は未実施であり、ローカルPCに対する検証結果ではない。

| 検証系 | 現在の状態 | 判断 |
| --- | --- | --- |
| A-1 atopile + KiCad | KiCad 10.0.8/pcbnew 10.0.8動作、Freerouting 2.1.0起動。atopile 0.15.8は`pyzig`の不正命令でCLI起動不可 | **ブロッカー** |
| A-2 KiCad | KiCad CLIおよびpcbnew import成功。回路図/PCBの実編集は未検証 | **新規設計のスモーク試験に進める** |
| A-3 EasyEDA Pro | 4.1.105でアクティベーション後のCLI・MCP・読み取り専用エディタAPIが成功。保存・再読込は未検証 | **小規模な保存/再読込試験に進める** |
| B-2 KiCad既存設計修正 | KiCadツールは起動。実データ・原本の保護・差分編集は未試験 | **対象データと保護手順が必要** |

## 課題1：atopile 0.15.8 Windows wheelのAVX-512障害（優先度：高）

### 観測された事実

- PCはIntel Core i7-12700、AVX2あり/AVX-512なし。
- atopile 0.15.8はuv経由でインストール済み。Python 3.14.10。
- `ato --help`、`ato --version`が`-1073741795`（`0xC000001D`）で停止。
- Windowsイベントの障害モジュールは`pyzig.cp314-win_amd64.pyd`、オフセット`0x444e4`。同環境で`import pyzig`も失敗。Windows版バイナリ内に非対応のAVX-512命令が含まれることを逆アセンブルで確認。
- [上流Issue #1838](https://github.com/atopile/atopile/issues/1838)は**open**で同じ版・オフセットを報告。
- [上流PR #1839](https://github.com/atopile/atopile/pull/1839)は**open / 未マージ**（レビュー時）。ビルド時に`ATOPILE_ZIG_CPU=baseline`を適用する修正案を説明し、公開Windows wheels 0.15.7/0.15.8/0.15.9の問題を確認している。

単純再インストール、PATHの調整、Pythonの通常の例外処理、アクティベーションでは解消しない。0.15.9への更新も根本対策ではない可能性が高い。

### 対応順（推奨）

**第1候補：Windows上でCPU baseline向けのネイティブモジュールを隔離ビルドする。**

1. 既存の`uv tool`環境とパッケージを保存し、元の`*.pyd`を破壊しない。
2. 公開された**atopile 0.15.8の正確なソース配布物**とハッシュを取得し、Zig/CMake/Pythonビルド要件を調査。新しいmainのソースと混在させない。
3. 上流PR #1839と該当リリースのビルド方式を参照し、CPUターゲットを`baseline`へ固定する。設定の有効性をビルドログで確認する。
4. `pyzig`と`pyzig_sexp`などの必要なネイティブモジュールを**同じソース/ABI/ビルド条件**で生成し、隔離環境のPython 3.14で`import`、`ato --version`、`ato --help`を確認する。
5. 利用可能なときは生成バイナリの命令セットも検査し、AVX-512を必須とする命令が含まれないことを確認する。
6. **隔離環境での動作確認後に限り**、正式環境への取り込みを検討する。元ファイルのバックアップ、復旧方法、変更ハッシュ、テスト結果を残す。

注意: `ATOPILE_ZIG_CPU=baseline`は上流で修正案として使われる値だが、0.15.8のソースにそのまま適用できるかは未確認。実際のCMake/Zig設定を調べてから使うこと。**未検証コマンドをそのまま実行しない。**

**第2候補：Linux環境（既存のWSL2がある場合を含む）で0.15.8を動かす。**

- 上流IssueではLinux向けwheelに同じAVX-512問題がないという報告がある。
- WSL2を新規に有効化するにはWindows機能・再起動などが必要であり、**ユーザーの承認がない限り実施しない**。
- Windows版KiCadとLinux側`pcbnew`のABIを混在させない。A-1のパイプラインはLinux内でのKiCad、make、Freeroutingを含めて一貫させるか、受け渡し境界を別途設計する。

**採用しない近道：atopile 0.16以降へ無条件で置換すること。**

- 上流公式発表では0.16からWeb/クラウド実行中心へ変更されている。現在リポジトリにコピーした`pcb-pipeline`が依存する0.15.8 CLIとは別の設計・実行経路になり、比較条件が変わる。
- 0.16以降を別実験として扱うことは可能だが、A-1の0.15.8を代替したことにはしない。
- 旧バージョンの部品選定はサインインと外部サービスに依存するため、CPU障害解消後も`ato auth login`と部品取得の確認が必要（認証は本人操作）。

## 課題2：A-1の補助ツール/Windowsパス（優先度：中）

- 上流MakefileがGNU make、zip、librsvg/rsvg-convert等を要求しているが、Windows環境に未配置。
- Git Bashは既存。KiCad同梱Python 3.11.5で`pcbnew` importに成功。別Python（atopile用3.14）へ`pcbnew`をコピーしない。
- `C:\Program Files\...`のパスに空白があるため、Bash/PowerShellのコマンドで確実に引用する。
- A-1がCLI起動できるまでは不要なパッケージをむやみに増やさず、必要な追加機能を把握して最小限導入する。
- 元スキル`.agents/skills/pcb-pipeline/`は上流コピー。Windows修正を入れる場合は**別のプロジェクト専用ラッパー**を優先し、上流ファイルを書き換える場合は差分を残す。

## 課題3：Freerouting設定とDSN/SES（優先度：中）

- 2.1.0 JARの起動は成功。**自動配線成功を意味しない**。
- 上流の`route.sh`が一時ディレクトリに置く`freerouting.json`と、実際に2.1.0が設定を読むユーザーデータ領域が一致するか未確認。
- 実配線に進む前にCLIの`--user_data_path`・設定ファイル配置・ログの有効反映を最小設計で検証。
- 設定の反映、SESファイルの生成、KiCadへの取り込み、配線後DRC/未接続数を別々に記録。ルータの違反数0だけでは完了と判定しない。

## 課題4：EasyEDA Proの初回アクティベーション（既に解除、優先度：低）

- 認証前の`BRIDGE_NOT_READY`、`REQUEST_TIMEOUT`、HTTP 400は記録済み。
- ユーザーの認証操作後、`open --headless true`、`invoke`による読み取り専用APIが成功し、現時点のブロッカーではない。
- `.eprj3`の実作成、保存、再読込、ERC/DRC、PCB編集は未実施。最小のローカルプロジェクトで試す。無断でクラウド公開や発注はしない。
- Codexへの常設MCP登録は未実施だが、CLIが使えるなら開始に必須ではない。

## 並列実験への影響

- **A-2とA-3はA-1の修復を待たずに先行可能**。ただし共通仕様をコミットで固定する。
- A-1のCPU障害修復は別作業に分離する。Worktreeはコードを隔離するが、PCに導入したアプリ、グローバル環境、GUIセッションは共有される。
- 同時セッションが`docs/work_log.md`等を同時編集すると競合するため、設計セッションごとのローカルログを方式別に保存し、統合時に共通ログへ要約する。

## 参照

- リモート実測: `docs/environment.md`, `docs/work_log.md`, `docs/knowledge_baseline.md`
- 上流Issue: https://github.com/atopile/atopile/issues/1838
- 上流PR: https://github.com/atopile/atopile/pull/1839
- 上流方針: https://atopile.io/blog/atopile-v16
- EasyEDA CLI: https://prodocs.easyeda.com/en/api/guide/cli.html
