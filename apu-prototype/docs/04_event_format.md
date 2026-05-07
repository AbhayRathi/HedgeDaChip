# Event format

The MVP uses one 128-bit beat per event.

## `event_t` bit mapping

| Bits | Field |
| --- | --- |
| `[7:0]` | `event_type` |
| `[8]` | `side` (`0=bid`, `1=ask`) |
| `[40:9]` | `price` (signed fixed-point placeholder) |
| `[72:41]` | `qty` |
| `[104:73]` | `ts` |
| `[127:105]` | `flags` |

Event types:

- `0`: NOP
- `1`: ADD
- `2`: CANCEL
- `3`: TRADE
- `4`: UPDATE

## `feature_t`

- best bid price / qty
- best ask price / qty
- spread
- imbalance (`bid_qty - ask_qty`)
- last trade price / qty

## `action_t`

| Bits | Field |
| --- | --- |
| `[7:0]` | `action_type` |
| `[39:8]` | `price` |
| `[71:40]` | `qty` |
| `[79:72]` | `reason_code` |
| `[127:80]` | reserved |
