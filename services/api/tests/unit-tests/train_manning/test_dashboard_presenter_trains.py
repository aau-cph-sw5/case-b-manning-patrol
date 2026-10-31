from datetime import UTC, datetime, timedelta
from uuid import UUID

from src.api.v2.schemas.dashboard import DashboardTrain
from src.domain.train_manning import TrainManningReport, TrainReference
from src.services.station_coverage.dashboard_presenter import DashboardPresenter

SENT_AT = datetime(2026, 9, 21, 10, 15, tzinfo=UTC)
TRAIN_ID = UUID("10000000-0000-0000-0000-000000000001")
BEACON = UUID("00000000-0000-0000-0000-00000000a001")
STEWARD_A = UUID("b80fdb46-0666-41e8-883c-0d0bda93f835")
STEWARD_B = UUID("c91fec57-1777-52f9-994d-1e1ceb04a946")


def make_presenter() -> DashboardPresenter:
    return DashboardPresenter(stations=[], station_lines=[])


def make_report(
    *,
    stewards: frozenset[UUID] = frozenset(),
    line_ids: frozenset[str] = frozenset({"M2", "M1"}),
    running: timedelta = timedelta(hours=12),
    manned: timedelta = timedelta(hours=3),
) -> TrainManningReport:
    return TrainManningReport(
        train=TrainReference(
            id=TRAIN_ID, slug="a29", beacon_id=BEACON, line_ids=line_ids
        ),
        running_time=running,
        manned_time=manned,
        manned_now=bool(stewards),
        current_steward_ids=stewards,
        as_of=SENT_AT,
    )


def test_present_maps_a_train_to_the_contract():
    presenter = make_presenter()

    dashboard = presenter.to_dashboard([], [make_report()], sent_at=SENT_AT)

    assert dashboard.trains == [
        DashboardTrain(
            id=TRAIN_ID,
            slug="a29",
            total_time_secs=12 * 3600,
            manned_time_secs=3 * 3600,
            current_steward_ids=[],
            line=["M1", "M2"],
        )
    ]


def test_unmanned_train_has_empty_current_steward_ids():
    presenter = make_presenter()

    dashboard = presenter.to_dashboard([], [make_report()], sent_at=SENT_AT)

    assert dashboard.trains[0].current_steward_ids == []


def test_manned_train_exposes_the_current_steward():
    presenter = make_presenter()

    dashboard = presenter.to_dashboard(
        [], [make_report(stewards=frozenset({STEWARD_A}))], sent_at=SENT_AT
    )

    assert dashboard.trains[0].current_steward_ids == [STEWARD_A]


def test_multiple_current_stewards_are_all_listed():
    presenter = make_presenter()

    dashboard = presenter.to_dashboard(
        [],
        [make_report(stewards=frozenset({STEWARD_B, STEWARD_A}))],
        sent_at=SENT_AT,
    )

    assert dashboard.trains[0].current_steward_ids == sorted([STEWARD_A, STEWARD_B])


def test_train_payload_has_exactly_the_contract_fields():
    presenter = make_presenter()

    dashboard = presenter.to_dashboard([], [make_report()], sent_at=SENT_AT)
    payload = dashboard.model_dump(mode="json")

    assert set(payload["trains"][0]) == {
        "id",
        "slug",
        "total_time_secs",
        "manned_time_secs",
        "current_steward_ids",
        "line",
    }


def test_present_keeps_stations_and_trains_together():
    presenter = make_presenter()

    dashboard = presenter.to_dashboard([], [make_report()], sent_at=SENT_AT)

    assert dashboard.stations == []
    assert len(dashboard.trains) == 1
    assert dashboard.time == SENT_AT
