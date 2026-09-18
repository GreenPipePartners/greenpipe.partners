# WashHeat Automation — Revision O

**Hanwha · 12001-HAN-WashHeat Automation · Engineering report · 18 September 2026**

This web edition includes prebuilt light/dark PLC drawings, supporting diagrams and Perspective screen captures. Use the website theme control to change menus, images and legends together.

[PLC logic](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html) · [Supporting resources](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/resources.html) · [Perspective screens](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/screens.html)

### Downloadable delivery

- [Complete portable Obsidian report and editable drawings](https://github.com/GreenPipePartners/greenpipe.partners/releases/download/hanwha-washheat-rev-o-2026-09-18/12001-HAN-WashHeat-Obsidian.zip).
- [Studio-check evidence and offline reference package](https://github.com/GreenPipePartners/greenpipe.partners/releases/download/hanwha-washheat-rev-o-2026-09-18/12001-HAN-WashHeat-Studio-Checks-2026-09-18.zip).
- [Standalone light/dark web viewers](https://github.com/GreenPipePartners/greenpipe.partners/releases/download/hanwha-washheat-rev-o-2026-09-18/12001-HAN-WashHeat-Web-Logic-Viewer.zip).
- [Download checksums](https://github.com/GreenPipePartners/greenpipe.partners/releases/download/hanwha-washheat-rev-o-2026-09-18/SHA256SUMS.txt).

**Studio-verified corrections, manual updates to the current live press programs, selectable CDL 1 / CDL 2, and the barcode-keyed part catalogue.**

Revision O incorporates the 18 September Studio verification findings into the main report, corrected source listings and refreshed native drawings. It documents manual implementation of both press changes on the current live programs. The eight requested deliverables remain covered. PLC additions are native ladder. The report and editable drawings are arranged by **Presses / CDLs / FDC**. Timing supports the operator’s stopwatch: press observations use FDC arrival time with an accepted **±1-second normal-operation uncertainty**.

## 1. Deliverables, revision changes and source selection

**Both press changes will be made manually to the current live programs.** The live 50 MN and 300 MN projects are the implementation baselines. Recovered/converted whole-press files in this report are offline reference and verification evidence, not replacement projects for download. Manual implementation is pending. See [Press manual-update instructions](Press-Manual-Update.md) and section 9.

| Controller | Recovered source / revision | Checked / offline-reference derivative |
|---|---|---|
| P50 / P5000 | P50_ORIGINAL_NATIVE_v19.L5X | P5000_10_09_2025_WH_DEV_v19.L5X |
| P300 / P33000_Controller | P300MN_L84E_030726.L5X | P300MN_L84E_030726_WH_DEV_v37.L5X |
| CDL1 / EN01_80A3_CPU | PA166_Howmett_C4010_260723.L5X | PA166_Howmett_C4010_260723_WH_DEV_v36.L5X |
| CDL2 / Firth_Rixson_PA209 | CDL2_180912.L5X | CDL2_180912_WH_DEV_v37.L5X |
| CDL / PA166_FIRTH_RIXSON | PA166_20422RDN.L5X | PA166_20422RDN_WH_DEV_v37.L5X |
| FDC / FGGW01CLX | FDC20206_V20_03_07_26.L5X | FDC20206_V20_03_07_26_WH_DEV_v37.L5X |


- **50 MN reference:** corrected to the original **1789-L60 SoftLogix / 19.11**, exported with RSLogix 5000 v19.01. Its 11 modules and seven external-routine entries are retained. The earlier v37/L75 conversion is superseded and excluded from the current source/drawing set.
- **300 MN reference:** 1756-L84E / 37.11. Registered MTS device descriptions retain all four cylinder modules and existing message paths in the checked offline copy.
- **CDL 1:** supplied `PA166_Howmett_C4010_260723.ACD`, **5069-L310ERMS3 / 36.14**. Code-only overlay on the original native ACD preserves hardware and safety definitions; full-L5X re-import still depends on the workstation chassis/profile configuration.
- **CDL 2:** PA209 / `Firth_Rixson_PA209`, v37. Native conversion plus code-only overlay preserves module data and original task scheduling. `PA166_20422RDN` remains an optional legacy CDL 1 compatibility reference. Use one CDL adapter at a time.
- **Generated v36/v37 instructions:** canonical `MOVE`, `EQ`, `NE`, `LT`, `LE`, `GT`, `GE` spellings are reflected in the current drawings and source ledgers. The native v19 press reference retains its version-appropriate spellings.
- [Ignition import ZIP](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/Implementation/WashHeat-Ignition.zip) · [Current drawing/build manifest](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/build-manifest.json) · [Source receipts](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/source-receipts.json) · [Recorded Studio evidence](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/Verification/Studio-2026-09-18/Evidence/index.html).

## 2. Common CDL interface and simplified messages

### Presses

**Implementation: manual merge into each current live press program.** The five-rung reference changes, initialization values and execution order are documented in [Press manual-update instructions](Press-Manual-Update.md).

Both press arrays remain **DINT[4]**. Existing press→FDC MSG instructions still transfer words **[2..3], two DINTs / eight bytes**. Word [2] retains original status and heartbeat ownership. The only new transferred value is a persistent **Cycle Start counter in [3]**. First scan initializes its baseline; subsequent edges increment, with a bounded wrap to 1. The existing FDC→press [0..1] transfer remains intact.

FDC detects a counter change and captures `WALLCLOCKTIME.DateTime` on arrival. Heartbeat transitions qualify communication freshness. A reset/skipped counter is a discontinuity, and a three-second communication age invalidates the link. Reconnection establishes a baseline instead of replaying an old event.

A **one-second cycle-publication grace period** allows an operator decision to be captured first. The original arrival timestamp stays in the record. An arrival observation within ±1000 ms of an explicit wash decision retains that decision and is stored as an advisory observation. A larger conflict requires review; it is not proof of physical event order.

### CDLs

Existing `UD_Robot_to_DataCollector` and `UD_DataCollector_to_Robot` types gain one trailing `WashHeat` member at both endpoints. Original members, values, message tags, paths and requested structure count are retained. The write extension is **17 DINTs / 68 bytes**; the read extension is **11 DINTs / 44 bytes**. The appended write payload refreshes while the original MSG is idle and is held while `.EN` is set. Actual updates follow the existing roughly 500 ms message cadence.

| Adapter | Start observation | Raw stop observation | Normalized source |
|---|---|---|---|
| CDL 1 / supplied PA166 | Original `ExternalComms/Transfer_Timer` running latch, original rung 006 | Original release predicate, rung 011; `Stations[3/4].Status.AtStation` | `SourceId=1`, `ctrl_CDL_DC.WashHeat` |
| CDL 2 / PA209 | Inside RF01 or RF02 with a clamped part, then both inside flags clear on withdrawal | Gripper open at `ROBOT_AT.BigPress` or `.SmallPress` | `SourceId=2`, `ctrl_CDL2_DC.WashHeat` |
| Optional legacy CDL 1 | Original `Automatic_Cycle/Transfer_Timer`, rung 005 | Original rung 010 | `SourceId=1`, same CDL 1 contract |

PA209 has no original transfer timer. The adapter observes its existing `ROBOT_IN.Furnace1/2` spatial boundary (extension >2000). The original automatic withdrawal retracts to 1800 at state 140 before progressing at 145. The single-furnace manual `Part_In_Transit` expression is not used as the removal trigger.

`WH_ActiveCDL` is an explicit FDC selection: **0 unconfigured, 1 CDL 1, 2 CDL 2**. Idle selection establishes a fresh baseline. A change during a handled part latches site fault 36. Separate receive mailboxes normalize to `WH_Link[0]`; return displays carry `TargetCdl`. Each emitted physical event retains `CdlId` and the selected 50/300 MN press.

The raw gripper-release stopwatch and independent transfer elapsed timer are distinct. The independent timer continues after release. `WH_TransferPopup` follows only a fresh, selected, active, valid, over-limit display. This is an advisory visibility tag; existing FactoryTalk display integration remains a commissioning item. PA166 also retains its raw release-event mailbox for optional direct Gateway archival; PA209 exposes raw release time through the common message.

### Field-by-field message drawings

Every visible UDT member, including nested original machine fields and the WashHeat extension, is listed source→meaning→destination. Press word shapes and the barcode translation have their own frames.

**Supporting-resource viewer — Database schema, Message translation and Calculation flow.** Select a resource in the table; expand its title for the legend and source details.

<iframe src="https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/resources.html" title="WashHeat Revision O — supporting resources"></iframe>

[Open Message translation](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/resources.html#logic-washheat-resources-rev-o/message-translations)

[Editable translations](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/editable/washheat-message-translations-rev-o.excalidraw) · [Message configurations and field register](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/message-translations.json).

## 3. Photographed barcode and dimension key

The smaller barcode decodes to **`FCBHAH05`**. The larger PDF417 decodes to:

```text
FCBHAH05,P/024236,00213,22G0436-01,NCR36941-HFF2,1690,25,340,654,22G0436-01-F1-02,22G0436-01-FF
```

| Index | Photographed value | Meaning | Original furnace item | Catalogue / runtime field |
|---|---|---|---|---|
| 0 | FCBHAH05 | Serial | strSN | serial_number |
| 1 | P/024236 | Work order | strWO | work_order |
| 2 | 00213 | Stage | strStg | stage |
| 3 | 22G0436-01 | Part number | strPN | part_number |
| 4 | NCR36941-HFF2 | Heat specification | strQA | qa_spec |
| 5 | 1690 | Barcode temperature | strBarCodeTemperature | temperature_sp |
| 6 | 25 | Temperature tolerance | strTolerance | temperature_tolerance |
| 7 | 340 | Minimum soak (minutes) | strSoak | min_soak_minutes |
| 8 | 654 | Maximum soak (minutes) | strMaxSoak | max_soak_minutes |
| 9 | 22G0436-01-F1-02 | Press recipe | strRecipe | press_recipe |
| 10 | 22G0436-01-FF | Press quality | strPressQA | press_qa |


The source `funcParseBarCodeData` splits eleven comma-delimited fields; `funcProcessFurnaceItem` retains them in the original item. The scanned temperature is stored in `strBarCodeTemperature`; the loaded item's active `TemperatureSP` comes from the furnace setpoint. `strSoak` / `strMaxSoak` preserve the minute strings and are converted into `MinSoak` / `MaxSoak`. **The ticket contains no dimensions.** Dimension resolution uses the exact composite:

```text
(part_number, stage, qa_spec, press_recipe, press_qa)
```

`strQA` is the heat specification; `strPressQA` is press quality. `strRecipe` identifies the press operation. Leading zeros, case and distinct operation/specification values are preserved; there is no QA-only fallback. `Recipe` and `PressQA` are now included in all frozen PLC/Gateway part identities along with serial, work order, part, stage, heat QA and the original seven-field load stamp.

## 4. Ignition screens and data entry

The native Perspective project provides three routes, borrowing the customer reference’s charcoal canvas, dark panels, orange **#F37321** accents, pale text and left navigation.

| Page | Route | Purpose |
|---|---|---|
| Part Status | `/` | Persisted run table: serial, part, stage, recipe, furnace/position, CDL/press, wash status, measured remaining time, dimensions and catalogue revision; select a row for decision controls |
| Part Data | `/parts` | Search existing operations, load keys from the photographed-style process barcode, enter measured dimensions and optional FM20 timing inputs, add/edit, deactivate and review revision history |
| Calculations / Records | `/tools` | Formula preview, FM20 limit entry, explicit simulated demonstrations and generated Tropos review records |

Saving part data and recording decisions require an authenticated actor. Project Properties selects the `default` Identity Provider; choose the site's provider during installation. Keys are immutable on edit: another operation uses **New Entry**. OD and height must be positive, the inscribed circle is optional, and values must fit decimal(18,6) without rounding. FM20 inputs must be either all present or all blank; the resulting limit must be exactly representable in milliseconds.

Enrollment resolves the exact captured identity, freezes dimensions/timing inputs and catalogue revision, and records the actor. The original load UTC is entered explicitly because the original PLC load stamp is retained as identity rather than assumed to be UTC. Catalogue edits never rewrite enrolled-run dimensions.

The browser checks exercise actual Perspective → Jython → SQL actions. Parts rows resolve all five immutable keys to the complete current SQL record; Part Status supplies a stable column schema for older runs and binds the clicked run ID.


**Perspective screen viewer — Part Status, Part Data and Calculations / Records.** The menu also includes barcode-entry, saved-dimension and revision-history captures. The light images are color-adapted report previews of the native captures; View JSON opens the exact released Perspective definition.

<iframe src="https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/screens.html" title="WashHeat Revision O — Perspective screens"></iframe>

All screenshots show identified synthetic lab records. [Browser checks and screenshots](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/UIReview/index.html) · [Deployed-file and SQL evidence](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/Verification/Gateway/index.html).

## 5. Calculation and persistence

FM497 uses D10 OD, **D16 height**, optional D30 inscribed circle and cumulative out-of-furnace time. The smallest applicable candidate is subject to the 45-minute minimum; cumulative out time strictly greater than 300 seconds produces a full-reheat requirement. Repeated wash episodes retain cumulative time and the original qualifying-soak budget. PLC elapsed samples, not Gateway wall-time extrapolation, drive observed reheat remaining time.

FM20 maximum Cycle Start time is **maximum transfer + DH Cycle Start elapsed − DH Tonnage elapsed − 3 seconds**. DH Tonnage is an elapsed time input, not a force value.

[Open Calculation flow in the resource viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/resources.html#logic-washheat-resources-rev-o/calculation-flow)

Migration 003 adds `part_recipe`, `part_recipe_revision`, and `run_recipe` to the existing eight tables. The exact five-column lookup uses binary collation. Save/history insertion share one SQL transaction and optimistic revision checks. `run_recipe` references the original immutable catalogue revision. The existing run snapshot remains the source of dimensions for that run. Tropos output remains an explicit review record with submission state `NOT_SENT`.

[Open Database schema in the resource viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/resources.html#logic-washheat-resources-rev-o/database-schema)

## 6. Studio verification and implementation status

The actual **Logic → Verify → Controller** command was run on WIN_L_VM for all six offline copies. SDK `build()` is a separate operation and did not detect the obsolete mnemonic errors. The canonical mnemonic corrections, native CDL overlays and MTS device-description registration were applied before the final checks.

| Project | Controller revision | Errors | Warnings | Baseline errors / warnings | Implementation |
|---|---:|---:|---:|---:|---|
| FDC | 37.11 | 0 | 209 | 0 / 17 | Checked native ACD / source-backed changes |
| CDL 1 | 36.14 | 0 | 7 | 0 / 5 | Checked native ACD / source-backed changes |
| CDL 2 | 37.11 | 0 | 7 | 0 / 7 | Checked native ACD / source-backed changes |
| 300 MN | 37.11 | 0 | 79 | 0 / 79 | Manual update of current live program; offline copy is reference only |
| 50 MN — native SoftLogix | 19.11 | 17 | 22 | 17 / 22 | Manual update of current live program; offline copy is reference only |
| Optional legacy CDL | 37.11 | 0 | 34 | 0 / 32 | Checked native ACD / source-backed changes |

The five zero-error results cover FDC, both operational CDLs, 300 MN and the optional legacy CDL. The native 50 MN reference retains exactly the original 17 errors: seven invalid external component specifications and ten associated `JXR` parameter errors. Its five WashHeat rungs add no errors. The selected press implementation route is a **manual merge into the current live program**, using that program's existing hardware and external components; these offline findings do not claim that a live press change has already been completed.

FDC adds 192 deliberate duplicate AOI-instance warnings for paired Pre/Post calls; its other 17 warnings are inherited. CDL 1 and optional legacy CDL each add two first-scan/cyclic-writer warnings. CDL 2, 300 MN and 50 MN warning counts match their baselines. The optional legacy conversion also retains baseline warnings for removed ASCII/DF1/SerialPort components. [Full diagnostics, hashes and screenshots](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/Verification/Studio-2026-09-18/Evidence/final-verification-summary.json).

**55 PLC and 71 application offline checks passed** after the mnemonic repair. Existing release evidence also records **10 Ignition/Jython/SQL catalogue checks and 15 browser checks**. The Ignition ZIP is unchanged: all 23 deployed release files matched its manifest, with the five existing `FM300_Form_83` files preserved. Native round-trip audits cover source data, message parameters, module definitions, scheduling, safety metadata and executable content; the native 50 MN builder proves its original components are retained.

Live PLC communication and manual press implementation remain pending. The Gateway adapter is packaged disabled (`ENABLED=False`, empty device/slot configuration), FDC installation words and clock validation require commissioning, and CDL selection defaults to unconfigured. No controller download or online edit was performed.

The lab contains identified synthetic catalogue entries, deactivated after verification; production dimensions were not inferred from the barcode.

## 7. Application hierarchy and full native ladder

| Measure | Count |
|---|---|
| controllers | 6 |
| new_components | 344 |
| new_program_routines | 30 |
| new_aoi_definitions | 1 |
| new_udt_definitions | 19 |
| new_udt_members | 223 |
| new_tags | 292 |
| modified_original_routines | 8 |
| modified_routine_rungs_total | 170 |
| added_hook_rungs | 25 |
| dispatch_rungs | 384 |
| st_lines | 0 |
| st_routines | 0 |
| aoi_parameters | 16 |
| aoi_local_tags | 27 |
| existing_nonempty_type_dependencies | 6 |


**Open the editable PLC drawings:** [Presses](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/editable/washheat-plc-presses-rev-o.excalidraw) · [CDLs](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/editable/washheat-plc-cdls-rev-o.excalidraw) · [FDC](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/editable/washheat-plc-fdc-rev-o.excalidraw)

The three separate PLC drawings contain **39 routine frames and 903 source rungs**. Original source variables are blue, state operands/values yellow, fault fields/nonzero codes red, and mapping sections carry MAP gutter labels. AOI operands are shown by parameter name. Indexed condensation is permitted only for sequences of five or more; complete occurrence and continuity ledgers retain all source coverage.

**Logic viewer — FDC / Presses / CDLs.** Select a new or modified routine from the application hierarchy. Use the rung selector, zoom and full-screen controls for long drawings.

<iframe src="https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html" title="WashHeat Revision O — PLC logic"></iframe>

[Complete application-hierarchy SVG](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/application-hierarchy.svg)

### Presses

#### P50 / WH_Signals/WH_SendSignals

**Manual implementation reference — apply to the current live press program.**

5 source rungs; 5 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/p50-wh-signals-wh-sendsignals)

#### P300 / WH_Signals/WH_SendSignals

**Manual implementation reference — apply to the current live press program.**

5 source rungs; 5 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/p300-wh-signals-wh-sendsignals)

### CDLs

#### CDL1 / ExternalComms/CDL_DC

17 source rungs; 2 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl1-externalcomms-cdl-dc)

#### CDL1 / ExternalComms/Transfer_Timer

24 source rungs; 15 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl1-externalcomms-transfer-timer)

#### CDL1 / ExternalComms/WH_CDL_Begin

8 source rungs; 8 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl1-externalcomms-wh-cdl-begin)

#### CDL1 / ExternalComms/WH_CDL_End

4 source rungs; 4 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl1-externalcomms-wh-cdl-end)

#### CDL1 / ExternalComms/WH_CDL_Init

5 source rungs; 5 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl1-externalcomms-wh-cdl-init)

