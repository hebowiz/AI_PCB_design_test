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

固定Worktreeは`codex/a2-r0035-usb-edge`の`ca191ab2a900714d53f7ab0eb8984b58f3af7ef8`を参照する。2026-11-25 22:14 JST、ユーザーの更新依頼によりR-0035のUSBコネクタ位置修正候補へ更新した。R-0035はユーザーOK。R-0034のOKと既存のレビュー判定は維持する。

CAD4ファイルとライブラリ・モデルを含む38ファイルのGit blob一致、ローカルモデル10ファイルの一致を確認した。58部品、配線・ビア計797個、6ゾーン、板厚1.6mm。J1原点は(111.000, 94.375)mm、J2モデルYオフセットは-0.7172mm。候補版のERC・DRC・未配線・回路図不一致は各0件で、今回の更新ではCADを再生成していない。画像と検証結果は固定Workspace内の`01_New_Design/kicad_direct/reports/usb_edge/README.md`を参照する。BOM・Gerber・実装座標は旧版のまま。

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

## 2026-11-24 PCB修正候補への更新

21:21 JST、`workspace/a2-active`を`a300e1c7cd89654fd2800c1bc7b8bad59dae5516`から`5596d3bc8802687b89b21fd9c57e1117ec9382e5`へfast-forwardした。更新前の未コミット変更はプロジェクト設定だけで、回路図・PCBに保存済み変更はなかった。

設定ファイルはローカルの`workspaces/_backups/A-2-20261124-212157/a2_usb_uart.kicad_pro`とGit stash `e51f0f6b9f3b540b1f42a1ec218900cfcf5a09a8`へ退避した。更新先の配線ルールを保持するため、旧設定は再適用していない。復元が必要な場合は内容を比較してから扱う。`.history/`内の7ファイルはハッシュ一致を確認した。

更新後のCAD4ファイルは対象コミットと一致し、追跡対象に未コミット変更はない。KiCadの回路図・PCBエディタは更新前に起動していなかった。mainの既存設定変更、他の設計ブランチ、レビュー判定は保持した。ローカルの更新記録はバックアップフォルダの`update_record.json`に保存した。

## 2026-11-24 PCB配線品質修正候補への更新

23:40 JST、`workspace/a2-active`を`5596d3bc8802687b89b21fd9c57e1117ec9382e5`から`87711e88e10653e79fdce9c3ade341b8f1440489`へfast-forwardした。未コミットのプロジェクト設定は`workspaces/_backups/A-2-20261124-234010/a2_usb_uart.kicad_pro`とGit stash `c8af3aafe7a6c3fa85550309751a95bdfcd29804`へ退避し、候補版の設定を使用する。旧設定は再適用していない。`.history/`は保持した。

更新後のCAD4ファイルは対象コミットと一致した。KiCad APIで部品58個、配線694本、ビア96個、ゾーン6個、板厚1.6mmを確認した。追跡対象に未コミット変更はない。mainの既存プロジェクト設定変更と既存設計ブランチは保護し、レビュー判定を変更していない。更新記録はバックアップフォルダの`update_record.json`に保存した。

## 2026-11-25 直角配線・電源デカップリング再修正候補への更新

01:03 JST、ユーザーの依頼により`workspace/a2-active`を`87711e88e10653e79fdce9c3ade341b8f1440489`から`22a74e75bdd508a28644a9df42fda8d10793d63e`へfast-forwardした。未コミットのプロジェクト設定は`workspaces/_backups/A-2-20261125-010305/`とstash `408b61b3c6f00e48c6caed48828bdcd8fe7d0eea`へ保存し、検証した候補版の設定を使用する。`.history/`7ファイル、mainの既存設定変更、既存設計ブランチを保持した。

更新後のCAD4ファイルは対象コミットと一致し、追跡対象に未コミット変更はない。PCB・回路図エディタは更新前に起動していなかった。ローカルの`update_record.json`にバックアップ・stash・ハッシュを記録した。R-0024・R-0027・R-0029の最終判定は未取得。

## 2026-11-25 20:40 JST — J2/J3修正と3D端合わせ候補への更新

ユーザーの「workspaceの更新をお願い。KiCADで確認したい」に従い、workspace/a2-activeを22a74e75bdd508a28644a9df42fda8d10793d63eから5cce544232e1f0eb137ef95f5060eeea5c9729efへfast-forwardした。追跡ファイルに未コミット変更はなく、.history/7ファイルのハッシュを保持した。PCB・回路図エディタは起動していなかった。

USBコネクタのローカル専用STEP2点もコピーし、元ファイル・移動先のハッシュと、元データの出典SHAを照合した。モデルはGit除外対象のまま。既存ファイルの破棄・強制上書きはしていない。更新後のCAD・ライブラリ・モデルのGit blobとPCBの読込を確認した。ローカル記録はworkspaces/_backups/A-2-20261125-203945/update_record.json。

