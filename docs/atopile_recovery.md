# atopile 0.15.8のWindows隔離ビルド結果

2026-11-19、Intel Core i7-12700上でCPU baseline向けのネイティブモジュールを生成し、隔離環境のatopile 0.15.8の起動に成功した。既存のuv tool環境と配布バイナリは変更していない。通常のPATHで呼ぶ`ato`は従来の環境を指すため、今回の修復版を使う際は隔離環境の実行ファイルを指定する。

## ソースとビルド条件

ソースは[PyPIのatopile 0.15.8](https://pypi.org/project/atopile/0.15.8/)の`atopile-0.15.8.tar.gz`を使用した。SHA256は`76c42f33f151947dbe533d4d0a04b60623b84c38ced6e40d17c3099e5f59b955`で、PyPIのJSONメタデータと一致した。展開した通常ファイル1,352件もアーカイブと一致した。既存wheelとsdistのPythonファイル427件は、CRLF/LFの違いを除いて全件一致していた。

[Issue #1838](https://github.com/atopile/atopile/issues/1838)と[PR #1839](https://github.com/atopile/atopile/pull/1839)を確認した。PRは調査時点でもopen・未マージだった。PRの変更を取り込む必要はなく、0.15.8のsdistには既にCPU指定を受け取る処理があった。

`src/faebryk/core/zig/CMakeLists.txt`が環境変数`ATOPILE_ZIG_CPU`を`-Dcpu`へ渡し、`build.zig`の`standardTargetOptions`が両拡張モジュールのターゲットを設定する。CMakeの構成ログに`Zig CPU target: baseline`、生成した`pyzig.vcxproj`に`-Dcpu=baseline`を確認してからビルドした。

| 項目 | 使用条件 |
| --- | --- |
| OS・CPU | Windows 11 x64、Intel Core i7-12700。AVX2有効、AVX512F無効 |
| Python | CPython 3.14.10、通常のGILあり版、x64 |
| Zig | 0.16.0。sdistの`pyproject.toml`が指定する版 |
| 最適化・CPU | `ReleaseFast`、`baseline` |
| CMake | 既存の3.28.3-msvc11 |
| ジェネレータ | 既存のVisual Studio 17 2022、x64 |
| C/C++・SDK | MSVC 19.40.33812.0、Windows SDK 10.0.26100.0 |
| ビルド対象 | `pyzig`。Zig側の依存関係により`pyzig_sexp`と型定義も生成 |
| 実行環境の依存 | 既存環境のfreezeから同じ123パッケージを別環境へ導入。版の差分なし |
| バイナリ検査 | iced-x86 1.21.0、pefile 2024.8.26 |

通常のwheel生成ではhatchling、hatch-vcs、nanobindとatopileのscikit-build-coreフォークも要求される。今回はsdist内のCMakeを直接使ってネイティブ部分だけを生成したため、これらを追加せず、wheel全体の再パッケージ化も行っていない。ソースコードや上流スキルに修正は加えていない。

## 隔離した配置

次の領域はすべてGit除外の`.setup-local/atopile-rebuild/`配下にある。

| 相対パス | 用途 |
| --- | --- |
| `atopile-0.15.8/` | ハッシュ確認済みsdistの展開先 |
| `build-venv/` | Zigとバイナリ検査用のPython環境 |
| `runtime-venv/` | 既存と同じ依存版を持つCLI試験環境 |
| `cmake-build/` | CMake/MSBuildの生成物 |
| `native-output/` | ABI接尾辞を付けた修復版の2モジュール |
| `uv-cache/`、`zig-global-cache/` | この作業用のキャッシュ |
| `runtime-profile/`、`runtime-logs/` | 設定・データの参照先とログを隔離するための領域 |

実行試験用パッケージはuvの`--link-mode copy`で導入した。`runtime-venv/Lib/site-packages/atopile_cpu_baseline.pth`が`native-output/`を検索パスの先頭に追加する。既存環境と試験環境のどちらでも、配布された元の`*.pyd`は上書きしていない。実際のimport先が`native-output/`であることも確認した。

## 実行結果

| 検証 | 結果 |
| --- | --- |
| 元環境の`import pyzig` | 不正命令`0xc000001d`を再現。今回のfaulthandler付き子プロセスは終了コード3 |
| CMake構成 | 出力先を補った再試行で終了コード0 |
| ネイティブビルド | 終了コード0、約210秒、MSBuildの警告・エラーとも0 |
| CMake install | 隔離出力先への配置に成功、終了コード0 |
| 修復版の命令検査 | 両モジュールともbaseline超過命令・解読不能命令の検出0、検査終了コード0 |
| `import pyzig` | 終了コード0 |
| `import pyzig_sexp` | 終了コード0 |
| 隔離版`ato --version` | 終了コード0、`0.15.8`を表示 |
| 隔離版`ato --help` | 終了コード0、CLIのオプションとコマンド一覧を表示 |
| 設定参照先を隔離した`ato --help` | 終了コード0。platformdirsの設定・データ参照先も隔離領域と確認 |
| 元環境の保全 | uv tool登録・依存版に変化なし。元の2モジュール、uv、atoのSHA256が一致 |
| 他方式の保全 | KiCad CLI、Java 21、Freerouting JARのSHA256が導入済み記録と一致。EasyEDAは操作していない |

命令検査にはPR #1839のコミット`0a8d41363bb59338afd05905b8f6180685b5e335`にある検査ロジックを、内容確認後に使用した。wheelの代わりに2つのPEファイルを渡すローカルの補助スクリプトで、実行可能セクションを走査した。元のモジュールではAVX512F/VL/BW/DQ/FP16などを検出し、修復版では検出しなかった。これは静的検査と当該PCでの起動確認であり、全CPU・全設計処理の動作保証ではない。

| 生成物 | バイト数 | 走査命令数 | SHA256 |
| --- | ---: | ---: | --- |
| `pyzig.cp314-win_amd64.pyd` | 1,274,368 | 196,421 | `33fd77ff4369a366caf3520efde795ee13f41d75262e9a36de832a1f673c55e1` |
| `pyzig_sexp.cp314-win_amd64.pyd` | 5,767,680 | 1,063,799 | `125990a54d86b630ad669a29ef8215204552de44954289a643992a474eb60c66` |

両ファイルはPE x86_64形式で、`python314.dll`を参照する。エクスポートされた初期化関数はそれぞれ`PyInit_pyzig`と`PyInit_pyzig_sexp`だった。Python 3.11やfree-threaded版へ流用しない。

## 実行した主要ビルドコマンド

以下はソース展開と仮想環境の準備後に使った条件を示す。`$rebuildCmake`には既存Visual Studio Build Tools付属の`cmake.exe`を指定した。各コマンドの出力・終了コードはローカルへ保存した。

```powershell
$rebuildRoot = (Resolve-Path .setup-local/atopile-rebuild).Path
$env:ATOPILE_ZIG_CPU = 'baseline'
$env:ZIG_GLOBAL_CACHE_DIR = "$rebuildRoot/zig-global-cache"
& $rebuildCmake -S "$rebuildRoot/atopile-0.15.8/src/faebryk/core" `
  -B "$rebuildRoot/cmake-build" -G 'Visual Studio 17 2022' -A x64 `
  "-DPython3_EXECUTABLE=$rebuildRoot/build-venv/Scripts/python.exe" `
  "-DSKBUILD_PLATLIB_DIR=$rebuildRoot/native-output"
& $rebuildCmake --build "$rebuildRoot/cmake-build" --config Release --target pyzig --verbose
& $rebuildCmake --install "$rebuildRoot/cmake-build" --config Release
```

## 隔離版の使い方と復旧方法

リポジトリルートから、次のように隔離版を指定できる。環境変数はそのPowerShellプロセス内だけに設定する。platformdirsの設定・データ参照先とログを隔離し、試験ではテレメトリを無効にした。認証や設計処理はまだ実行していない。

```powershell
$rebuildRoot = (Resolve-Path .setup-local/atopile-rebuild).Path
$env:WIN_PD_OVERRIDE_LOCAL_APPDATA = "$rebuildRoot/runtime-profile/Local"
$env:WIN_PD_OVERRIDE_APPDATA = "$rebuildRoot/runtime-profile/Roaming"
$env:FBRK_LOG_DIR = "$rebuildRoot/runtime-logs"
$env:FBRK_TELEMETRY = 'false'
& "$rebuildRoot/runtime-venv/Scripts/ato.exe" --version
& "$rebuildRoot/runtime-venv/Scripts/ato.exe" --help
```

次の最短経路は、この隔離版を明示してA-1の後続検証に使う方法である。通常環境の`ato`は変更していないため、隔離版の利用を止めれば元の構成に戻る。今回の環境変数を設定したPowerShellを終了すれば、その指定も残らない。隔離環境の読み込み変更を戻す場合は、`atopile_cpu_baseline.pth`だけを無効化すれば元の配布モジュールが選ばれる。ただし、このPCでは元の起動障害も再発する。

通常のuv tool環境へ修復版を取り込むかは未決定である。移行する場合の対象は、その環境の`Lib/site-packages`に置く専用の`.pth`と、管理先を固定した修復版2ファイルである。元の配布ファイルを保存したまま読み込み先を切り替え、移行先で同じ4項目の起動確認を行う。復旧時は追加した`.pth`を無効化する。現状の`.pth`にはローカルの絶対パスがあるため、フォルダ移動時には更新が必要となる。uvによる再導入・更新後も再確認が必要で、この移行は今回実施していない。

## 発生した問題と未検証事項

Windowsのtarは、AGENTS.mdとUI画像3件のシンボリックリンク作成に失敗した。通常ファイルの欠落はなく、AGENTS.mdの参照先CLAUDE.mdも読んだ。今回のネイティブビルドには影響しなかったが、配布アーカイブ全体を完全展開できたとは扱わない。

CMakeを直接呼んだ初回は、wheelビルド時に設定される`SKBUILD_PLATLIB_DIR`がなく、`install FILES given no DESTINATION`となった。隔離出力先を明示して解消した。uvの依存一覧取得でも、既定キャッシュへのサンドボックスアクセス拒否が一度あった。作業用の`UV_CACHE_DIR`を指定して再実行した。

回路・PCBの作成、`ato build`、認証、部品選定、ネットワークサービスとの連携は未実施である。GNU make/zip/librsvg不足とFreeroutingの設定参照先も今回の修復対象には含めない。起動障害はWindowsネイティブで解消できたため、本件のためにWSL2を有効化する必要はなく、OS機能・再起動・既存ツールの削除や版変更は行っていない。

生ログ、ソース、依存一覧、バイナリ、元環境のハッシュ一覧はGit除外領域に保存した。公開リポジトリに含めるのは本書と共通ログの要約だけである。
