from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, List

from .apu_params import (
    BASE_QTY,
    DEFAULT_IMBALANCE_THRESHOLD,
    DEFAULT_MAX_ORDERS_PER_WINDOW,
    DEFAULT_WINDOW_CYCLES,
    DEFAULT_SPREAD_THRESHOLD,
    MAX_QTY,
    MIN_QTY,
)

EVENT_NOP = 0
EVENT_ADD = 1
EVENT_CANCEL = 2
EVENT_TRADE = 3
EVENT_UPDATE = 4

ACTION_NONE = 0
ACTION_BUY = 1
ACTION_SELL = 2
ACTION_CANCEL = 3

REASON_KILL = 0x10
REASON_QTY = 0x11
REASON_PRICE = 0x12
REASON_RATE = 0x13

OUTPUT_REASON_NONE = 0
OUTPUT_REASON_BUY = 1
OUTPUT_REASON_SELL = 2
OUTPUT_REASON_BLOCKED = 3


@dataclass(eq=True)
class Event:
    event_type: int
    side: int
    price: int
    qty: int
    ts: int = 0
    flags: int = 0


@dataclass(eq=True)
class Feature:
    best_bid_price: int = 0
    best_bid_qty: int = 0
    best_ask_price: int = 0
    best_ask_qty: int = 0
    spread: int = 0
    imbalance: int = 0
    last_trade_price: int = 0
    last_trade_qty: int = 0
    event_ts: int = 0


@dataclass(eq=True)
class Action:
    action_type: int = ACTION_NONE
    price: int = 0
    qty: int = 0
    reason_code: int = 0
    timestamp: int = 0


@dataclass(eq=True)
class OutputFrame:
    action_type: int = ACTION_NONE
    price: int = 0
    qty: int = 0
    reason_code: int = OUTPUT_REASON_NONE
    timestamp: int = 0
    checksum: int = 0


def to_u32(value: int) -> int:
    return value & 0xFFFF_FFFF


def to_s32(value: int) -> int:
    value &= 0xFFFF_FFFF
    return value if value < 0x8000_0000 else value - 0x1_0000_0000


def encode_event_frame(event: Event) -> int:
    frame = 0
    frame |= event.event_type & 0xFF
    frame |= (event.side & 0x1) << 8
    frame |= to_u32(event.price) << 9
    frame |= to_u32(event.qty) << 41
    frame |= to_u32(event.ts) << 73
    frame |= (event.flags & ((1 << 23) - 1)) << 105
    return frame


def parse_event_frame(frame: int) -> Event:
    event_type = frame & 0xFF
    side = (frame >> 8) & 0x1
    price = to_s32((frame >> 9) & 0xFFFF_FFFF)
    qty = (frame >> 41) & 0xFFFF_FFFF
    ts = (frame >> 73) & 0xFFFF_FFFF
    flags = (frame >> 105) & ((1 << 23) - 1)
    if event_type > EVENT_UPDATE:
        event_type = EVENT_NOP
        flags |= 0x1
    return Event(event_type, side, price, qty, ts, flags)


def encode_feature(feature: Feature) -> int:
    value = 0
    fields = [
        feature.best_bid_price,
        feature.best_bid_qty,
        feature.best_ask_price,
        feature.best_ask_qty,
        feature.spread,
        feature.imbalance,
        feature.last_trade_price,
        feature.last_trade_qty,
        feature.event_ts,
    ]
    for index, field in enumerate(fields):
        value |= to_u32(field) << (32 * index)
    return value


def decode_feature(value: int) -> Feature:
    return Feature(
        best_bid_price=to_s32((value >> 0) & 0xFFFF_FFFF),
        best_bid_qty=(value >> 32) & 0xFFFF_FFFF,
        best_ask_price=to_s32((value >> 64) & 0xFFFF_FFFF),
        best_ask_qty=(value >> 96) & 0xFFFF_FFFF,
        spread=to_s32((value >> 128) & 0xFFFF_FFFF),
        imbalance=to_s32((value >> 160) & 0xFFFF_FFFF),
        last_trade_price=to_s32((value >> 192) & 0xFFFF_FFFF),
        last_trade_qty=(value >> 224) & 0xFFFF_FFFF,
        event_ts=(value >> 256) & 0xFFFF_FFFF,
    )


