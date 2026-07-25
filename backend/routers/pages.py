from fastapi import APIRouter
from backend.handlers.pages_handler import _make_handler

router = APIRouter(include_in_schema=False, tags=["pages"])

_DASHBOARD_PAGES = [
    ("/", "index.html", "home"),
    ("/Dashboard", "FrontEnd/Dashboard/dashboard.html", "dashboard"),
    ("/Dataset-Explorer", "FrontEnd/Dashboard/dataset-explorer.html", "dataset_explorer"),
    ("/Network-Traffic", "FrontEnd/Dashboard/network-traffic.html", "network_traffic"),
    ("/Prediction-Timeline", "FrontEnd/Dashboard/prediction-timeline.html", "prediction_timeline"),
    ("/Research-Metrics", "FrontEnd/Dashboard/research-metrics.html", "research_metrics"),
    ("/Settings", "FrontEnd/Dashboard/settings.html", "settings"),
    ("/Threat-Intelligence", "FrontEnd/Dashboard/threat-intelligence.html", "threat_intelligence"),
    ("/XAI-Dashboard", "FrontEnd/Dashboard/xai-dashboard.html", "xai_dashboard"),
    ("/Architecture", "FrontEnd/research/architecture.html", "architecture"),
    ("/Contributions", "FrontEnd/research/contributions.html", "contributions"),
    ("/Experiment-Results", "FrontEnd/research/experimental-results.html", "experiment_results"),
    ("/Methodology", "FrontEnd/research/methodology.html", "methodology"),
    ("/Research-Paper", "FrontEnd/research/research-paper.html", "research_paper"),
    ("/AI", "FrontEnd/Dashboard/ai.html", "ai"),
]


for _path, _template, _name in _DASHBOARD_PAGES:
    router.add_api_route(
        path=_path,
        endpoint=_make_handler(_template),
        methods=["GET"],
        name=_name,
    )
