import manning_patrol_backend


def test_package_imports() -> None:
    assert callable(manning_patrol_backend.main)


def test_main_runs(capsys) -> None:
    manning_patrol_backend.main()
    captured = capsys.readouterr()
    assert "Hello from manning-patrol-backend!" in captured.out