def encode_action(action: Action) -> int:
    value = 0
    value |= action.action_type & 0xFF
    value |= to_u32(action.price) << 8
    value |= to_u32(action.qty) << 40
    value |= (action.reason_code & 0xFF) << 72
    value |= to_u32(action.timestamp) << 80
    return value


def decode_action(value: int) -> Action:
    return Action(
        action_type=value & 0xFF,
        price=to_s32((value >> 8) & 0xFFFF_FFFF),
        qty=(value >> 40) & 0xFFFF_FFFF,
        reason_code=(value >> 72) & 0xFF,
        timestamp=(value >> 80) & 0xFFFF_FFFF,
    )


def output_reason_code(action: Action) -> int:
    if action.action_type == ACTION_BUY:
        return OUTPUT_REASON_BUY
    if action.action_type == ACTION_SELL:
        return OUTPUT_REASON_SELL
    if action.reason_code != 0:
        return OUTPUT_REASON_BLOCKED
    return OUTPUT_REASON_NONE


def output_checksum_from_payload(payload: int) -> int:
    checksum = 0
    for shift in range(16, 128, 16):
        checksum ^= (payload >> shift) & 0xFFFF
    return checksum & 0xFFFF


def encode_output_frame(action: Action) -> int:
    timestamp = action.timestamp
    value = 0
    value |= (action.action_type & 0xFF) << 120
    value |= to_u32(action.price) << 88
    value |= to_u32(action.qty) << 56
    value |= (output_reason_code(action) & 0xFF) << 48
    value |= to_u32(timestamp) << 16
    value |= output_checksum_from_payload(value)
    return value


def decode_output_frame(bits: int) -> OutputFrame:
    return OutputFrame(
        action_type=(bits >> 120) & 0xFF,
        price=to_s32((bits >> 88) & 0xFFFF_FFFF),
        qty=(bits >> 56) & 0xFFFF_FFFF,
        reason_code=(bits >> 48) & 0xFF,
        timestamp=(bits >> 16) & 0xFFFF_FFFF,
        checksum=bits & 0xFFFF,
    )


class OrderBookModel:
    def __init__(self) -> None:
        self.best_bid_price = 0
        self.best_bid_qty = 0
        self.best_ask_price = 0
        self.best_ask_qty = 0
        self.last_trade_price = 0
        self.last_trade_qty = 0

    def apply(self, event: Event) -> Feature:
        if event.event_type in (EVENT_ADD, EVENT_UPDATE):
            if event.side == 0:
                if self.best_bid_qty == 0 or event.price >= self.best_bid_price:
                    self.best_bid_price = max(event.price, self.best_bid_price)
                    self.best_bid_qty = event.qty
            else:
                if self.best_ask_qty == 0 or min(event.price, self.best_ask_price) == event.price:
                    self.best_ask_price = min(event.price, self.best_ask_price)
                    self.best_ask_qty = event.qty
        elif event.event_type in (EVENT_CANCEL, EVENT_TRADE):
            if event.side == 0 and event.price == self.best_bid_price:
                if event.qty >= self.best_bid_qty:
                    self.best_bid_price = 0
                    self.best_bid_qty = 0
                else:
                    self.best_bid_qty -= event.qty
            if event.side == 1 and event.price == self.best_ask_price:
                if event.qty >= self.best_ask_qty:
                    self.best_ask_price = 0
                    self.best_ask_qty = 0
                else:
                    self.best_ask_qty -= event.qty
            if event.event_type == EVENT_TRADE:
                self.last_trade_price = event.price
                self.last_trade_qty = event.qty
        has_valid_spread = self.best_bid_qty and self.best_ask_qty and self.best_ask_price >= self.best_bid_price
        spread = self.best_ask_price - self.best_bid_price if has_valid_spread else 0
        imbalance = self.best_bid_qty - self.best_ask_qty
        return Feature(
            best_bid_price=self.best_bid_price,
            best_bid_qty=self.best_bid_qty,
            best_ask_price=self.best_ask_price,
            best_ask_qty=self.best_ask_qty,
            spread=spread,
            imbalance=imbalance,
            last_trade_price=self.last_trade_price,
            last_trade_qty=self.last_trade_qty,
            event_ts=event.ts,
        )