#### CDL1 / ExternalComms/WH_CDL_Start

2 source rungs; 2 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl1-externalcomms-wh-cdl-start)

#### CDL1 / ExternalComms/WH_CDL_Stop

12 source rungs; 12 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl1-externalcomms-wh-cdl-stop)

#### CDL1 / ExternalComms/WH_PackMessage

4 source rungs; 4 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl1-externalcomms-wh-packmessage)

#### CDL1 / ExternalComms/WH_ReceiveDisplay

5 source rungs; 5 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl1-externalcomms-wh-receivedisplay)

#### CDL1 / ExternalComms/WH_SendSignals

16 source rungs; 16 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl1-externalcomms-wh-sendsignals)

#### CDL2 / ExternalPLC/ToDataCollector

28 source rungs; 3 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl2-externalplc-todatacollector)

#### CDL2 / ExternalPLC/WH_Adapter

11 source rungs; 11 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl2-externalplc-wh-adapter)

#### CDL2 / ExternalPLC/WH_PackMessage

4 source rungs; 4 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl2-externalplc-wh-packmessage)

#### CDL2 / ExternalPLC/WH_ReceiveDisplay

5 source rungs; 5 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl2-externalplc-wh-receivedisplay)

#### CDL2 / ExternalPLC/WH_SendSignals

