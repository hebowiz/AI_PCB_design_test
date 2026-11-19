# Codex作業指示：A-1のatopile起動障害を安全に切り分け・修復する

まず`AGENTS.md`、`docs/environment.md`、`docs/work_log.md`、`docs/setup_issues_2026-11-19.md`を読む。現在のGit差分と使用ツールを検査する。**回路・基板の設計は今回始めない。**

## 目的

Windows 11 + i7-12700においてatopile 0.15.8を起動すると`pyzig.cp314-win_amd64.pyd`が`0xC000001D`で停止する。公開Windows wheelのAVX-512不整合が原因と考えられる。既存環境を壊さず、まずWindowsネイティブのCPU互換版が成立するか調査・検証する。

## 実施内容

1. 起動障害、Python版、バイナリの保存先、`uv tool list`、CPU命令セットを再確認し、**既存の`uv`管理環境を変更しない**。
2. 上流Issue https://github.com/atopile/atopile/issues/1838 とPR https://github.com/atopile/atopile/pull/1839 を読む。0.15.8の正確な配布ソースと必要なビルドツール、Zig/CMakeビルド設定を調査する。
3. `ATOPILE_ZIG_CPU=baseline`などCPUターゲット固定方式が当該ソースで本当に有効か確認する。**効果が確認できない場合はビルドを強行しない**。
4. 必要なビルド依存をインストールする場合は**プロジェクト外の既存環境を壊さない方法**を優先し、必要なものと変更範囲を明示する。
5. `.setup-local/atopile-rebuild/`等のGit除外ローカル領域に隔離環境を作り、0.15.8の同一ソースからCPU baseline対象のネイティブモジュールを生成する。**元の配布`*.pyd`を上書きしない**。
6. 生成物のABI・対応Python版・命令セットを確認し、隔離環境で`import pyzig`、`import pyzig_sexp`、`ato --version`、`ato --help`を実行。各段階の終了コード・ハッシュ・結果を記録する。
7. 修復ができれば移行手順と復旧方法を提案する。既存の稼働中環境に差し替える前には、対象ファイル・復旧方法・動作確認結果を整理する。
8. ビルドできない場合は、原因を記録しWSL2案を具体化する。**WSL2有効化、OS機能の変更、再起動、既存ツールのアンインストール、atopileの版変更は、ユーザーの明示承認なしに実施しない**。

## 並行作業・他の未解決事項

- A-2（KiCad）とA-3（EasyEDA Pro）のセットアップを壊さない。EasyEDAは認証後のエディタAPIまで起動確認済みなので再インストール不要。
- GNU make/zip/librsvg不足、Freerouting設定パスの課題は`docs/setup_issues_2026-11-19.md`に沿って切り分け、**本タスクではまずatopile障害を優先**する。
- 修正を上流`pcb-pipeline`へ直接混ぜず、必要なら別のWindows互換ラッパーを作る。
- 生ログ・バイナリ・ユーザーパス・認証情報は公開GitHubに載せない。作業ログは`docs/work_log.md`、環境更新は`docs/environment.md`へ追記し、レビューしやすい差分にまとめる。
- コミット・pushはAGENTS.mdの運用規則に従い、他のCodexセッションの変更を消さない。

## 終了報告

「試した方式」「実際の結果（成功/失敗/未実施）」「作成した隔離環境」「変更範囲」「ユーザー判断が必要な事項」「次の最短経路」を区別して日本語で報告する。
