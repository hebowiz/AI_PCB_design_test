# 基板プロジェクトの Makefile のひな形。プロジェクトの直下に置いて使う。
# .ato -> kicad_pcb -> Freerouting -> DRC -> ガーバー -> 発注ファイル
#
#   make build    ato build (部品選定, ERC) -> board/layouts/$(BUILD)/$(BUILD).kicad_pcb
#   make place    board/placement_$(BUILD).txt のとおりに部品を置く
#   make pre      層・取付穴・配線前の銅・固定配線・ファンアウト・禁止領域 (board/finish.py)
#   make unroute  ロックしていない配線と、配線後のベタを剥がす
#   make dsn      Specctra DSN を書き出す
#   make route    Freerouting (ヘッドレス) -> .ses
#   make ses      .ses を取り込む
#   make post     禁止領域を外し、ルータ出力を掃除し、ベタとステッチング (board/finish.py)
#   make routed   pre から post + DRC まで。未接続が残れば ROUTE_TRIES 回までやり直す
#   make labels   シルクの部品番号を部品に隠れない位置に置き直す
#   make drc      DRC (違反か未接続があれば失敗)
#   make check    部品の重なりと 3D モデル・実装属性の検査
#   make gerber   ガーバーとドリル。銅層は基板の層数から決まる
#   make fab      ガーバー zip, BOM, 実装座標 (FAB の書式)。all には含まない。部品を変えたら流し直す
#   make docs     ネット表 (docs/netlist.md)。回路図を描くなら SCHEMATIC を指定
#   make all      place から gerber まで
#   make fresh    レイアウトを退避して作り直す (部品を変えたら必要)
#   make clean    生成物 (out/) を消す
#
# 初回だけ `ato auth login` が要る (対話式)。

# スキルの場所 (SKILL.md のあるディレクトリ)。プラグインとして入れたなら
# ~/.claude/plugins/ や ~/.codex/plugins/ の下になる。エージェントが写すときは
# 自分の読み込み元の絶対パスを書く。書かなければ既定の置き場所を順に探す
SKILL      ?= $(firstword $(wildcard $(HOME)/.claude/skills/pcb-pipeline $(HOME)/.agents/skills/pcb-pipeline))
ifeq ($(SKILL),)
  $(error SKILL に pcb-pipeline の SKILL.md があるディレクトリを指定してください)
endif
S          := $(SKILL)/scripts

ATO        ?= $(HOME)/.local/bin/ato
KICAD_APP  ?= /Applications/KiCad/KiCad.app
KICAD_CLI  ?= $(shell command -v kicad-cli 2>/dev/null || echo $(KICAD_APP)/Contents/MacOS/kicad-cli)
KICAD_PY   := $(shell $(S)/kicad_python.sh)
BUILD      ?= default

PCB       := board/layouts/$(BUILD)/$(BUILD).kicad_pcb
BOM       := board/build/builds/$(BUILD)/$(BUILD).bom.csv
PLACEMENT := board/placement_$(BUILD).txt
FINISH    ?= board/finish.py
OUT       := out
DSN       := $(OUT)/$(BUILD).dsn
SES       := $(OUT)/$(BUILD).ses
PASSES    ?= 30

# 製造業者。scripts/fab_files.py の FABS にある名前 (jlcpcb, generic)
FAB         ?= jlcpcb
# 実装から外して手で付ける部品 (atopile のインスタンス名)
HAND_SOLDER ?=
# 回路図を描くスクリプト (examples/dcdc-4layer/draw_schematic.py を見本に書く)。空なら描かない
SCHEMATIC   ?=

.PHONY: all routed build place pre post labels unroute dsn route ses drc check gerber fab docs fresh clean
all: place routed labels drc gerber

# KiCad 10 が書いた基板を atopile は読めないので、ato build の前に整える
build:
	if [ -f $(PCB) ]; then python3 $(S)/sanitize_pcb.py $(PCB); fi
	cd board && $(ATO) build --build $(BUILD)
	python3 $(S)/prune_fp_lib_table.py board/layouts/$(BUILD)/fp-lib-table
	python3 $(S)/dedupe_uuids.py $(PCB)