mainの未コミットプロジェクト設定、既存設計ブランチ、レビュー判定は保持した。これは人間レビュー用の更新で、最終OKや製造承認ではない。

## 2026-11-25 22:14 JST — R-0035修正候補への更新

ユーザーの依頼により`workspace/a2-active`を`5cce544232e1f0eb137ef95f5060eeea5c9729ef`から`ca191ab2a900714d53f7ab0eb8984b58f3af7ef8`へfast-forwardした。未コミットのプロジェクト設定にはUSB差動ネットクラスやビア寸法の差分があったため、`workspaces/_backups/A-2-20261125-221454/a2_usb_uart.kicad_pro`とstash `9e7f5ac0edc1f10c5acc2637a4330d851e1d6414`へ退避した。候補版の検証済み設定を使用し、退避した設定は再適用していない。

回路図・PCBに保存済み変更はなく、更新前に両エディタの停止を確認した。`.history/`7ファイルとmainの既存プロジェクト設定はハッシュ一致で保全を確認した。更新後の追跡ファイルに未コミット変更はない。照合結果はバックアップフォルダの`update_record.json`に保存した。設計ブランチとmainのCADは変更していない。

## レビュー成果物の保存方式

新規レビューでは[固定保存方式](review_artifacts.md)を使う。設計ブランチ内の`reports/current/`が最終成果物の固定入口となる。現在のca191ab版は旧方式のまま保護し、今回の規則変更では固定Workspaceを更新しない。次回の設計作業から新方式へ移行する。過去フォルダの整理は別計画とする。

## 人間実演用とAI実践用の固定環境

2026-11-28 23:23 JST、最新の修正候補を両環境の共通出発点として作成した。基準は`codex/a2-pcb-network-reroute`の`3c53ed3ceecdad2ddc6d701d4913993f0e477bf3`、そのCADソースは`b16abc0023ffc0514cb936e0f7fcf6148b9ce9c1`。未解決箇所を含む実演用の基準であり、承認済み版への昇格ではない。

| 用途 | 固定フォルダ | 初期ローカルブランチ | 初期コミット |
| --- | --- | --- | --- |
| 従来のレビュー | `workspaces/A-2/` | `workspace/a2-active` | `ca191ab2a900714d53f7ab0eb8984b58f3af7ef8`を維持 |
| 人間の修正実演 | `workspaces/A-2-human/` | `workspace/a2-human` | `3c53ed3ceecdad2ddc6d701d4913993f0e477bf3` |
| Codexの修正実践 | `workspaces/A-2-ai/` | `workspace/a2-ai` | `3c53ed3ceecdad2ddc6d701d4913993f0e477bf3` |

人間が開くプロジェクトは次のファイル。

```text
D:/Documents/KiCad/10.0/projects/99_AI_PCB_design_test/workspaces/A-2-human/01_New_Design/kicad_direct/a2_usb_uart.kicad_pro
```

AI側は同じ相対パスを`workspaces/A-2-ai/`から参照する。両環境でmanifestの入力38ファイルのSHA256一致とGit差分なしを確認した。USBのローカル専用STEP2点も元データとハッシュ一致で配置し、Git除外を維持した。基板、回路図、製造データは再生成していない。従来のレビュー環境とmainの未コミット編集は保護した。

### 事例ごとの操作

人間は対象箇所をチャットで伝え、人間用プロジェクトを編集・保存し、判断理由と「実演完了」を知らせる。Gitの操作はCodexが担当する。保存中のファイルを確定版とせず、実演完了後に保存済み差分を確認する。別の編集が混在していれば、含める範囲を確認してからコミットする。

Codexは個別IDの受付時に共通修正前SHAを固定する。初回事例は上記の初期ブランチを使用できる。人間・AIそれぞれ原則1事例1設計コミットとし、ブランチを明示してpushする。実演のコミットは人間による編集と明記し、AI成果として扱わない。

次の事例で両者が異なる履歴になっている場合は、次の共通基準を確認する。保存済み変更をすべて保護し、編集を終えた状態で同一基準から`codex/a2-human-rNNNN`と`codex/a2-ai-rNNNN`等へ切り替える。固定フォルダは増やさず、以前の枝とコミットは残す。resetや強制切替で揃えない。ブランチ名が既存なら再利用可否を調べ、上書きしない。

AI実践の開始直前に、AI側CADが当該事例の修正前SHAと一致することを確認する。人間の修正済みCADやパッチをAI側へコピーしない。次事例の共通基準に過去の承認済み成果を採用する場合は、その選択を明記する。

比較成果物はAI側の`reports/current/`へ固定名で保存し、人間側の実演CADを書き換えない。管理文書・スキルはmainを正本とし、設計側へ取り込まない。従来の`A-2`への反映は、これまでどおり別途依頼・承認と保全確認を経て行う。