16 source rungs; 16 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl2-externalplc-wh-sendsignals)

#### CDL / Automatic_Cycle/Transfer_Timer

23 source rungs; 15 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl-automatic-cycle-transfer-timer)

#### CDL / External_Communication/CDL_DC

15 source rungs; 2 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl-external-communication-cdl-dc)

#### CDL / Automatic_Cycle/WH_CDL_Begin

8 source rungs; 8 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl-automatic-cycle-wh-cdl-begin)

#### CDL / Automatic_Cycle/WH_CDL_End

4 source rungs; 4 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl-automatic-cycle-wh-cdl-end)

#### CDL / Automatic_Cycle/WH_CDL_Init

5 source rungs; 5 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl-automatic-cycle-wh-cdl-init)

#### CDL / Automatic_Cycle/WH_CDL_Start

2 source rungs; 2 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl-automatic-cycle-wh-cdl-start)

#### CDL / Automatic_Cycle/WH_CDL_Stop

12 source rungs; 12 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl-automatic-cycle-wh-cdl-stop)

#### CDL / Automatic_Cycle/WH_ReceiveDisplay

5 source rungs; 5 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl-automatic-cycle-wh-receivedisplay)

#### CDL / Automatic_Cycle/WH_SendSignals

16 source rungs; 16 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl-automatic-cycle-wh-sendsignals)

#### CDL / External_Communication/WH_PackMessage

4 source rungs; 4 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/cdl-external-communication-wh-packmessage)

### FDC

#### FDC / MainProgram/MainRoutine

22 source rungs; 3 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/fdc-mainprogram-mainroutine)

#### FDC / RF01CLX/Main

20 source rungs; 5 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/fdc-rf01clx-main)

#### FDC / RF02CLX/Main

21 source rungs; 5 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/fdc-rf02clx-main)

#### FDC / WH_Channel/Logic

108 source rungs; 108 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/fdc-wh-channel-logic)

#### FDC / MainProgram/WH_ReceiveLinks

42 source rungs; 42 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/fdc-mainprogram-wh-receivelinks)

#### FDC / MainProgram/WH_SiteBindings

27 source rungs; 27 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/fdc-mainprogram-wh-sitebindings)

#### FDC / MainProgram/WH_Startup

3 source rungs; 3 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/fdc-mainprogram-wh-startup)

#### FDC / MainProgram/WH_TransferDisplay

11 source rungs; 11 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/fdc-mainprogram-wh-transferdisplay)

#### FDC / RF01CLX/WH_CapturePost

96 source rungs; 2 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/fdc-rf01clx-wh-capturepost)

#### FDC / RF01CLX/WH_CapturePre

96 source rungs; 2 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/fdc-rf01clx-wh-capturepre)

#### FDC / RF02CLX/WH_CapturePost

96 source rungs; 2 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/fdc-rf02clx-wh-capturepost)

#### FDC / RF02CLX/WH_CapturePre

96 source rungs; 2 displayed. Full source is indexed below.

