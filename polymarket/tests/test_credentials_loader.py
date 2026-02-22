from pathlib import Path

from polymarket_core.adapters.credentials import load_polymarket_credentials


def test_credentials_loader_supports_live_fields(tmp_path: Path) -> None:
    credentials_file = tmp_path / "credential.txt"
    credentials_file.write_text(
        "\n".join(
            [
                "POLYMARKET_API_KEY=test-key",
                "POLYMARKET_API_SECRET=test-secret",
                "POLYMARKET_API_PASSPHRASE=test-passphrase",
                "POLYMARKET_PRIVATE_KEY=test-private-key",
                "POLYMARKET_FUNDER=0xabc",
            ]
        ),
        encoding="utf-8",
    )
    credentials = load_polymarket_credentials(str(credentials_file))
    assert credentials is not None
    assert credentials.private_key == "test-private-key"
    assert credentials.funder == "0xabc"

