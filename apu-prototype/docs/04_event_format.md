# Event format

The MVP uses one 128-bit beat per replay event and one 128-bit beat per encoded action response.

## Input `event_t` bit mapping

| Bits | Field |
| --- | --- |
| `[7:0]` | `event_type` |
| `[8]` | `side` (`0=bid`, `1=ask`) |
| `[40:9]` | `price` (signed fixed-point placeholder) |
| `[72:41]` | `qty` |
| `[104:73]` | `ts` |
| `[127:105]` | `flags` |

Supported event types:

- `0`: NOP
- `1`: ADD
- `2`: CANCEL
- `3`: TRADE
- `4`: UPDATE

Invalid event types are normalized by the parser into `NOP` with `flags[0]=1`, making bad frames deterministic and visible to software.

## `feature_t` fields

The orderbook stage emits one feature record per accepted input event after the BRAM-backed state update is committed:

- best bid price / qty
- best ask price / qty
- spread (`best_ask_price - best_bid_price` when valid)
- imbalance (`best_bid_qty - best_ask_qty`)
- last trade price / qty
- `event_ts` copied from the triggering replay event

## Internal `action_t` fields

The decision and risk stages exchange `action_t` internally as a packed struct with:

- `action_type`
- `price`
- `qty`
- `reason_code`
- `timestamp`
- reserved bits for later expansion

`timestamp` currently carries the originating event timestamp so the encoder and golden model can agree exactly on the emitted action frame.

## Output action frame (host-visible)

The order encoder emits this explicit 128-bit layout:

| Bits | Field |
| --- | --- |
| `[127:120]` | `action_type` |
| `[119:88]` | `price` (signed) |
| `[87:56]` | `qty` |
| `[55:48]` | `reason_code` |
| `[47:16]` | `timestamp` |
| `[15:0]` | `checksum` |

Reason-code encoding on the wire is intentionally compact for host consumers:

- `0`: no action
- `1`: buy candidate approved
- `2`: sell candidate approved
- `3`: blocked by risk or other gate

The 16-bit checksum is the XOR of the seven 16-bit words in bits `[127:16]`.

## Example

A BUY action at price `104`, quantity `4`, reason `1`, timestamp `12` is encoded by placing each field in the fixed slices above and computing the checksum over the full payload. The Python golden model exposes `encode_output_frame()` and `decode_output_frame()` so tests can assert the same field-level interpretation that software will use.