[Open this routine in the logic viewer](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/logic.html#logic-washheat-rev-o/fdc-rf02clx-wh-capturepre)


## 8. Exact executable source index

| PLC | Executable unit | Exact RLL |
|---|---|---|
| P50 | WH_Signals/WH_SendSignals | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/P50/Programs__WH_Signals__Routines__WH_SendSignals.rll.txt) |
| P300 | WH_Signals/WH_SendSignals | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/P300/Programs__WH_Signals__Routines__WH_SendSignals.rll.txt) |
| CDL1 | ExternalComms/WH_CDL_Begin | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL1/Programs__ExternalComms__Routines__WH_CDL_Begin.rll.txt) |
| CDL1 | ExternalComms/WH_CDL_End | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL1/Programs__ExternalComms__Routines__WH_CDL_End.rll.txt) |
| CDL1 | ExternalComms/WH_CDL_Init | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL1/Programs__ExternalComms__Routines__WH_CDL_Init.rll.txt) |
| CDL1 | ExternalComms/WH_CDL_Start | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL1/Programs__ExternalComms__Routines__WH_CDL_Start.rll.txt) |
| CDL1 | ExternalComms/WH_CDL_Stop | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL1/Programs__ExternalComms__Routines__WH_CDL_Stop.rll.txt) |
| CDL1 | ExternalComms/WH_PackMessage | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL1/Programs__ExternalComms__Routines__WH_PackMessage.rll.txt) |
| CDL1 | ExternalComms/WH_ReceiveDisplay | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL1/Programs__ExternalComms__Routines__WH_ReceiveDisplay.rll.txt) |
| CDL1 | ExternalComms/WH_SendSignals | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL1/Programs__ExternalComms__Routines__WH_SendSignals.rll.txt) |
| CDL1 | ExternalComms/CDL_DC | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL1/Programs__ExternalComms__Routines__CDL_DC.rll.txt) |
| CDL1 | ExternalComms/Transfer_Timer | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL1/Programs__ExternalComms__Routines__Transfer_Timer.rll.txt) |
| CDL2 | ExternalPLC/WH_Adapter | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL2/Programs__ExternalPLC__Routines__WH_Adapter.rll.txt) |
| CDL2 | ExternalPLC/WH_PackMessage | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL2/Programs__ExternalPLC__Routines__WH_PackMessage.rll.txt) |
| CDL2 | ExternalPLC/WH_ReceiveDisplay | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL2/Programs__ExternalPLC__Routines__WH_ReceiveDisplay.rll.txt) |
| CDL2 | ExternalPLC/WH_SendSignals | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL2/Programs__ExternalPLC__Routines__WH_SendSignals.rll.txt) |
| CDL2 | ExternalPLC/ToDataCollector | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL2/Programs__ExternalPLC__Routines__ToDataCollector.rll.txt) |
| CDL | Automatic_Cycle/WH_CDL_Begin | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL/Programs__Automatic_Cycle__Routines__WH_CDL_Begin.rll.txt) |
| CDL | Automatic_Cycle/WH_CDL_End | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL/Programs__Automatic_Cycle__Routines__WH_CDL_End.rll.txt) |
| CDL | Automatic_Cycle/WH_CDL_Init | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL/Programs__Automatic_Cycle__Routines__WH_CDL_Init.rll.txt) |
| CDL | Automatic_Cycle/WH_CDL_Start | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL/Programs__Automatic_Cycle__Routines__WH_CDL_Start.rll.txt) |
| CDL | Automatic_Cycle/WH_CDL_Stop | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL/Programs__Automatic_Cycle__Routines__WH_CDL_Stop.rll.txt) |
| CDL | Automatic_Cycle/WH_ReceiveDisplay | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL/Programs__Automatic_Cycle__Routines__WH_ReceiveDisplay.rll.txt) |
| CDL | Automatic_Cycle/WH_SendSignals | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL/Programs__Automatic_Cycle__Routines__WH_SendSignals.rll.txt) |
| CDL | External_Communication/WH_PackMessage | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL/Programs__External_Communication__Routines__WH_PackMessage.rll.txt) |
| CDL | Automatic_Cycle/Transfer_Timer | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL/Programs__Automatic_Cycle__Routines__Transfer_Timer.rll.txt) |
| CDL | External_Communication/CDL_DC | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/CDL/Programs__External_Communication__Routines__CDL_DC.rll.txt) |
| FDC | WH_Channel/Logic | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/FDC/AddOnInstructionDefinitions__WH_Channel__Routines__Logic.rll.txt) |
| FDC | MainProgram/WH_ReceiveLinks | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/FDC/Programs__MainProgram__Routines__WH_ReceiveLinks.rll.txt) |
| FDC | MainProgram/WH_SiteBindings | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/FDC/Programs__MainProgram__Routines__WH_SiteBindings.rll.txt) |
| FDC | MainProgram/WH_Startup | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/FDC/Programs__MainProgram__Routines__WH_Startup.rll.txt) |
| FDC | MainProgram/WH_TransferDisplay | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/FDC/Programs__MainProgram__Routines__WH_TransferDisplay.rll.txt) |
| FDC | RF01CLX/WH_CapturePost | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/FDC/Programs__RF01CLX__Routines__WH_CapturePost.rll.txt) |
| FDC | RF01CLX/WH_CapturePre | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/FDC/Programs__RF01CLX__Routines__WH_CapturePre.rll.txt) |
| FDC | RF02CLX/WH_CapturePost | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/FDC/Programs__RF02CLX__Routines__WH_CapturePost.rll.txt) |
| FDC | RF02CLX/WH_CapturePre | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/FDC/Programs__RF02CLX__Routines__WH_CapturePre.rll.txt) |
| FDC | MainProgram/MainRoutine | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/FDC/Programs__MainProgram__Routines__MainRoutine.rll.txt) |
| FDC | RF01CLX/Main | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/FDC/Programs__RF01CLX__Routines__Main.rll.txt) |
| FDC | RF02CLX/Main | [Source](https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/references/PLC/FDC/Programs__RF02CLX__Routines__Main.rll.txt) |


## 9. Manual press implementation

### Press changes — manual update of the current live programs

**Revision O implementation decision: apply the 50 MN and 300 MN WashHeat changes manually to each press's current live program.** The current live program is the implementation baseline. The recovered/converted press ACDs and full-controller L5X files in this delivery are offline reference and verification evidence, not replacement press projects for download.

**Status: manual implementation pending.** The WIN_L_VM verification results apply to the offline reference copies. They do not establish that either live press has been edited or verified after the proposed manual changes.

#### Small change set on each press

Add the five-rung Cycle Start counter logic below, four working tags, and one cyclic execution point. The reference implementation uses `WH_Signals/WH_SendSignals`. Merge that logic into the current live program with equivalent ordering, after the source-input update and before the existing press-to-FDC send logic. The reference schedules are shown below; reconcile their names and operands against the live program.

| Item | 50 MN reference | 300 MN reference |
|---|---|---|
| Recovered controller | 1789-L60 SoftLogix / 19.11 | 1756-L84E / 37.11 |
| Cycle Start source | `Local:2:I.Data[9].25` | `Logic.Auto.Start.Closed` |
| Counter destination | `P5000DataCtrlWord[3]` | `PressDataCtrlWrd[3]` |
| Reference execution order | Task `P5000`, immediately after `ITSLX`, 10 ms | Task `MachineLogicTask`, immediately after `IOIn` |
| Existing write MSG | `SLXDCMsg` | `SLXDC_MSG` |
| Existing payload | Words `[2..3]`, two DINTs / 8 bytes | Words `[2..3]`, two DINTs / 8 bytes |

Keep the current press arrays at DINT[4]. Retain existing words `[0..2]`, including the status/heartbeat in `[2]`, and the existing FDC-to-press `[0..1]` transfer. Word `[3]` carries the new persistent counter. Keep the live MSG path, count, source/destination configuration and send pacing. This change adds no MSG instruction.

##### Tags and first-use initialization

| New tag | Type | First-use value | Reference external access |
|---|---|---:|---|
| `MAX_INT` | DINT | 2147483647 | Read Only |
| `MAX_INT_MINUS_ONE` | DINT | 2147483646 | Read Only |
| `WH_SourceONS` | BOOL | 0, established while Cycle Start is inactive | None |
| `WH_SourceEdge` | BOOL | 0 | None |

The two DINTs are software constants with `Constant=false`, because the startup rungs write them. Use existing compatible tags if the live project already owns these names; avoid introducing a conflicting second writer.

**Do not rely on `S:FS` being true when inserting logic into an already-running program.** Initialize the two DINT values explicitly before the new counter logic executes. Establish word `[3]` as the initial counter baseline at FDC when bringing the change into service; this baseline is not a production Cycle Start. Establish the one-shot with Cycle Start inactive so installing the logic does not create a fabricated edge. Keep the `S:FS` rungs for normal startup initialization.

##### 50 MN reference rungs — native v19 mnemonics

```text
RUNG 000
COMMENT
INIT constants: signed DINT maximum and maximum minus one. Ordered branches initialize the controller-wide software constants before any consumer.
XIC(S:FS)[MOV(2147483647,MAX_INT),SUB(MAX_INT,1,MAX_INT_MINUS_ONE)];

RUNG 001
COMMENT
New startup baseline. Existing MSG carries word [3]; no array or message configuration change.
XIC(S:FS)MOV(0,P5000DataCtrlWord[3]);

RUNG 002
COMMENT
Retain a Cycle Start edge as a counter change even when the pulse ends before the next message.
XIC(Local:2:I.Data[9].25)ONS(WH_SourceONS)XIO(S:FS)OTE(WH_SourceEdge);

RUNG 003
COMMENT
Bounded counter wraps to 1 on this edge, without overflowing a DINT.
XIC(WH_SourceEdge)GEQ(P5000DataCtrlWord[3],MAX_INT_MINUS_ONE)MOV(0,P5000DataCtrlWord[3]);

RUNG 004
COMMENT
Existing press-to-FDC MSG already writes words [2..3]. FDC records approximate arrival time.
XIC(WH_SourceEdge)ADD(P5000DataCtrlWord[3],1,P5000DataCtrlWord[3]);
```

##### 300 MN reference rungs — native v37 mnemonics

