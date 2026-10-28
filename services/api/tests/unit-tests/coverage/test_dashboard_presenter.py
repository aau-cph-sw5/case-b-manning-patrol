from datetime import UTC, datetime, timedelta

from src.api.v2.schemas.dashboard import DashboardArea, DashboardStation
from src.db.models import Station
from src.domain.patrol_area import AreaKind
from src.services.station_coverage.dashboard_presenter import DashboardPresenter

SENT_AT = datetime(2026, 9, 21, 10, 15, tzinfo=UTC)


def test_present_maps_a_station_to_the_contract(station_report, dashboard_presenter):
    last_covered_at = SENT_AT - timedelta(minutes=20)
    report = station_report(
        "kongens-nytorv",
        covered_now=False,
        as_of=SENT_AT,
        last_covered_at=last_covered_at,
    )

    dashboard = dashboard_presenter.present([report], sent_at=SENT_AT)

    assert dashboard.stations == [
        DashboardStation(
            station_id="kongens-nytorv",
            name="Kongens Nytorv",
            areas=[
                DashboardArea(
                    area_id="platform-1",
                    name="Platform",
                    line=["M1", "M2"],
                    area_type=AreaKind.PLATFORM,
                    covered_now=False,
                    overdue_at=last_covered_at + timedelta(minutes=60),
                )
            ],
        )
    ]


def test_present_stamps_the_send_time_and_has_no_trains(
    station_report, dashboard_presenter
):
    report = station_report(
        "marmorkirken", covered_now=True, as_of=SENT_AT, last_covered_at=SENT_AT
    )

    dashboard = dashboard_presenter.present([report], sent_at=SENT_AT)

    assert dashboard.time == SENT_AT
    assert dashboard.trains == []


def test_area_has_no_deadline_while_covered_now(station_report, dashboard_presenter):
    report = station_report(
        "marmorkirken", covered_now=True, as_of=SENT_AT, last_covered_at=SENT_AT
    )

    dashboard = dashboard_presenter.present([report], sent_at=SENT_AT)

    area = dashboard.stations[0].areas[0]
    assert area.covered_now is True
    assert area.overdue_at is None


def test_station_without_lines_gets_an_empty_line_list(station_report):
    presenter = DashboardPresenter(
        stations=[Station(id="marmorkirken", name="Marmorkirken")],
        station_lines=[],
    )
    report = station_report(
        "marmorkirken", covered_now=True, as_of=SENT_AT, last_covered_at=SENT_AT
    )

    dashboard = presenter.present([report], sent_at=SENT_AT)

    assert dashboard.stations[0].areas[0].line == []
