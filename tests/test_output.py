from app.output import (
    CompositeOutputAdapter,
    DeliveryResult,
    OutputEnvelope,
    OutputEventStore,
    StoreOutputAdapter,
)


class _FailingAdapter:
    def emit(self, envelope: OutputEnvelope) -> DeliveryResult:
        del envelope
        return DeliveryResult(ok=False, backend="failed", error="no audio")


def _event(title: str = "喝水") -> OutputEnvelope:
    return OutputEnvelope(
        event_type="reminder.triggered",
        persona_id="persona-1",
        display_text=f"提醒已觸發：{title}",
        speech_text=f"提醒您，現在該{title}了。",
        source_id="reminder-1",
    )


def test_event_store_assigns_monotonic_ids_and_supports_after_id() -> None:
    store = OutputEventStore(max_events=3)
    store.append(_event("A"))
    store.append(_event("B"))
    store.append(_event("C"))

    all_events = store.list()
    assert [event.event_id for event in all_events] == [1, 2, 3]
    assert [event.display_text for event in store.list(after_id=1)] == [
        "提醒已觸發：B",
        "提醒已觸發：C",
    ]


def test_composite_delivery_succeeds_when_store_succeeds_but_audio_fails() -> None:
    store = OutputEventStore()
    adapter = CompositeOutputAdapter(StoreOutputAdapter(store), _FailingAdapter())

    result = adapter.emit(_event())

    assert result.ok is True
    assert "event_store" in result.backend
    assert "failed" in result.backend
    assert result.error == "failed: no audio"
    assert len(store.list()) == 1