```text
RUNG 000
COMMENT
INIT constants: signed DINT maximum and maximum minus one. Ordered branches initialize the controller-wide software constants before any consumer.
XIC(S:FS)[MOVE(2147483647,MAX_INT),SUB(MAX_INT,1,MAX_INT_MINUS_ONE)];

RUNG 001
COMMENT
New startup baseline. Existing MSG carries word [3]; no array or message configuration change.
XIC(S:FS)MOVE(0,PressDataCtrlWrd[3]);

RUNG 002
COMMENT
Retain a Cycle Start edge as a counter change even when the pulse ends before the next message.
XIC(Logic.Auto.Start.Closed)ONS(WH_SourceONS)XIO(S:FS)OTE(WH_SourceEdge);

RUNG 003
COMMENT
Bounded counter wraps to 1 on this edge, without overflowing a DINT.
XIC(WH_SourceEdge)GE(PressDataCtrlWrd[3],MAX_INT_MINUS_ONE)MOVE(0,PressDataCtrlWrd[3]);

RUNG 004
COMMENT
Existing press-to-FDC MSG already writes words [2..3]. FDC records approximate arrival time.
XIC(WH_SourceEdge)ADD(PressDataCtrlWrd[3],1,PressDataCtrlWrd[3]);
```

The counter increments once per observed rising edge. At or above 2147483646, that edge wraps the value to 1 without DINT overflow. It remains unchanged between edges, allowing the existing cyclic MSG to carry an event even after the Cycle Start pulse ends.

#### Verification after the manual merge

Run **Verify Controller on the updated live-program project**, and compare its diagnostics against that project's pre-change baseline. Check the actual input mapping, cyclic execution order, first-use constants and one-shot baseline, and the unchanged MSG payload. Confirm one counter increment per genuine Cycle Start and FDC reception of the changed word through the existing message. Record the updated live-project version and result when the work is performed.

FDC timestamps receipt with advisory **±1-second normal-operation uncertainty** and retains its one-second publication grace. These observations complement the operator's stopwatch and do not establish authoritative event order.

#### Meaning of the offline press results

- **300 MN:** the reference copy verifies with 0 errors / 79 baseline warnings after the matching MTS descriptions were registered on WIN_L_VM. This is evidence for the manual change, not a whole-project deployment instruction.
- **50 MN:** the native v19 reference and untouched original both report 17 errors / 22 warnings. The errors concern seven existing external-routine component specifications and ten associated `JXR` calls. The five WashHeat rungs add no errors. Use the live program's existing external components and hardware configuration for the manual merge; reconstructing the incomplete offline external-routine environment is not the selected press deployment route.
- The earlier 50 MN v37/L75 conversion is unsuitable as a press implementation baseline: it changed the controller type and omitted SoftLogix-specific content.

No live press modification or controller download was performed during this report update.


## Appendix A — Native declarations

### Complete PLC declarations

#### P50: all added tags

| Tag / scope | Type | Dimensions | External access |
|---|---|---|---|
| `Tags/MAX_INT` | DINT | — | Read Only |
| `Tags/MAX_INT_MINUS_ONE` | DINT | — | Read Only |
| `Tags/WH_SourceEdge` | BOOL | — | None |
| `Tags/WH_SourceONS` | BOOL | — | None |

#### P300: all added tags

| Tag / scope | Type | Dimensions | External access |
|---|---|---|---|
| `Tags/MAX_INT` | DINT | — | Read Only |
| `Tags/MAX_INT_MINUS_ONE` | DINT | — | Read Only |
| `Tags/WH_SourceEdge` | BOOL | — | None |
| `Tags/WH_SourceONS` | BOOL | — | None |

#### CDL1: `WH_CDL_Display`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_CDL_Display | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Boot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Sequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Furnace` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Slot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Active` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TransferMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `LimitMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `LimitValid` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Exceeded` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `DataValid` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TargetCdl` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### CDL1: `WH_CDL_Event`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_CDL_Event | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Sequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Boot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Kind` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Furnace` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `StartedUTC` | `DINT` | 7 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `CapturedUTC` | `DINT` | 7 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TimerMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `At33000` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `At5000` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Enter300MN` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### CDL1: `WH_LinkData`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_LinkData | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Boot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `SampleSequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `EventSequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ClockValidated` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Fault` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Furnace` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Running` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TimerMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `EventUTC` | `DINT` | 7 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TransferElapsedMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `SourceId` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### CDL1: all added tags

| Tag / scope | Type | Dimensions | External access |
|---|---|---|---|
| `Programs/ExternalComms/Tags/WH_CDL_Furnace` | DINT | — | None |
| `Programs/ExternalComms/Tags/WH_CDL_LastTimerMs` | DINT | — | None |
| `Programs/ExternalComms/Tags/WH_CDL_Publish` | BOOL | — | None |
| `Programs/ExternalComms/Tags/WH_CDL_Sequence` | DINT | — | None |
| `Programs/ExternalComms/Tags/WH_CDL_StartedFurnace` | DINT | — | None |
| `Programs/ExternalComms/Tags/WH_CDL_StartedUTC` | DINT | 7 | None |
| `Programs/ExternalComms/Tags/WH_CDL_WasRunning` | BOOL | — | None |
| `Programs/ExternalComms/Tags/WH_CDL_Zero` | WH_CDL_Event | — | None |
| `Tags/MAX_INT` | DINT | — | Read Only |
| `Tags/MAX_INT_MINUS_ONE` | DINT | — | Read Only |
| `Tags/WH_CDL_AckBoot` | DINT | — | Read/Write |
| `Tags/WH_CDL_AckSequence` | DINT | — | Read/Write |
| `Tags/WH_CDL_Boot` | DINT | — | Read Only |
| `Tags/WH_CDL_Event` | WH_CDL_Event | — | Read Only |
| `Tags/WH_CDL_Fault` | DINT | — | Read Only |
| `Tags/WH_CDL_State` | DINT | — | Read Only |
| `Tags/WH_ClockValidated` | DINT | — | None |
| `Tags/WH_Display` | WH_CDL_Display | — | Read Only |
| `Tags/WH_DisplayAge` | TIMER | — | Read Only |
| `Tags/WH_DisplaySeen` | DINT | — | Read Only |
| `Tags/WH_LinkLive` | WH_LinkData | — | None |
| `Tags/WH_NewSnapshot` | BOOL | — | None |
| `Tags/WH_SourceEdge` | BOOL | — | None |
| `Tags/WH_SourceONS` | BOOL | — | None |
| `Tags/WH_TransferElapsed` | TIMER | — | Read Only |
| `Tags/WH_TransferPopup` | BOOL | — | Read Only |
| `Tags/WH_TransferStarted` | BOOL | — | None |

#### CDL2: `WH_CDL_Display`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_CDL_Display | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Boot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Sequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Furnace` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Slot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Active` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TransferMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `LimitMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `LimitValid` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Exceeded` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `DataValid` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TargetCdl` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### CDL2: `WH_LinkData`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_LinkData | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Boot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `SampleSequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `EventSequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ClockValidated` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Fault` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Furnace` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Running` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TimerMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `EventUTC` | `DINT` | 7 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TransferElapsedMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `SourceId` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### CDL2: all added tags

| Tag / scope | Type | Dimensions | External access |
|---|---|---|---|
| `Tags/MAX_INT` | DINT | — | Read Only |
| `Tags/MAX_INT_MINUS_ONE` | DINT | — | Read Only |
| `Tags/WH_AdapterRunning` | BOOL | — | None |
| `Tags/WH_AdapterStart` | BOOL | — | None |
| `Tags/WH_CDL_Armed` | BOOL | — | None |
| `Tags/WH_CDL_Furnace` | DINT | — | None |
| `Tags/WH_ClockValidated` | DINT | — | None |
| `Tags/WH_Display` | WH_CDL_Display | — | Read Only |
| `Tags/WH_DisplayAge` | TIMER | — | None |
| `Tags/WH_DisplaySeen` | DINT | — | None |
| `Tags/WH_LinkLive` | WH_LinkData | — | None |
| `Tags/WH_NewSnapshot` | BOOL | — | None |
| `Tags/WH_RawTransferTimer` | TIMER | — | None |
| `Tags/WH_SourceEdge` | BOOL | — | None |
| `Tags/WH_SourceONS` | BOOL | — | None |
| `Tags/WH_TransferElapsed` | TIMER | — | Read Only |
| `Tags/WH_TransferPopup` | BOOL | — | Read Only |
| `Tags/WH_TransferStarted` | BOOL | — | None |

