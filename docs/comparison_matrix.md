# 設計手段と検証内容の組合せ

## 基本マトリクス

| 手段 | 内容A: 新規設計 | 内容B: KiCad既存設計の修正 |
| --- | --- | --- |
| 1. atopile + KiCad | **A-1 実施** | 対象外 |
| 2. KiCad | **A-2 実施** | **B-2 実施** |
| 3. EasyEDA Pro | **A-3 実施** | 対象外 |

**3手段・2内容・4ケース**を実施する。BはKiCadだけ。

## A: 共通設計仕様を3方式で検証

- 共通入力は `01_New_Design/specs/` で管理し、各方式で勝手に仕様を変えない。
- A-1: `01_New_Design/atopile/` — atopile→KiCad、Freerouting等
- A-2: `01_New_Design/kicad_direct/` — KiCad回路図とPCBをAIが直接編集
- A-3: `01_New_Design/easyeda/` — EasyEDA Pro回路図とPCBをAIが直接編集

主な記録項目: 仕様達成、部品選定、検証（ERC/DRC等）、作業時間、AI自動化率、手動修正、出力品質、環境依存、設計データの可読性。

## B-2: 既存KiCad設計の修正

- `02_Design_Modification/original/`に原本、`working/`に複製、`reports/`に差分と検証を保存。
- 修正前後の接続、部品・配線・ゾーン、保護対象の不変性と人間のレビュー容易性を重視。
- 元設計が外部公開不可の場合、公開GitHubにファイル・内部情報を置かない。

## 共通の条件

- ERC/DRC合格は動作保証ではない。
- 実行した作業と予定・仮説を明確に分けて記録する。
- 目的は実機比較。まずは環境構築、テスト回路選定と共通入力の確定から始める。