# atopile は差し替えた部品にネットを載せないことがある。部品を変えたら作り直す
fresh: | $(OUT)
	if [ -f $(PCB) ]; then mv $(PCB) $(OUT)/$(BUILD)-previous.kicad_pcb; fi
	$(MAKE) build place pre

place:
	$(KICAD_PY) $(S)/place.py $(PCB) $(PLACEMENT)

pre:
	$(KICAD_PY) $(S)/finish_board.py $(PCB) pre $(FINISH)

post:
	$(KICAD_PY) $(S)/finish_board.py $(PCB) post $(FINISH)

$(OUT):
	mkdir -p $(OUT)

unroute:
	$(KICAD_PY) $(S)/unroute.py $(PCB)

dsn: | $(OUT)
	$(KICAD_PY) $(S)/export_dsn.py $(PCB) $(DSN)

# Freerouting は内層の面とベタで完結する接続も未配線に数える。本当の判定は DRC の未接続 0
ALLOW_UNROUTED ?= 0
route: | $(OUT)
	ALLOW_UNROUTED=$(ALLOW_UNROUTED) ROUTE_TIMEOUT=00:08:00 timeout 600 $(S)/route.sh $(DSN) $(SES) $(PASSES)

ses:
	$(KICAD_PY) $(S)/import_ses.py $(PCB) $(SES)

# Freerouting の結果は毎回違い、まれに数本を引き残す。DRC の未接続が 0 になるまで
# pre からやり直す
ROUTE_TRIES ?= 3
routed:
	@for i in $$(seq 1 $(ROUTE_TRIES)); do \
		echo "=== routing attempt $$i"; \
		$(MAKE) pre unroute dsn && ($(MAKE) route || true) && $(MAKE) ses post && $(MAKE) drc && exit 0; \
	done; echo "still unconnected after $(ROUTE_TRIES) attempts" >&2; exit 1

# 配線とベタには触らない。シルクと Fab だけ
labels:
	$(KICAD_PY) $(S)/place_labels.py $(PCB)

drc: | $(OUT)
	$(KICAD_CLI) pcb drc --severity-error --exit-code-violations \
		--format json -o $(OUT)/$(BUILD)-drc.json $(PCB)

check:
	$(KICAD_PY) $(S)/check_overlap.py $(PCB)
	$(KICAD_PY) $(S)/check_models.py $(PCB)

gerber: | $(OUT)
	rm -rf $(OUT)/gerber $(OUT)/$(BUILD)-gerber.zip
	mkdir -p $(OUT)/gerber
	$(KICAD_CLI) pcb export gerbers --no-protel-ext --layers $$(python3 $(S)/gerber_layers.py $(PCB)) \
		-o $(OUT)/gerber/ $(PCB)
	$(KICAD_CLI) pcb export drill --format excellon --excellon-separate-th -o $(OUT)/gerber/ $(PCB)
	cd $(OUT)/gerber && zip -q -r ../$(BUILD)-gerber.zip . && echo "packaged $(OUT)/$(BUILD)-gerber.zip"

fab: gerber
	mkdir -p $(OUT)/$(FAB)
	cp $(OUT)/$(BUILD)-gerber.zip $(OUT)/$(FAB)/gerber.zip
	$(KICAD_CLI) pcb export pos --format csv --units mm --side both \
		-o $(OUT)/$(BUILD).pos.csv $(PCB)
	python3 $(S)/fab_files.py $(FAB) $(OUT)/$(BUILD).pos.csv $(BOM) $(OUT)/$(FAB) \
		$(if $(HAND_SOLDER),$(PCB) $(HAND_SOLDER))

docs:
	mkdir -p docs
	$(KICAD_PY) $(S)/netlist_diagram.py $(PCB) docs/netlist.md $(BOM)
	$(if $(SCHEMATIC),SKILL_SCRIPTS=$(S) python3 $(SCHEMATIC) $(PCB) docs/netlist.md docs/schematic.svg)

clean:
	rm -rf $(OUT)
