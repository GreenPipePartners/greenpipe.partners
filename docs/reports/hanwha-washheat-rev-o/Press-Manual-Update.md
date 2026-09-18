# Press changes — manual update of the current live programs

**Revision O implementation decision: apply the 50 MN and 300 MN WashHeat changes manually to each press's current live program.** The current live program is the implementation baseline. The recovered/converted press ACDs and full-controller L5X files in this delivery are offline reference and verification evidence, not replacement press projects for download.

**Status: manual implementation pending.** The WIN_L_VM verification results apply to the offline reference copies. They do not establish that either live press has been edited or verified after the proposed manual changes.

## Small change set on each press

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

### Tags and first-use initialization

| New tag | Type | First-use value | Reference external access |
|---|---|---:|---|
| `MAX_INT` | DINT | 2147483647 | Read Only |
| `MAX_INT_MINUS_ONE` | DINT | 2147483646 | Read Only |
| `WH_SourceONS` | BOOL | 0, established while Cycle Start is inactive | None |
| `WH_SourceEdge` | BOOL | 0 | None |

The two DINTs are software constants with `Constant=false`, because the startup rungs write them. Use existing compatible tags if the live project already owns these names; avoid introducing a conflicting second writer.

**Do not rely on `S:FS` being true when inserting logic into an already-running program.** Initialize the two DINT values explicitly before the new counter logic executes. Establish word `[3]` as the initial counter baseline at FDC when bringing the change into service; this baseline is not a production Cycle Start. Establish the one-shot with Cycle Start inactive so installing the logic does not create a fabricated edge. Keep the `S:FS` rungs for normal startup initialization.

### 50 MN reference rungs — native v19 mnemonics

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

### 300 MN reference rungs — native v37 mnemonics

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

## Verification after the manual merge

Run **Verify Controller on the updated live-program project**, and compare its diagnostics against that project's pre-change baseline. Check the actual input mapping, cyclic execution order, first-use constants and one-shot baseline, and the unchanged MSG payload. Confirm one counter increment per genuine Cycle Start and FDC reception of the changed word through the existing message. Record the updated live-project version and result when the work is performed.

FDC timestamps receipt with advisory **±1-second normal-operation uncertainty** and retains its one-second publication grace. These observations complement the operator's stopwatch and do not establish authoritative event order.

## Meaning of the offline press results

- **300 MN:** the reference copy verifies with 0 errors / 79 baseline warnings after the matching MTS descriptions were registered on WIN_L_VM. This is evidence for the manual change, not a whole-project deployment instruction.
- **50 MN:** the native v19 reference and untouched original both report 17 errors / 22 warnings. The errors concern seven existing external-routine component specifications and ten associated `JXR` calls. The five WashHeat rungs add no errors. Use the live program's existing external components and hardware configuration for the manual merge; reconstructing the incomplete offline external-routine environment is not the selected press deployment route.
- The earlier 50 MN v37/L75 conversion is unsuitable as a press implementation baseline: it changed the controller type and omitted SoftLogix-specific content.

No live press modification or controller download was performed during this report update.