#### CDL: `WH_CDL_Display`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_CDL_Display | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Boot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Sequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Furnace` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Slot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Active` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TransferMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `LimitMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `LimitValid` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Exceeded` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `DataValid` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TargetCdl` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### CDL: `WH_CDL_Event`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_CDL_Event | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Sequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Boot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Kind` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Furnace` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `StartedUTC` | `DINT` | 7 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `CapturedUTC` | `DINT` | 7 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TimerMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `At33000` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `At5000` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Enter300MN` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### CDL: `WH_LinkData`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_LinkData | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Boot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `SampleSequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `EventSequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ClockValidated` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Fault` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Furnace` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Running` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TimerMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `EventUTC` | `DINT` | 7 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TransferElapsedMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `SourceId` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### CDL: all added tags

| Tag / scope | Type | Dimensions | External access |
|---|---|---|---|
| `Programs/Automatic_Cycle/Tags/WH_CDL_Furnace` | DINT | — | None |
| `Programs/Automatic_Cycle/Tags/WH_CDL_LastTimerMs` | DINT | — | None |
| `Programs/Automatic_Cycle/Tags/WH_CDL_Publish` | BOOL | — | None |
| `Programs/Automatic_Cycle/Tags/WH_CDL_Sequence` | DINT | — | None |
| `Programs/Automatic_Cycle/Tags/WH_CDL_StartedFurnace` | DINT | — | None |
| `Programs/Automatic_Cycle/Tags/WH_CDL_StartedUTC` | DINT | 7 | None |
| `Programs/Automatic_Cycle/Tags/WH_CDL_WasRunning` | BOOL | — | None |
| `Programs/Automatic_Cycle/Tags/WH_CDL_Zero` | WH_CDL_Event | — | None |
| `Tags/MAX_INT` | DINT | — | Read Only |
| `Tags/MAX_INT_MINUS_ONE` | DINT | — | Read Only |
| `Tags/WH_CDL_AckBoot` | DINT | — | Read/Write |
| `Tags/WH_CDL_AckSequence` | DINT | — | Read/Write |
| `Tags/WH_CDL_Boot` | DINT | — | Read Only |
| `Tags/WH_CDL_Event` | WH_CDL_Event | — | Read Only |
| `Tags/WH_CDL_Fault` | DINT | — | Read Only |
| `Tags/WH_CDL_State` | DINT | — | Read Only |
| `Tags/WH_ClockValidated` | DINT | — | None |
| `Tags/WH_Display` | WH_CDL_Display | — | Read Only |
| `Tags/WH_DisplayAge` | TIMER | — | Read Only |
| `Tags/WH_DisplaySeen` | DINT | — | Read Only |
| `Tags/WH_LinkLive` | WH_LinkData | — | None |
| `Tags/WH_NewSnapshot` | BOOL | — | None |
| `Tags/WH_SourceEdge` | BOOL | — | None |
| `Tags/WH_SourceONS` | BOOL | — | None |
| `Tags/WH_TransferElapsed` | TIMER | — | Read Only |
| `Tags/WH_TransferPopup` | BOOL | — | Read Only |
| `Tags/WH_TransferStarted` | BOOL | — | None |

#### WH_Channel revision 5.0 — complete signature and local state

| Parameter | Type | Usage |
|---|---|---|
| EnableIn | BOOL | Input |
| EnableOut | BOOL | Output |
| Phase | DINT | Input |
| Furnace | DINT | Input |
| Slot | DINT | Input |
| Item | sFurnaceItem | InOut |
| Cfg | WH_Settings | InOut |
| Site | WH_Site | InOut |
| Limit | WH_TransferLimit | InOut |
| Source | WH_Physical | InOut |
| State | WH_State | InOut |
| Event | WH_EventData | InOut |
| Receipt | WH_EventReceipt | InOut |
| Elapsed | TIMER | InOut |
| MaxInt | DINT | Input |
| MaxIntMinusOne | DINT | Input |

| Local | Type | Dimensions |
|---|---|---|
| SeenBoot | DINT | — |
| SeenInstallation | DINT | 4 |
| Frame | WH_Physical | — |
| PreviousMask | DINT | — |
| Mask | DINT | — |
| Capture | DINT | — |
| NewPhysical | DINT | — |
| SampleCounter | DINT | — |
| ZeroState | WH_State | — |
| ZeroEvent | WH_EventData | — |
| ExpectedSource | DINT | — |
| ReceiptMatches | BOOL | — |
| CaptureBefore | BOOL | — |
| PublishAfter | BOOL | — |
| ChannelIndex | DINT | — |
| MapEmit | BOOL | — |
| MapReady | BOOL | — |
| MapOwner | BOOL | — |
| MapReturn | BOOL | — |
| MapDecision | BOOL | — |
| MapCycle | BOOL | — |
| MapStart | BOOL | — |
| MapFault | BOOL | — |
| MapLimit | BOOL | — |
| MapDecisionEdge | BOOL | — |
| MapTimeOrder | DINT | — |
| MapReturnSeen | BOOL | — |

#### FDC: `WH_CDL_Display`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_CDL_Display | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Boot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Sequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Furnace` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Slot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Active` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TransferMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `LimitMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `LimitValid` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Exceeded` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `DataValid` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TargetCdl` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### FDC: `WH_EventData`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_EventData | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Sequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Installation` | `DINT` | 4 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Boot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Furnace` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Slot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `CommandMask` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ClockValidated` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `PhysicalIsNew` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `CapturedUTC` | `DINT` | 7 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `MappingApproved` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `QualifyingSourceApproved` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TimerReturnSequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TimerValid` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ElapsedMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Physical` | `WH_Physical` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `BoundItem` | `sFurnaceItem` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `Before` | `sFurnaceItem` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `After` | `sFurnaceItem` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |

#### FDC: `WH_EventReceipt`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_EventReceipt | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Installation` | `DINT` | 4 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Boot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Sequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### FDC: `WH_Identity`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_Identity | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `SN` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `WO` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `PN` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `Stage` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `QA` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `Recipe` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `PressQA` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `LoadStamp` | `DINT` | 7 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### FDC: `WH_LinkData`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_LinkData | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Boot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `SampleSequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `EventSequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ClockValidated` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Fault` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Furnace` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Running` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TimerMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `EventUTC` | `DINT` | 7 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TransferElapsedMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `SourceId` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### FDC: `WH_LinkState`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_LinkState | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Boot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `SampleSequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `EventSequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ExpectedEvent` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Valid` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Fault` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Freshness` | `TIMER` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `Heartbeat` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### FDC: `WH_Physical`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_Physical | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Sequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `BindingValid` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ReturnConfirmed` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Removal` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `CycleStart` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Decision` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `WashAuthorized` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `OriginFurnace` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Identity` | `WH_Identity` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `QualifyingValid` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `QualifyingMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `MaximumSoakMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `OccurredUTC` | `DINT` | 7 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `CdlId` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Press` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### FDC: `WH_Settings`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_Settings | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Installation` | `DINT` | 4 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Boot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `MappingApproved` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `QualifyingSourceApproved` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ClockValidated` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### FDC: `WH_Site`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_Site | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Fault` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `CandidateCount` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `CandidateIndex` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `CandidateFurnace` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `CandidatePress` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `CandidateItem` | `sFurnaceItem` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `Active` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Index` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Furnace` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Press` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `CdlId` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Item` | `sFurnaceItem` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `Removed` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Destination1` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Destination2` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `StartPending` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `StartUTC` | `DINT` | 7 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `StartFurnace` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `CyclePending` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `CycleUTC` | `DINT` | 7 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `CycleGrace` | `TIMER` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `DecisionPending` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `DecisionUTC` | `DINT` | 7 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `DecisionObserved` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `OwnerBusy` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ReturnCount` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ReturnIndex` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ReturnPending` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ReturnUTC` | `DINT` | 7 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ReturnItem` | `sFurnaceItem` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `TransferMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `LimitMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `LimitValid` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### FDC: `WH_State`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_State | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `SampleSequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Installation` | `DINT` | 4 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Boot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Furnace` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Slot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `MappingApproved` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ClockValidated` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `QualifyingSourceApproved` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `CaptureState` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `EventSequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `SourceSequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Fault` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TimerState` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TimerReturnSequence` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TimerValid` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ElapsedMs` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ItemEmpty` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ItemStamped` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ItemWashHeat` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `CurrentIdentity` | `WH_Identity` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `Physical` | `WH_Physical` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |

#### FDC: `WH_TransferLimit`

WashHeat interface v4: selectable CDL adapters, legacy MSG transport and exact operation identity; Ignition-owned workflow.