def compute_order_qty(feature: Feature, imbalance_threshold: int = DEFAULT_IMBALANCE_THRESHOLD) -> int:
    spread_scale = feature.spread if feature.spread > 0 else 1
    imbalance_mag = abs(feature.imbalance)
    threshold_mag = abs(imbalance_threshold)
    imbalance_ratio = 0 if imbalance_mag < threshold_mag else imbalance_mag // spread_scale
    qty = imbalance_ratio * BASE_QTY
    return max(MIN_QTY, min(MAX_QTY, qty))


def decision_model(
    feature: Feature,
    spread_threshold: int = DEFAULT_SPREAD_THRESHOLD,
    imbalance_threshold: int = DEFAULT_IMBALANCE_THRESHOLD,
) -> Action:
    action = Action(timestamp=feature.event_ts)
    if feature.best_bid_qty and feature.best_ask_qty and feature.spread > spread_threshold:
        if feature.imbalance >= imbalance_threshold:
            return Action(ACTION_BUY, feature.best_ask_price, compute_order_qty(feature, imbalance_threshold), 1, feature.event_ts)
        if feature.imbalance <= -imbalance_threshold:
            return Action(ACTION_SELL, feature.best_bid_price, compute_order_qty(feature, imbalance_threshold), 2, feature.event_ts)
    return action


class RiskModel:
    def __init__(self, max_orders_per_window: int = DEFAULT_MAX_ORDERS_PER_WINDOW, window_cycles: int = DEFAULT_WINDOW_CYCLES) -> None:
        self.max_orders_per_window = max_orders_per_window
        self.window_cycles = window_cycles
        self.window_counter = 0
        self.orders_in_window = 0

    def step(self, action: Action, hard_block: bool = False) -> Action:
        if self.window_counter == self.window_cycles - 1:
            self.window_counter = 0
            self.orders_in_window = 0
        else:
            self.window_counter += 1
        effective_orders = self.orders_in_window
        if action.action_type == ACTION_NONE:
            return action
        if hard_block:
            return Action(reason_code=REASON_KILL, timestamp=action.timestamp)
        if action.qty == 0:
            return Action(reason_code=REASON_QTY, timestamp=action.timestamp)
        if action.price == 0:
            return Action(reason_code=REASON_PRICE, timestamp=action.timestamp)
        if effective_orders >= self.max_orders_per_window:
            return Action(reason_code=REASON_RATE, timestamp=action.timestamp)
        self.orders_in_window = effective_orders + 1
        return action


def end_to_end_model(
    events: Iterable[Event],
    spread_threshold: int = DEFAULT_SPREAD_THRESHOLD,
    imbalance_threshold: int = DEFAULT_IMBALANCE_THRESHOLD,
    max_orders_per_window: int = DEFAULT_MAX_ORDERS_PER_WINDOW,
    hard_block: bool = False,
) -> List[Action]:
    book = OrderBookModel()
    risk = RiskModel(max_orders_per_window)
    actions: List[Action] = []
    for event in events:
        parsed = parse_event_frame(encode_event_frame(event))
        feature = book.apply(parsed)
        candidate = decision_model(feature, spread_threshold, imbalance_threshold)
        actions.append(risk.step(candidate, hard_block=hard_block))
    return actions


def dataclass_to_dict(value: object) -> dict:
    return asdict(value)
