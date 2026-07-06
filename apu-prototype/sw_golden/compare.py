from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Iterable, Sequence


class GoldenComparator:
    def compare_fields(
        self,
        actual: Sequence[object],
        expected: Sequence[object],
        fields: Sequence[str],
        *,
        input_events: Sequence[object] | None = None,
        label: str = 'sequence',
    ) -> dict:
        mismatches: list[dict] = []
        max_len = max(len(actual), len(expected))
        for index in range(max_len):
            if index >= len(actual) or index >= len(expected):
                mismatches.append(
                    {
                        'index': index,
                        'field': '__length__',
                        'expected': self._serialize(expected[index]) if index < len(expected) else None,
                        'actual': self._serialize(actual[index]) if index < len(actual) else None,
                        'input_event': self._serialize(input_events[index]) if input_events and index < len(input_events) else None,
                    }
                )
                continue
            actual_item = actual[index]
            expected_item = expected[index]
            for field in fields:
                actual_value = self._field(actual_item, field)
                expected_value = self._field(expected_item, field)
                if actual_value != expected_value:
                    mismatches.append(
                        {
                            'index': index,
                            'field': field,
                            'expected': expected_value,
                            'actual': actual_value,
                            'input_event': self._serialize(input_events[index]) if input_events and index < len(input_events) else None,
                        }
                    )
        return {'pass': not mismatches, 'label': label, 'mismatches': mismatches}

    def compare_actions(self, actual: Sequence[object], expected: Sequence[object], *, input_events: Sequence[object] | None = None) -> dict:
        return self.compare_fields(actual, expected, ['action_type', 'price', 'qty', 'reason_code', 'timestamp'], input_events=input_events, label='actions')

    def compare_events(self, actual: Sequence[object], expected: Sequence[object], *, input_events: Sequence[object] | None = None) -> dict:
        return self.compare_fields(actual, expected, ['event_type', 'side', 'price', 'qty', 'ts', 'flags'], input_events=input_events, label='events')

    def compare_features(self, actual: Sequence[object], expected: Sequence[object], *, input_events: Sequence[object] | None = None) -> dict:
        return self.compare_fields(
            actual,
            expected,
            ['best_bid_price', 'best_bid_qty', 'best_ask_price', 'best_ask_qty', 'spread', 'imbalance', 'last_trade_price', 'last_trade_qty', 'event_ts'],
            input_events=input_events,
            label='features',
        )

    def format_report(self, report: dict) -> str:
        if report['pass']:
            return f"{report['label']} matched golden model"
        lines = [f"{report['label']} mismatches ({len(report['mismatches'])})"]
        for mismatch in report['mismatches']:
            lines.append(
                f"idx={mismatch['index']} field={mismatch['field']} expected={mismatch['expected']} actual={mismatch['actual']} input={mismatch['input_event']}"
            )
        return '\\n'.join(lines)

    def _field(self, value: object, field: str):
        if is_dataclass(value):
            return getattr(value, field)
        if isinstance(value, dict):
            return value[field]
        return getattr(value, field)

    def _serialize(self, value: object):
        if value is None:
            return None
        if is_dataclass(value):
            return asdict(value)
        if isinstance(value, dict):
            return value
        if isinstance(value, (str, int, float, bool)):
            return value
        return repr(value)
