.PHONY: promql-doc grafana-dashboard grafana-vllm-dashboard grafana-integrated-dashboard grafana-log-dashboard assets
promql-doc:
	python3 scripts/build_promql_doc.py

grafana-dashboard:
	python3 scripts/build_grafana_gpu_dashboard.py

grafana-vllm-dashboard:
	python3 scripts/build_grafana_vllm_dashboard.py

grafana-integrated-dashboard:
	python3 scripts/build_grafana_integrated_dashboard.py

grafana-log-dashboard:
	python3 scripts/build_grafana_log_dashboard.py

assets: promql-doc grafana-dashboard grafana-vllm-dashboard grafana-integrated-dashboard grafana-log-dashboard
