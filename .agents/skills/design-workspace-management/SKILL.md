---
name: design-workspace-management
description: "Keep a fixed local Git worktree path for the current human-reviewable CAD design, including KiCad, without merging review branches into main or overwriting user edits. Resolve the active reviewed revision, set up and safely advance workspaces, and report the exact project path."
metadata:
  version: "0.1.0"
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
- **レビューの最終OKとCADの更新、PCBの同期は別**。現在のA-2は回路図だけR-0016まで反映、PCB/BOM/Gerberは旧設計であり、固定Worktree作成だけで一致したと主張しない。
- CAD設計の承認版と実際に作業中の未承認版を混同しない。未承認変更のレビュー中は固定フォルダ内を黙って入れ替えない。
- A-1/A-3/B-2への導入は各ケースの適切なCAD形式と保護条件を確認してから独立`workspaces/<CASE>/`で実施する。A-2用のブランチやスクリプトを無条件に転用しない。

## 補足

- [ローカルWorktreeの運用ルール](../../../../docs/design_workspaces.md)
- [安全な初回セットアップ・更新コマンド](references/windows-setup.md)
- 設計の電気的検証は`schematic-design`、議事録は`design-review-records`など既存の役割に従う。本スキルはワークスペース運用だけを担当。
