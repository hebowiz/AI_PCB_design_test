# 人間が参照する設計の固定ワークスペース

## 原則

レビュー用のブランチやGit Worktreeは都度増えても、**人間がKiCadで開くローカルパスは固定**する。

- リポジトリ直下の`workspaces/`は`.gitignore`で除外する。
- 各`workspaces/<CASE>/`は**単なる設計ファイルのコピーではなく、独立したGit Worktree**。その内部での設計変更はGitにより追跡できる。
- `main`は共通仕様、レビュー台帳、スキルの正本として維持。**`main`のA-2 CADを最新だと仮定しない。**
- `workspaces/`の中身はローカル専用。GitHubにフォルダがないことは設計消失を意味しない。
- レビュー未承認の設計を、固定フォルダへ勝手に昇格させない。最終OKした修正版を基準に、更新可能ならfast-forwardする。
- Worktree内で人間がCAD編集した場合は、未コミット変更を保護。Codexが見つけたら上書きせずに報告する。

## A-2固定パス

```text
<ローカルリポジトリ>/workspaces/A-2/01_New_Design/kicad_direct/a2_usb_uart.kicad_pro
```

リポジトリのルートからは：

```powershell
git worktree list
git -C workspaces/A-2 branch --show-current
git -C workspaces/A-2 rev-parse HEAD
```

**初回作成元**：`codex/a2-r0016-usb5v-jumper` / `fffbcdbe41bad236baee48d88cf96b95f27421f4`（2026-11-22、ユーザーOK）。

**ローカルの固定ブランチ**：`workspace/a2-active`。人間が開くパスは変更しない。後続レビューが承認されたら更新する。新しい承認済み版へ移った場合はこの文書の基準情報も更新する。

**初回移行前提**：`workspaces/A-2/`はGitHubから自動生成されない。ローカルのCodexでWorktree作成が必要。今回のスキル追加コミットはローカル移行完了の証明ではない。

## 現時点で一致していない範囲

A-2最新の回路図はR-0016を反映しているが、**PCB・BOM・Gerberは初期設計のまま**。同一フォルダに`.kicad_pro`, `.kicad_sch`, `.kicad_pcb`があることは、回路図とPCBが一致することを意味しない。PCB同期後に改めて設計検証する。

## Codexの基本ルール

- ローカルパス確認・初回移行・承認後の更新には[design-workspace-management](../.agents/skills/design-workspace-management/SKILL.md)を適用する。
- 共通規則の正本は`main`。最新ルールがデザインブランチの古い`AGENTS.md`には反映されていない可能性があるため、**main側のルール/スキル**を読み込む。
- 複数作業セッションの同時編集・ブランチ切替は避ける。既存ローカルWorktreeを無断削除しない。
- 将来B-2やA-1/A-3へ展開する際は、各ケースのCAD・作業方針を確認し`workspaces/<CASE>/`を採用する。

Windowsでの安全な初回作成・更新手順は[こちら](../.agents/skills/design-workspace-management/references/windows-setup.md)。
