# Codex初回セットアップ・実施指示（Windows 11）

この文書は実行指示です。**調査や手順提案だけで終わらず、可能な範囲でインストールとコマンド確認まで実行する。** 未実施項目は未実施として明記する。
インストール先は全て公式インストーラ・パッケージマネージャのデフォルト。勝手に独自ディレクトリへ入れ直さない。既存インストールを先に検出し、無用な再導入やアップグレードは行わない。

## 0. 共通ルールと前提知識（最初に必ず行う）

リポジトリルートを作業場所として、次を読んで内容を把握する（省略不可）。

1. `AGENTS.md`（プロジェクトの最優先作業規則）
2. `README.md`、`THIRD_PARTY_NOTICES.md`
3. `docs/discussion_log.md`、`docs/decision_log.md`、`docs/work_log.md`、`docs/report_outline.md`
4. `.agents/skills/pcb-pipeline/SKILL.md`（スキル本体）
5. `.agents/skills/pcb-pipeline/examples/Makefile`
6. `.agents/skills/pcb-pipeline/references/atopile.md`、`pcbnew.md`、`routing.md`、`design-rules.md`、`finish-config.md`、`fab/README.md`
7. `.agents/skills/pcb-pipeline/scripts/` の処理対象、Pythonモジュール依存、bash依存、CLI入出力を静的に確認する（この段階では実行しない）。

`docs/knowledge_baseline.md` を作成し、少なくとも (a) 2種類の実験の目的・違い、(b) スキルのデータフロー、(c) 各ツールの役割とバージョン、(d) 失敗しやすい条件（再生成・部品差替え・固定配線・DRC限界など）、(e) Windowsでの不明点、(f) 未決定事項 を**自分の言葉で**整理する。
設計や修正を勝手に開始しない。元スキルの仕様と今回のプロジェクト独自ルールを区別する。

## 1. ディレクトリ整備

既存の構造を維持し、以下のフォルダを用意する。既存ファイルは上書きしない。空フォルダのGit管理が必要なら `.gitkeep` を使う。

```text
AI_PCB_design_test/
├── AGENTS.md
├── README.md
├── THIRD_PARTY_NOTICES.md
├── .agents/skills/pcb-pipeline/    # 上流のSKILL.md、scripts、references、examplesを維持
├── docs/
│   ├── discussion_log.md
│   ├── decision_log.md
│   ├── work_log.md
│   ├── report_outline.md
│   ├── setup_plan.md
│   ├── knowledge_baseline.md       # Codexが新規作成
│   └── environment.md              # Codexが新規作成
├── 01_New_Design/
│   ├── specs/                      # 仕様書
│   ├── atopile/                    # 新規生成・atopile方式
│   ├── kicad_direct/               # KiCad直接編集方式（将来比較）
│   └── reports/                    # ERC/DRC、レビュー、成果記録
└── 02_Design_Modification/
    ├── original/                   # 原本保存・Git追跡禁止
    ├── working/                    # 作業コピー・Git追跡禁止
    └── reports/                    # 機密情報を除いた結果のみ
```

**公開リポジトリである。** 既存の会社・顧客・第三者の回路、製品情報、ネットリスト、設計ライブラリ等を許可なく公開・コミット・送信しない。特に `02_Design_Modification/original/` と `working/` はGitから除外し、Git以外のバックアップも維持する。ローカル環境のユーザー名・フルパス等も公開ログでは必要最小限にする。

## 2. Windows環境の事前調査

PowerShellで Windows版・CPUアーキテクチャ・権限・PATH、`winget`、`git`、`python`、`py`、`uv`、`java`、`jar`、`kicad-cli`、`ato`、`make`、`bash` を確認する。
現状と発見した実行ファイルの場所、バージョンを `docs/environment.md` に記録する。
利用可能なツールについては再インストールせず、**必要な版に合致するか**を確認する。

## 3. 必要なツールのインストール（主対象3種類）

| 主対象 | 固定バージョン/条件 | 依存 |
| --- | --- | --- |
| KiCad | 10.x（できれば最新の10.0.x安定版） | 公式Windows版、標準コンポーネント（ライブラリも含む） |
| atopile | **0.15.8**（上流スキルのCLI版） | uv / Python（uvが解決） |
| Freerouting | **2.1.0** の実行JAR | Eclipse Temurin **Java 21** |