| Definition | Source attributes |
|---|---|
| WH_TransferLimit | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Boot` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `LoadStamp` | `DINT` | 7 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Milliseconds` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Valid` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### FDC: all added tags

| Tag / scope | Type | Dimensions | External access |
|---|---|---|---|
| `Programs/MainProgram/Tags/WH_ZeroPhysical` | WH_Physical | — | None |
| `Programs/RF01CLX/Tags/WH_Node_01A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_01B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_01C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_01D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_02A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_02B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_02C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_02D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_03A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_03B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_03C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_03D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_04A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_04B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_04C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_04D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_05A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_05B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_05C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_05D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_06A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_06B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_06C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_06D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_07A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_07B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_07C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_07D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_08A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_08B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_08C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_08D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_09A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_09B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_09C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_09D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_10A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_10B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_10C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_10D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_11A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_11B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_11C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_11D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_12A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_12B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_12C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_12D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_13A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_13B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_13C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_13D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_14A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_14B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_14C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_14D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_15A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_15B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_15C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_15D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_16A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_16B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_16C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_16D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_17A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_17B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_17C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_17D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_18A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_18B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_18C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_18D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_19A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_19B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_19C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_19D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_20A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_20B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_20C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_20D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_21A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_21B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_21C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_21D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_22A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_22B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_22C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_22D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_23A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_23B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_23C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_23D` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_24A` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_24B` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_24C` | WH_Channel | — | None |
| `Programs/RF01CLX/Tags/WH_Node_24D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_01A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_01B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_01C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_01D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_02A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_02B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_02C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_02D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_03A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_03B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_03C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_03D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_04A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_04B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_04C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_04D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_05A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_05B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_05C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_05D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_06A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_06B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_06C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_06D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_07A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_07B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_07C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_07D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_08A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_08B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_08C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_08D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_09A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_09B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_09C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_09D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_10A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_10B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_10C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_10D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_11A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_11B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_11C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_11D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_12A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_12B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_12C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_12D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_13A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_13B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_13C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_13D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_14A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_14B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_14C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_14D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_15A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_15B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_15C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_15D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_16A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_16B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_16C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_16D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_17A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_17B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_17C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_17D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_18A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_18B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_18C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_18D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_19A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_19B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_19C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_19D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_20A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_20B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_20C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_20D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_21A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_21B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_21C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_21D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_22A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_22B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_22C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_22D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_23A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_23B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_23C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_23D` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_24A` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_24B` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_24C` | WH_Channel | — | None |
| `Programs/RF02CLX/Tags/WH_Node_24D` | WH_Channel | — | None |
| `Tags/MAX_INT` | DINT | — | Read Only |
| `Tags/MAX_INT_MINUS_ONE` | DINT | — | Read Only |
| `Tags/WH_ActiveCDL` | DINT | — | Read/Write |
| `Tags/WH_BindCandidate` | BOOL | — | None |
| `Tags/WH_ClockValidated` | DINT | — | None |
| `Tags/WH_DisplayLive` | WH_CDL_Display | — | None |
| `Tags/WH_Elapsed` | TIMER | 192 | None |
| `Tags/WH_Event` | WH_EventData | 192 | Read Only |
| `Tags/WH_Link` | WH_LinkData | 3 | Read Only |
| `Tags/WH_LinkState` | WH_LinkState | 3 | Read Only |
| `Tags/WH_NewLinkEvent` | BOOL | 32 | None |
| `Tags/WH_PressHeartbeatEdge` | BOOL | 32 | None |
| `Tags/WH_Receipt` | WH_EventReceipt | 192 | Read/Write |
| `Tags/WH_SelectedCDL` | DINT | — | Read Only |
| `Tags/WH_Settings` | WH_Settings | — | None |
| `Tags/WH_Site` | WH_Site | — | Read Only |
| `Tags/WH_Source` | WH_Physical | 192 | None |
| `Tags/WH_State` | WH_State | 192 | Read Only |
| `Tags/WH_TransferLimit` | WH_TransferLimit | 192 | Read/Write |

#### FDC: existing dependency `TIMER`

| Definition | Source attributes |
|---|---|
| TIMER | Family=NoFamily; Class=ProductDefined |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Control` | `DINT` | 0 | Radix=Decimal; Hidden=true; ExternalAccess=Read/Write |
| `PRE` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `ACC` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `EN` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=Control; BitNumber=31; ExternalAccess=Read/Write |
| `TT` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=Control; BitNumber=30; ExternalAccess=Read/Write |
| `DN` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=Control; BitNumber=29; ExternalAccess=Read/Write |

#### FDC: existing dependency `sDateTime`

Date Time Structure

| Definition | Source attributes |
|---|---|
| sDateTime | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `Year` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Month` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Day` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Hour` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Minute` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Second` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Microsecond` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### FDC: existing dependency `sFurnaceItem`

Item Specification

| Definition | Source attributes |
|---|---|
| sFurnaceItem | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `strSN` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `strPN` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `strTemperature` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `strBarCodeTemperature` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `strStg` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `strTolerance` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `strSoak` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `strMaxSoak` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `strWO` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `strQA` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `strTimeIn` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `strTimeOut` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `strWHTimeIn` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `strWHTimeOut` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `strRecipe` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `strPressQA` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `MinSoak` | `sTime` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `MaxSoak` | `sTime` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `TotalSoak` | `sTime` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `TimeStampIn` | `sDateTime` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `TimeStampSoak` | `sDateTime` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `TimeStampOut` | `sDateTime` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `SoakTimer` | `TIMER` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `ToleranceTimer` | `TIMER` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `TransitionTimer` | `TIMER` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `Control` | `sFurnaceItemControl` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `TransitionTime` | `sTime` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `SoakSegment` | `INT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Status` | `INT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `MinTemperature` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `MaxTemperature` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TemperatureSP` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `TemperatureTolerance` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `WHTimeStampIn` | `sDateTime` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `WHTimeStampOut` | `sDateTime` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |
| `WHSoakSegment` | `INT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |

#### FDC: existing dependency `sFurnaceItemControl`

Scan Item

| Definition | Source attributes |
|---|---|
| sFurnaceItemControl | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `ZZZZZZZZZZsFurnaceIt0` | `SINT` | 0 | Radix=Decimal; Hidden=true; ExternalAccess=Read/Write |
| `cmdAccept` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt0; BitNumber=0; ExternalAccess=Read/Write |
| `cmdClear` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt0; BitNumber=1; ExternalAccess=Read/Write |
| `cmdLoad` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt0; BitNumber=2; ExternalAccess=Read/Write |
| `cmdRemove` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt0; BitNumber=3; ExternalAccess=Read/Write |
| `cmdCancel` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt0; BitNumber=4; ExternalAccess=Read/Write |
| `cmdValidate` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt0; BitNumber=5; ExternalAccess=Read/Write |
| `cmdReset` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt0; BitNumber=6; ExternalAccess=Read/Write |
| `cmdStamp` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt0; BitNumber=7; ExternalAccess=Read/Write |
| `ZZZZZZZZZZsFurnaceIt9` | `SINT` | 0 | Radix=Decimal; Hidden=true; ExternalAccess=Read/Write |
| `cmdCancelStamp` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt9; BitNumber=0; ExternalAccess=Read/Write |
| `cmdWashHeat` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt9; BitNumber=1; ExternalAccess=Read/Write |
| `cmdLoadWashHeat` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt9; BitNumber=2; ExternalAccess=Read/Write |
| `cmdPartAtPress` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt9; BitNumber=3; ExternalAccess=Read/Write |
| `stsLocked` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt9; BitNumber=4; ExternalAccess=Read/Write |
| `stsEmpty` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt9; BitNumber=5; ExternalAccess=Read/Write |
| `stsAccepted` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt9; BitNumber=6; ExternalAccess=Read/Write |
| `stsLoaded` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt9; BitNumber=7; ExternalAccess=Read/Write |
| `ZZZZZZZZZZsFurnaceIt18` | `SINT` | 0 | Radix=Decimal; Hidden=true; ExternalAccess=Read/Write |
| `stsSoaking` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt18; BitNumber=0; ExternalAccess=Read/Write |
| `stsRemoved` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt18; BitNumber=1; ExternalAccess=Read/Write |
| `stsValidated` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt18; BitNumber=2; ExternalAccess=Read/Write |
| `stsToleranceWarning` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt18; BitNumber=3; ExternalAccess=Read/Write |
| `stsToleranceAlarm` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt18; BitNumber=4; ExternalAccess=Read/Write |
| `stsStamped` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt18; BitNumber=5; ExternalAccess=Read/Write |
| `stsTroposEvent` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt18; BitNumber=6; ExternalAccess=Read/Write |
| `stsTroposError` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt18; BitNumber=7; ExternalAccess=Read/Write |
| `ZZZZZZZZZZsFurnaceIt27` | `SINT` | 0 | Radix=Decimal; Hidden=true; ExternalAccess=Read/Write |
| `stsOutOfToleranceHI` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt27; BitNumber=0; ExternalAccess=Read/Write |
| `stsOutOfToleranceLO` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt27; BitNumber=1; ExternalAccess=Read/Write |
| `stsWashHeat` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt27; BitNumber=2; ExternalAccess=Read/Write |
| `stsPartAtPress` | `BIT` | 0 | Radix=Decimal; Hidden=false; Target=ZZZZZZZZZZsFurnaceIt27; BitNumber=3; ExternalAccess=Read/Write |

#### FDC: existing dependency `sTime`

Seconds Component

| Definition | Source attributes |
|---|---|
| sTime | Family=NoFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `msecTime` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Minutes` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `Time` | `strItemInfo` | 0 | Radix=NullType; Hidden=false; ExternalAccess=Read/Write |

