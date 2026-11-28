---
name: design-workspace-management
description: "Keep a fixed local Git worktree path for the current human-reviewable CAD design, including KiCad, without merging review branches into main or overwriting user edits. Resolve the active reviewed revision, set up and safely advance workspaces, and report the exact project path."
metadata:
  version: "0.2.0"
---

# CAD設計の固定Worktree管理

## 目的

人間がKiCad等で開く**作業場所を設計ケースごとに固定**する。レビューごとにGitブランチやコミットが増えてもCADの参照フォルダを変えない。

- メインのリポジトリ直下を基準に、A-2は`workspaces/A-2/`を使う。
- `workspaces/`はローカル専用・Git管理対象外（**ディレクトリはignoreするが内部は独立Git Worktreeとして管理**）とする。
- 現在のA-2最終承認済み回路図は`codex/a2-r0016-usb5v-jumper`の`fffbcdbe41bad236baee48d88cf96b95f27421f4`。これは**初回移行時の基準点**であり、将来の固定SHAを意味しない。
- 固定しているのはパスであり、中身は次の承認済み設計へ安全に更新する。
- 対象CADパス：`workspaces/A-2/01_New_Design/kicad_direct/a2_usb_uart.kicad_pro`。

## 自動適用の契機

「KiCadで最新を開く」「レビュー後の設計はどこ」「設計ファイルを開いて」「ローカル同期」「Worktree切替」「最新版を反映」「PCB設計へ進める」「固定フォルダで管理」など。ユーザーがスキル名を指定する必要はない。

## 作業を始める場所に注意

**本スキルと共通`AGENTS.md`の正本は`main`のリポジトリルートにある。** 古い設計コミットから作成した作業Worktree内の`AGENTS.md`や`.agents/skills/`には、新しい規則が入っていないことがある。

Codexは設計Worktreeの内容だけを読み「最新版のスキルを適用済み」と主張せず、**main側の実ファイル**または`git show main:<path>`で共通ルールを読み、設計側の実行に反映する。新しい共通スキルをCADブランチへ勝手にマージ・cherry-pickしない。

## 初回移行

手順は[Windows / PowerShell用](references/windows-setup.md)を参照。

1. 現在のルート・Worktree・ブランチ・clean状態・対象設計の最新**承認済み**コミットを確認する。
2. `workspaces/A-2/`が未作成であることを確認する。既存フォルダの削除・上書きはしない。
3. A-2は`workspace/a2-active`ローカルブランチを、承認済み設計コミットから作成する。`git worktree add`を使い、単純コピーや手動上書きで版管理を分断しない。
4. `git worktree list`と`git -C workspaces/A-2 rev-parse HEAD`で、意図したGitコミットが開けることを確認する。
5. KiCadで開くべき**絶対パス**、現在のブランチ/コミット、回路図とPCBの同期状態をユーザーへ簡潔に報告する。
6. 初期移行はローカルGit操作のみでよい。既存ブランチ、設計、レビュー台帳、`main`のCADを変更しない。

## 以後の利用と更新

- 人間がKiCadから開くプロジェクトは常に上記の固定フォルダ。**`main/01_New_Design/kicad_direct`のファイルを最新版と取り違えない。**
- 新規レビュー修正は独立した設計ブランチで行い、最終承認された後に、固定Worktreeの`workspace/a2-active`を**fast-forwardのみ**で更新する。
- 更新前に固定Worktreeの`git status --porcelain`を検査。KiCadでの手動編集など未コミット変更があれば更新を停止し、保存/コミット/退避の方針を確認する。強制上書き、reset --hard、clean -fd、checkout -fは禁止。
- fast-forwardできない場合は勝手にmerge/rebase/cherry-pick/forceしない。コミットの系譜と人間による編集内容を調べ、方針を報告する。
- **レビューの最終OKとCADの更新、PCBの同期は別**。初回移行時は回路図だけR-0016まで反映されていた。現在の同期状態は対象SHAと検証証跡で確認し、固定Worktree作成だけで一致したと主張しない。
- CAD設計の承認版と実際に作業中の未承認版を混同しない。未承認変更のレビュー中は固定フォルダ内を黙って入れ替えない。
- A-1/A-3/B-2への導入は各ケースの適切なCAD形式と保護条件を確認してから独立`workspaces/<CASE>/`で実施する。A-2用のブランチやスクリプトを無条件に転用しない。

## 補足

- [ローカルWorktreeの運用ルール](../../../docs/design_workspaces.md)
- [安全な初回セットアップ・更新コマンド](references/windows-setup.md)
- 設計の電気的検証は`schematic-design`、議事録は`design-review-records`など既存の役割に従う。本スキルはワークスペース運用だけを担当。

## A-2成果物の保存方式

新規作業では[共通の固定保存方式](../../../docs/review_artifacts.md)を読む。最終出力は設計ブランチの`reports/current/`、新規の詳細・一括履歴はmainの`docs/reviews/history.md`へ集約する。レビューごとのreports・details・batches・evidenceを新設しない。既存記録は保持し、旧フォルダの整理は別途承認された範囲だけで行う。
Workspace更新時は、存在する`reports/current/manifest.json`の対象CADハッシュと実際のファイルを照合する。旧方式の版にはmanifestがないことを記録し、無断生成しない。成果物だけの後続コミットと設計コミットを区別する。更新のためにmainの規則を設計へマージせず、共通ツールはmain側から対象Worktreeを明示して実行する。

## 人間実演用とAI実践用

人間の修正実演・AIによる再現の環境準備にも本スキルを適用する。[固定環境の運用](../../../docs/design_workspaces.md#人間実演用とai実践用の固定環境)に従い、`A-2-human`と`A-2-ai`を同一の明示した基準SHAから作る。未承認候補を実演基準に使う場合はその状態を明記し、既存のレビュー用`A-2`を更新しない。

作成前に両パス・ブランチの存在を確認する。各環境のHEAD、CAD・設定・ライブラリ、ローカル専用モデルを照合し、初期差分がないことを確認する。人間の未保存・未コミット編集は保護し、実演完了の連絡後に差分の確定とコミットを担当する。AI側は当該事例の修正前データを維持し、実演結果を取り込まない。次事例の基準変更は旧履歴を残した別ブランチで行い、固定フォルダを増やさない。
