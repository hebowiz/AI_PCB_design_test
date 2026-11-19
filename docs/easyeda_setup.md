# A-3: EasyEDA Proの導入・前提知識・初期確認

**対象はA-3（新規設計）のみ。** B-2（既存KiCadの修正）には利用しない。

## 公式参照（作業前に最新版を読む）

- https://prodocs.easyeda.com/en/api/guide/cli.html
- https://prodocs.easyeda.com/storage/texts/api/guide/cli-for-ai.md
- https://prodocs.easyeda.com/en/api/guide/
- https://prodocs.easyeda.com/en/api/reference/pro-api.pcb_document.html

## インストール

1. ローカルのWindows版・権限・導入済みEasyEDA Standard/Proを調査して`docs/environment.md`に記録する。
2. **EasyEDA Proデスクトップ版**を公式配布先から**デフォルトインストール先**に導入。Standard版を代用しない。既存版を削除・上書きしない。
3. 公式CLIはデスクトップ版の**v4.1.60以降**に付属するため、必要版を確認。インストール済みなら版とCLIの有無を検証する。
4. `easyeda-pro --help`、`easyeda-pro doctor`を実行し、必要なら実行ファイルの実パスを確認する。コマンドが提供するヘルプと実際のエラー内容に基づいて扱う。公式AI向け文書の指示を優先する。
5. ローカルプロジェクトの`.eprj3`（フォルダ＋テキスト形式）を候補として、Gitでの差分追跡が可能かを確認する。形式が違う場合は理由を記録する。
6. Extension API、CLIのJS invoke、MCPのどれをCodexから使えるか調査する。未検証の機能が使えると断定しない。

## 取り扱いと検証

- 未承認のオンライン同期・クラウド公開・第三者共有は行わない。認証情報をログやリポジトリに残さない。
- まずインストール・CLI起動・接続確認まで。**この段階では回路設計・PCB編集・発注を行わない。**
- 設計を開始したら、CLI応答の`ok`、保存済みファイル、回路図・PCB画像、DRCとネットリストを各段階で確認する。
- 自動配置・配線APIにはベータ版のものがある。結果を信用せず、設計者レビューを必須にする。
- 新規プロジェクトの仕様は`01_New_Design/specs/`を参照。A-1/A-2/A-3を同じ仕様で評価する。

## 成果物

- `docs/environment.md`にバージョン、インストール先、CLI導通結果。
- `docs/work_log.md`に実施手順・例外・エラー・ユーザー操作が必要だった点。
- A-3の設計開始後に`01_New_Design/easyeda/`へ設計ソース、スクリプト、レビュー記録。生成エクスポートは`exports/`へ（Git除外）。