#### FDC: existing dependency `strItemInfo`

| Definition | Source attributes |
|---|---|
| strItemInfo | Family=StringFamily; Class=User |

| Member | Data type | Dimension | Other declared attributes |
|---|---|---|---|
| `LEN` | `DINT` | 0 | Radix=Decimal; Hidden=false; ExternalAccess=Read/Write |
| `DATA` | `SINT` | 32 | Radix=ASCII; Hidden=false; ExternalAccess=Read/Write |


## Appendix B — Complete SQL DDL

### washheat.run

```sql
CREATE TABLE washheat.run (
    run_id nvarchar(64) NOT NULL PRIMARY KEY,
    furnace nvarchar(4) NOT NULL CHECK (furnace IN ('RF01','RF02')),
    phase nvarchar(40) NOT NULL,
    revision int NOT NULL CHECK (revision >= 0),
    snapshot nvarchar(max) NOT NULL CHECK (ISJSON(snapshot) = 1),
    created_at datetime2(3) NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_at datetime2(3) NOT NULL DEFAULT SYSUTCDATETIME()
);
```

### washheat.event

```sql
CREATE TABLE washheat.event (
    event_id nvarchar(64) NOT NULL PRIMARY KEY,
    run_id nvarchar(64) NOT NULL REFERENCES washheat.run(run_id),
    event_type nvarchar(40) NOT NULL,
    event_at_ms bigint NOT NULL,
    payload nvarchar(max) NOT NULL CHECK (ISJSON(payload) = 1),
    payload_sha256 char(64) NOT NULL,
    actor nvarchar(128) NOT NULL,
    state_revision int NOT NULL,
    received_at datetime2(3) NOT NULL DEFAULT SYSUTCDATETIME(),
    UNIQUE (run_id, state_revision)
);
```

### washheat.handling_slot

```sql
CREATE TABLE washheat.handling_slot (
        slot_id int NOT NULL PRIMARY KEY CHECK (slot_id = 1),
        run_id nvarchar(64) NULL REFERENCES washheat.run(run_id)
    );
```

### washheat.tropos_record

```sql
CREATE TABLE washheat.tropos_record (
    run_id nvarchar(64) NOT NULL REFERENCES washheat.run(run_id),
    episode_no int NOT NULL,
    record_revision int NOT NULL DEFAULT 1,
    payload nvarchar(max) NOT NULL CHECK (ISJSON(payload) = 1),
    payload_sha256 char(64) NOT NULL,
    review_status nvarchar(40) NOT NULL DEFAULT 'PENDING_QUALITY_PRODUCTION',
    submission_status nvarchar(40) NOT NULL DEFAULT 'NOT_SENT' CHECK (submission_status = 'NOT_SENT'),
    created_at datetime2(3) NOT NULL DEFAULT SYSUTCDATETIME(),
    PRIMARY KEY (run_id, episode_no, record_revision)
);
```

### washheat.schema_version

```sql
CREATE TABLE washheat.schema_version(version int PRIMARY KEY, installed_at datetime2(3) DEFAULT SYSUTCDATETIME());
```

### washheat.plc_binding

```sql
CREATE TABLE washheat.plc_binding (
    binding_key char(64) NOT NULL PRIMARY KEY,
    run_id nvarchar(64) NOT NULL UNIQUE REFERENCES washheat.run(run_id),
    controller nvarchar(128) NOT NULL,
    channel_index int NULL CHECK (channel_index BETWEEN 0 AND 191),
    payload nvarchar(max) NOT NULL CHECK (ISJSON(payload)=1)
);
```

### washheat.plc_capture

```sql
CREATE TABLE washheat.plc_capture (
    capture_key char(64) NOT NULL PRIMARY KEY,
    channel_key char(64) NOT NULL,
    event_sequence int NOT NULL CHECK (event_sequence>0),
    run_id nvarchar(64) NULL REFERENCES washheat.run(run_id),
    disposition int NOT NULL CHECK (disposition IN (100,200,900)),
    reason nvarchar(1024) NULL,
    payload nvarchar(max) NOT NULL CHECK (ISJSON(payload)=1),
    payload_sha256 char(64) NOT NULL,
    received_at_ms bigint NOT NULL,
    UNIQUE (channel_key,event_sequence)
);
```

### washheat.plc_sample

```sql
CREATE TABLE washheat.plc_sample (
    run_id nvarchar(64) NOT NULL PRIMARY KEY REFERENCES washheat.run(run_id),
    payload nvarchar(max) NOT NULL CHECK (ISJSON(payload)=1)
);
```

### washheat.part_recipe

```sql
CREATE TABLE washheat.part_recipe (
    recipe_id nvarchar(64) NOT NULL PRIMARY KEY,
    part_number nvarchar(32) COLLATE Latin1_General_100_BIN2 NOT NULL,
    stage nvarchar(32) COLLATE Latin1_General_100_BIN2 NOT NULL,
    qa_spec nvarchar(32) COLLATE Latin1_General_100_BIN2 NOT NULL,
    press_recipe nvarchar(32) COLLATE Latin1_General_100_BIN2 NOT NULL,
    press_qa nvarchar(32) COLLATE Latin1_General_100_BIN2 NOT NULL,
    od_in decimal(18,6) NOT NULL CHECK (od_in > 0),
    height_in decimal(18,6) NOT NULL CHECK (height_in > 0),
    circle_in decimal(18,6) NULL CHECK (circle_in > 0),
    max_transfer_seconds decimal(18,6) NULL,
    dh_cycle_start_seconds decimal(18,6) NULL,
    dh_tonnage_seconds decimal(18,6) NULL,
    active bit NOT NULL DEFAULT 1,
    revision int NOT NULL CHECK (revision > 0),
    notes nvarchar(1024) NOT NULL DEFAULT '',
    updated_by nvarchar(128) NOT NULL,
    updated_at datetime2(3) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT UQ_part_recipe_lookup UNIQUE (part_number, stage, qa_spec, press_recipe, press_qa),
    CONSTRAINT CK_part_recipe_timing CHECK (
      (max_transfer_seconds IS NULL AND dh_cycle_start_seconds IS NULL AND dh_tonnage_seconds IS NULL) OR
      (max_transfer_seconds IS NOT NULL AND dh_cycle_start_seconds IS NOT NULL AND dh_tonnage_seconds IS NOT NULL
       AND max_transfer_seconds >= 0 AND dh_cycle_start_seconds >= 0 AND dh_tonnage_seconds >= 0
       AND max_transfer_seconds + dh_cycle_start_seconds - dh_tonnage_seconds - 3 > 0
       AND max_transfer_seconds + dh_cycle_start_seconds - dh_tonnage_seconds - 3 <= 2147483.646))
);
```

### washheat.part_recipe_revision

```sql
CREATE TABLE washheat.part_recipe_revision (
    recipe_id nvarchar(64) NOT NULL REFERENCES washheat.part_recipe(recipe_id),
    revision int NOT NULL,
    payload nvarchar(max) NOT NULL CHECK (ISJSON(payload) = 1),
    changed_by nvarchar(128) NOT NULL,
    changed_at datetime2(3) NOT NULL DEFAULT SYSUTCDATETIME(),
    PRIMARY KEY (recipe_id, revision)
);
```

### washheat.run_recipe

```sql
CREATE TABLE washheat.run_recipe (
    run_id nvarchar(64) NOT NULL PRIMARY KEY REFERENCES washheat.run(run_id),
    recipe_id nvarchar(64) NOT NULL,
    recipe_revision int NOT NULL,
    enrolled_by nvarchar(128) NOT NULL,
    FOREIGN KEY (recipe_id, recipe_revision) REFERENCES washheat.part_recipe_revision(recipe_id, revision)
);
```
