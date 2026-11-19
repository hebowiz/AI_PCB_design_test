# Codex実行指示：3設計手段・4検証ケースの前提把握とEasyEDA Pro導入

作業対象：`hebowiz/AI_PCB_design_test`（Windows PCのローカルclone）

## 目的

プロジェクトの定義を次のとおり理解し、A-3（EasyEDA Proによる新規設計）の環境を構築する。今回の作業は**セットアップまで**であり、回路・PCBの実設計はまだ行わない。

| 設計手段 | A: 新規設計 | B: 既存KiCad設計の修正 |
| --- | --- | --- |
| 1. atopile + KiCad | A-1 | 実施しない |
| 2. KiCad | A-2 | B-2 |
| 3. EasyEDA Pro | A-3 | 実施しない |

**2つの検証内容×3手段という分類で、対象は合計4ケース。** Bの対象は手段2のみ。元の①②のセットアップを壊さずに、③を追加する。

## 実施順序

### 1. 共通ルールと前提知識の把握
- 最初にルート`AGENTS.md`を読んで遵守する。続いて`README.md`、`docs/comparison_matrix.md`、`docs/setup_plan.md`、`docs/easyeda_setup.md`を読む。
- `docs/discussion_log.md`、`docs/decision_log.md`、`docs/work_log.md`、`docs/report_outline.md`、既存の`docs/knowledge_baseline.md`、`docs/environment.md`（存在する場合）も読む。
- `.agents/skills/pcb-pipeline/SKILL.md`はA-1専用の上流スキルとして理解する。A-2やA-3に無断適用しない。
- 既存の成果・進行中の作業を尊重し、`docs/knowledge_baseline.md`があれば内容を保持して3手段4ケースに合わせて追記・修正する（他の担当作業を消さない）。

### 2. ディレクトリ構成の点検
- `01_New_Design/specs/` = Aに共通の要求仕様
- `01_New_Design/atopile/` = A-1
- `01_New_Design/kicad_direct/` = A-2
- `01_New_Design/easyeda/projects/` = A-3の設計プロジェクト
- `01_New_Design/easyeda/scripts/` = A-3のスクリプト・CLI操作
- `01_New_Design/easyeda/reports/` = A-3のテスト・レビュー記録
- `01_New_Design/easyeda/exports/` = A-3の生成ファイル（Git除外）
- `02_Design_Modification/original/`、`working/`、`reports/` = B-2のみ
- `docs/` = 全方式共通の履歴・環境・比較評価

必要なフォルダのみ作り、既存のファイルやフォルダを無断で移動・削除しない。ローカルで進行中の差分を優先し、衝突時は作業を止めて状況を報告する。

### 3. EasyEDA Proの環境構築
1. Windowsのアーキテクチャ・導入済みEasyEDA Standard/Pro・バージョンを調査する。
2. `docs/easyeda_setup.md`に記載された**公式ドキュメントを最新状態で確認**し、CLI・MCP・Extension APIの実際の対応範囲を把握する。
3. EasyEDA **Proデスクトップ版**の必要な対応バージョンを公式配布元からデフォルトのインストール先へ導入する。既存版が要件を満たせば再導入しない。Standard版との混同に注意する。
4. 導入後、公式資料と実際のCLIヘルプに基づき、版、CLI起動、診断コマンド、利用可能なAPIインターフェース、プロジェクト保存形式を確認する。例：`easyeda-pro --help`、`easyeda-pro doctor`（実際に提供されていることを確認してから実行）。
5. CodexからCLI/API/MCPを呼び出す接続方式を調べて、現段階で確認できた範囲と、追加の認証・GUI起動等が必要な範囲を分ける。
6. Windowsネイティブで問題が出た場合は、失敗理由と回避案を比較して記録。無断でWSL、Docker、OS設定を変更しない。

### 4. 動作確認と記録
- **インストール済み**／**CLI起動確認済み**／**実設計ワークフロー確認済み**を分ける。今回は前2つが対象。
- 既存のKiCad、atopile、Freerouting環境の作業結果を勝手にリセットしない。
- `docs/environment.md`: EasyEDA版、実際のインストール先、CLI/APIの確認結果、依存と未解決事項を追記。
- `docs/work_log.md`: 日付、実行操作・コマンド、結果、失敗・再試行、作成/変更したファイルを追記。
- `docs/decision_log.md`: 新たな採用・保留判断が生じた場合だけ追記。
- `docs/knowledge_baseline.md`: 既存の①②も含めた3手段4ケースの前提知識を明確にする。
- 認証情報、ユーザーの個人パス、社内の非公開設計、外部公開不可の資産は公開GitHubへコミットしない。

## 完了条件
- A-1/A-2/A-3/B-2という検証構成と各作業領域を正しく把握できた。
- EasyEDA Proを導入できたか、導入できない場合は正確な理由と対応案を記録した。
- CLIとAPIについて**実際に確認した機能と未確認機能を区別**した。
- 設計生成・発注・クラウド公開・他方式の既存成果物の改変は行っていない。
- 最後に、実行した内容、結果、残課題と人間の操作が必要な事項を日本語で報告する。

オンラインアカウント認証・外部送信・クラウド同期・製造発注は明示承認なしに進めない。
