# Windows / PowerShell：A-2固定Worktreeへの初回移行

**この手順を実行するのはローカルPCのCodex。ChatGPT側からローカルWorktreeを作成したことにはならない。**

## 初回

既存のメインWorktree（`main`）のルートで実行する。ローカルリポジトリの実際の絶対パスはCodexが取得する。

```powershell
$repo = (git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Not in Git repository' }
Set-Location $repo
git fetch origin
git worktree list --porcelain
git status --short
git branch --show-current
```

1. 実際に`main`Worktreeへいること、未コミットの編集や他セッションの作業との競合がないことを確認する。main作業フォルダに変更があるなら破棄しない。
2. `git show main:.agents/skills/design-workspace-management/SKILL.md`で**main側のスキル**が実際に読み込めることを確認する。
3. `origin/codex/a2-r0016-usb5v-jumper`が`fffbcdbe41bad236baee48d88cf96b95f27421f4`を指すか、GitHubとの同期が取れているか確認する。現時点の承認済み版がより新しければ**その最新の承認済み版**を優先し、理由を記録する。
4. 既存`workspaces/A-2`の存在、`workspace/a2-active`ブランチが既存か否かを確認。存在する場合は決して上書きせず、まず既存Worktreeとその状態を調査する。

初回にどちらも存在しない場合：

```powershell
$dest = Join-Path $repo 'workspaces/A-2'
if (Test-Path $dest) { throw "Destination already exists: $dest" }
git show-ref --verify --quiet refs/heads/workspace/a2-active
if ($LASTEXITCODE -eq 0) { throw 'workspace/a2-active branch already exists; inspect first' }
git worktree add -b workspace/a2-active $dest origin/codex/a2-r0016-usb5v-jumper
if ($LASTEXITCODE -ne 0) { throw 'git worktree add failed' }
git -C $dest status --short
git -C $dest rev-parse HEAD
git worktree list
$project = Join-Path $dest '01_New_Design/kicad_direct/a2_usb_uart.kicad_pro'
if (-not (Test-Path $project)) { throw "KiCad project not found: $project" }
Write-Output $project
```

このコマンドはローカルブランチを新規作成するだけで、既存レビュー用ブランチの内容や履歴を変更しない。個人のPC環境に依存するため、実際の実行はCodexが都度確認・検証する。

## 継続利用

ユーザーがKiCadで開く場所：

```text
<ローカルリポジトリ>/workspaces/A-2/
  01_New_Design/kicad_direct/
    a2_usb_uart.kicad_pro   ← KiCadプロジェクトマネージャから開く
    a2_usb_uart.kicad_sch   ← 回路図：現在の対象SHAで確認
    a2_usb_uart.kicad_pcb   ← PCB：同期状態は対象版の検証証跡で確認
```

現在の固定Worktreeの正確な状態：

```powershell
git -C (Join-Path $repo 'workspaces/A-2') status --short
git -C (Join-Path $repo 'workspaces/A-2') branch --show-current
git -C (Join-Path $repo 'workspaces/A-2') rev-parse HEAD
```

## 次回レビューOK後の更新

1. 更新先`workspace/a2-active`が前回承認済み版であることを確認。
2. 対象設計が本当にユーザー承認済みか、修正コミットと台帳を確認。
3. 更新先の作業内容に未コミット変更がないことを確認。KiCadは閉じる。
4. 新しい設計コミットが既存コミットの子孫であることを確認する。**不一致なら停止**。
5. その場合だけ固定Worktreeで`git merge --ff-only <承認済みブランチ名>`。成功後`git rev-parse HEAD`が期待SHAと一致することを確認。
6. 新たなERC・DRC/PCBの未同期範囲を**移行の成功と混同せず**報告。

### しないこと

- `main`とレビュー設計ブランチのマージを版更新の代わりに行わない。
- `git reset --hard`、`git clean -fd`、既存Worktreeの削除を無断で行わない。
- 回路図だけを古い`main`へコピーして上書きしない。
- 既存のCADファイルを再生成しない。

## 固定成果物の確認

新方式の設計版では`01_New_Design/kicad_direct/reports/current/manifest.json`の入力ハッシュをCADと照合する。ファイルの存在だけで最新・検証済みと判断しない。過去結果はGitの固定SHAから一時領域へ取り出し、固定Workspace内にレビュー別コピーを作らない。旧方式の版を更新する際は旧成果物をそのまま保護し、この手順を理由に再生成しない。共通規約は[固定保存方式](../../../../docs/review_artifacts.md)を参照。

## 人間実演・AI実践の初期作成

`docs/design_workspaces.md`で共通基準SHAを確認し、上記の存在確認・新規ブランチ作成手順を次の2組に適用する。両方の作成先とブランチを先に確認し、既存であれば作成を停止して内容を調べる。

| 作成先 | 新規ローカルブランチ |
| --- | --- |
| `workspaces/A-2-human` | `workspace/a2-human` |
| `workspaces/A-2-ai` | `workspace/a2-ai` |

`git worktree add -b <branch> <dest> <完全な共通基準SHA>`で作成し、両方のHEADとCADのGit blobを照合する。Git管理外のUSBモデルは、既存の出典・ハッシュを確認して新しい環境へ配置する。既存ファイルがあれば上書きせず照合する。公開Gitには追加しない。

manifestの入力ハッシュも確認する。チェックアウトの改行変換による差だけなら、新規環境に限り検証済みの入力とバイト列を揃えてよい。Gitの作業差分・ステージ差分がなく、設計内容が基準から変わっていないことを確認する。

次事例への切替前には、人間が編集・保存を終えたことと未コミット変更がないことを確認する。共通基準が変わる場合は旧ブランチを残し、新しい事例ブランチへ通常の`git switch -c`で切り替える。進行中の人間用Worktreeへ自動merge、reset、stash、checkoutを実行しない。
