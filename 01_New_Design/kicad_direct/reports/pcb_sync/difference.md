# 回路図と旧PCBの差分、および反映結果

比較基準は承認済みコミット`fffbcdbe41bad236baee48d88cf96b95f27421f4`の回路図と、そのコミットに残っていた旧PCB。部品・端子の全差分は[JSON](schematic_pcb_difference.json)、反映後の全端子検証と配線UUID差分は[integrity.json](integrity.json)に保存した。

## 部品差分

|参照番号|区分|旧PCB → 承認済み回路図・同期後PCB|
|---|---|---|
|C1|変更|value: 1u → 4.7u; footprint: A2:C_0402_1005Metric → Capacitor_SMD:C_0805_2012Metric|
|C11|変更|value: 1u → 4.7u; footprint: A2:C_0402_1005Metric → Capacitor_SMD:C_0805_2012Metric|
|C12|変更|value: 1u → 4.7u; footprint: A2:C_0402_1005Metric → Capacitor_SMD:C_0805_2012Metric|
|C13|変更|value: 27p → 15p 1%|
|C14|変更|value: 27p → 15p 1%|
|C2|変更|value: 2.2u → 4.7u; footprint: A2:C_0603_1608Metric → Capacitor_SMD:C_0805_2012Metric|
|C20|削除|1u / A2:C_0402_1005Metric|
|C21|削除|1u / A2:C_0402_1005Metric|
|C23|追加|100n / A2:C_0402_1005Metric|
|D1|変更|value: TPD2EUSB30 → ESD321DPYR; footprint: A2:Texas_DRT-3 → Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm|
|D5|追加|ESD321DPYR / Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm|
|R16|削除|100 / A2:R_0402_1005Metric|
|R17|追加|0R / 0603 / A2:R_0603_Bourns_CRPF|
|TP1|追加|D1.5mm / A2:TestPoint_Pad_D1.5mm|
|TP2|追加|D1.5mm / A2:TestPoint_Pad_D1.5mm|
|U3|削除|AP2112K-3.3 / A2:SOT-23-5|
|U6|削除|TPS22919DCK / A2:SOT-363_SC-70-6|
|Y1|変更|value: 12MHz 18pF → 12MHz 12pF|

Y1のMPNは`ABM8-12.000MHZ-12-B1U-T`、C13/C14は15pF・1%の承認済み属性を反映した。C11/C12はDNPを維持。全58部品でValue・Footprint・MPN・Note・DNPと全端子の接続を照合した。TP1/TP2のBOM除外属性も反映している。部品表の出力ファイルは更新していない。

## ネット差分

電源名の先頭`/`削除は、ローカルラベルから電源シンボルへの変更に伴う名称更新。`GND`、`USB5V`、`+3V3`、`VIO`、`VIO_OUT`、`USB5V_OUT`、`VPHY`、`VPLL`、`VCCA_1V8`、`VCORE_1V8`が該当する。スイッチ未接続ネットの`{slash}`と`/`はKiCadのエスケープ差として照合した。

端子を持つネットは旧PCBの58から55になった。名称の表記差を正規化した後の増減を次に示す。

|区分|ネット|処理|
|---|---|---|
|追加|`/USB5V_SW`|SW2出力とR17入力・TP1を接続|
|削除|`/USB5V_ENABLED`|U6削除に伴い残る配電をUSB5Vへ統合|
|削除|`/QOD`|U6/R16削除に伴う消滅|
|削除|`unconnected-(U3-NC-Pad4)`|U3削除に伴う消滅|
|削除|`unconnected-(U6-NC-Pad4)`|U6削除に伴う消滅|

既存部品の意味のある端子変更は次のとおり。D1.3は3端子保護アレイから2端子品への置換で消滅したパッドであり、未接続化ではない。

|端子|旧PCBネット|同期後ネット|
|---|---|---|
|D1.2|`/USB_D-`|`GND`|
|D1.3|`/GND`|パッド削除|
|SW2.2|`/USB5V_OUT`|`/USB5V_SW`|
|SW2.3|`/USB5V_ENABLED`|`USB5V`|
|U1.40|`/+3V3`|`USB5V`|

U3削除に伴いU1.40をUSB5Vへ接続し、U1.39のVCCDと既存+3V3配電を保持。U6/R16削除に伴い`/USB5V_ENABLED`側をUSB5Vへ接続し、`/QOD`を削除した。`/PWR_EN`はU1側の端子ネットを保持し、旧U6へ伸びていた行き止まり配線を除去した。

新設`/USB5V_SW`はSW2.2・R17.1・TP1.1、`USB5V_OUT`はR17.2・TP2.1・J2.4を接続する。C23はUSB5V–GND間。D1はUSB_D+–GND、D5はUSB_D−–GNDへ接続した。

## 配置・配線の差分

既存部品の中心または角度を変更したのは次の5部品。座標はKiCad基板座標のmm。

|部品|変更前 座標 / 角度|変更後 座標 / 角度|
|---|---|---|
|C1|[116.3, 105.8] / 90.0°|[118.9, 108.5] / 180.0°|
|C11|[108.0, 106.8] / 0.0°|[103.9, 106.0] / 90.0°|
|C12|[120.5, 112.3] / 90.0°|[108.7, 107.3] / 180.0°|
|C2|[118.5, 111.5] / 0.0°|[118.2, 111.5] / 0.0°|
|D1|[111.0, 107.5] / 0.0°|[110.9, 107.5] / 90.0°|

新設部品の座標は[local_placement.json](local_placement.json)に保存。USBコネクタJ1、外部ヘッダJ2/J3、SW1/SW2/SW3の位置・角度は変更していない。0805へ大型化したC1/C2/C11/C12と小型化したD1の周辺を局所修正した。C11/C12はDNPのまま、コートヤードの干渉を避ける位置へ移した。

配線・ビアは旧1088オブジェクト中1022をUUID・形状とも保持した。66を削除し145を追加、最終1167。保持した93.93%はオブジェクト数の割合であり、配線長の割合ではない。削除・追加の全座標、層、太さ、ネット、UUIDは[integrity.json](integrity.json)にある。旧U3/U6の不要枝と交換パッド付近の干渉配線を対象に除去し、DRCで未接続とされた端点間だけを追加配線した。

GNDゾーンの輪郭・層・クリアランス・最小厚とUUIDを維持して再充填。外形線のUUIDと幾何形状も不変。部品・配線に合わせた銅箔充填の変化は意図した差分である。
