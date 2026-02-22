from polymarket_core.config import PipelineConfig
from polymarket_core.web.dashboard import create_app


def main() -> None:
    app = create_app(PipelineConfig(force_real_data=True))
    app.run(host="127.0.0.1", port=5080, debug=False)


if __name__ == "__main__":
    main()