### KiCad

公式 https://www.kicad.org/download/windows/ のWindows版10.xをデフォルトのインストール先へ導入。winget使用前に表示されるパッケージIDと利用可能な版を確認し、`KiCad.KiCad` の10.xを選択する。既に10.xがあれば原則流用する。既存の異なるメジャー版を消さない。
`kicad-cli version` を実行し、必要なら実行ファイルをインストール先から直接呼ぶ。標準フットプリントライブラリの存在も確認。
KiCadの`pcbnew` Python環境については、導入後に**実際のインストール先とPython互換性**を確認し、未確認のパスを決め打ちしない。

### atopile

`uv` が無ければ公式 https://docs.astral.sh/uv/getting-started/installation/ のWindows向け手順（例: `winget install -e --id astral-sh.uv`）で導入し、必要なら新しいシェルでPATHを再評価する。

```powershell
uv tool install "atopile==0.15.8"
ato --help
```

既存版があれば`uv tool list`等で確認する。0.16以降のWebアプリ版へ勝手に置き換えない。
Windowsネイティブでインストールできない場合はエラーログと原因を保存し、`WSL2` などの代替案を比較して報告する。ユーザー許可なくWSL2を有効化・再起動・OS構成変更しない。
`ato auth login` はブラウザ認証が必要である。ユーザーによる操作が必要な時点で案内し、**未認証でもインストール完了と動作確認完了を区別**する。認証情報をログへ保存しない。

### Freerouting

上流スキルが固定している **2.1.0** を使用する。先に `java -version` を確認し、Java 21 が無ければ https://adoptium.net/temurin/releases/?version=21 から標準インストール（wingetの `EclipseAdoptium.Temurin.21.JDK` が使用可能ならそれを利用）する。

上流スキルの実行形式はOS固有のインストーラではなく `freerouting-2.1.0.jar`。
GitHub公式リリース https://github.com/freerouting/freerouting/releases/tag/v2.1.0 のJARを取得し、上流の想定パスに相当するユーザーホーム `$HOME/tools/freerouting-2.1.0.jar` に保存（既存ファイルがあれば検証して流用）。取得元、サイズ、SHA256を記録する。
`java -version`、`jar tf <jar-path>` などでJavaとJARの健全性を確認する。JARのCLI引数は上流スクリプト `scripts/route.sh` のものを参照し、未確認引数を推測して実行しない。

## 4. 導入後のスモークテスト（設計はしない）

1. `kicad-cli version` で10.xを確認。KiCad実行ファイルと標準ライブラリのパスを記録。
2. `ato --help` / 利用可能なら`ato --version` を確認し、インストール版が0.15.8であることを記録。
3. `java -version` とJARの存在／構造確認を行う。Freerouting本体を実行できる場合はヘルプ等の**非破壊の**コマンドのみ。
4. KiCad Python `import pcbnew` の可否を**適合するPython実行環境**で確認する。Pythonバージョン不一致があれば記録し、既存Pythonを上書きしない。
5. `make`、`bash`、シェルスクリプトおよびDSN/SES変換のWindows実行可否を判定する。必要な追加依存があれば**列挙・説明**し、今回の3主ツール導入と区別する。
6. エラーは隠さず、動作OK・インストールのみOK・保留・失敗を区別する。

## 5. 成果物と終了条件

- `docs/knowledge_baseline.md`: エージェントが把握した前提知識。
- `docs/environment.md`: OS、インストール済みバージョン、配置パス、実行テストと検証結果（シークレットを記録しない）。
- `docs/work_log.md`: 今回の具体的な実作業とエラー、回避策を時系列追記。
- `docs/decision_log.md`: 手順やOS方針など、新たに決定したことがあれば追記。
- 必要なフォルダ構成を整え、`git status` で変更一覧を確認する。

**このタスクの対象はセットアップまで。** 回路・PCBの自動生成、既存データの変更、製造発注はまだ行わない。最後に「インストール完了／未完了」「Windowsネイティブで動く範囲」「今後の障害」「ユーザー操作が必要な事項」を簡潔に報告する。
