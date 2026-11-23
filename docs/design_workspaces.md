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

## 現在のレビュー対象

固定Worktreeは`codex/a2-pcb-sync`の`a300e1c7cd89654fd2800c1bc7b8bad59dae5516`を参照する。2026-11-23、ユーザーの更新指示によりPCBレビュー候補版を配置した。回路図はR-0016まで承認済み、PCBは回路図へ同期済みで、人間によるPCBレビューは未承認。

同期版の検証結果はERC・DRC・未配線・回路図不一致が各0件。今回のWorkspace更新ではCADのGit blob一致を検証し、ERC/DRCは再実行していない。詳細と未検証事項は同期版の`01_New_Design/kicad_direct/reports/pcb_sync/README.md`を参照する。BOM・Gerber・ドリル・実装座標は旧版のままで、同期後PCBには対応しない。

## Codexの基本ルール

- ローカルパス確認・初回移行・承認後の更新には[design-workspace-management](../.agents/skills/design-workspace-management/SKILL.md)を適用する。
- 共通規則の正本は`main`。最新ルールがデザインブランチの古い`AGENTS.md`には反映されていない可能性があるため、**main側のルール/スキル**を読み込む。
- 複数作業セッションの同時編集・ブランチ切替は避ける。既存ローカルWorktreeを無断削除しない。
- 将来B-2やA-1/A-3へ展開する際は、各ケースのCAD・作業方針を確認し`workspaces/<CASE>/`を採用する。

Windowsでの安全な初回作成・更新手順は[こちら](../.agents/skills/design-workspace-management/references/windows-setup.md)。

## ローカル移行結果

2026-11-23、このPCの固定Worktreeを次の場所に作成した。

```text
D:\Documents\KiCad\10.0\projects\99_AI_PCB_design_test\workspaces\A-2\01_New_Design\kicad_direct\a2_usb_uart.kicad_pro
```

ローカルブランチは`workspace/a2-active`、初期コミットは`fffbcdbe41bad236baee48d88cf96b95f27421f4`。最新の共通台帳とリモートを確認し、R-0016より新しい承認済み設計はなかった。プロジェクト・回路図・PCBのGit blobが初期コミットと一致し、Worktreeが未変更であることを確認した。

既存のレビュー用Worktreeと設計ブランチは保持した。PCB・BOM・Gerberは回路図と未同期のまま。今後は承認済み版への更新前に未コミット変更とコミットの系譜を確認し、fast-forwardできる場合だけ固定Worktreeを更新する。

## 2026-11-23 PCBレビュー候補版への更新

ユーザーが固定Workspaceの更新と未コミット変更の破棄を承認したため、対象の`a2_usb_uart.kicad_pro`だけを復元し、`workspace/a2-active`を`fffbcdbe41bad236baee48d88cf96b95f27421f4`から`a300e1c7cd89654fd2800c1bc7b8bad59dae5516`へfast-forwardした。更新後のプロジェクト・回路図・PCBは対象コミットと一致し、固定Worktreeに未コミット変更はない。

今回は明示された更新依頼に基づくレビュー用配置であり、PCBのOK判定ではない。main側のプロジェクト設定の未コミット変更、既存設計ブランチ、他Worktreeは保持した。設計成果物のmainへのマージと再生成は実施していない。
