start:
	docker compose up -d streamlit data_loader
	uvicorn agent.main:app --host 0.0.0.0 --port ${AGENT_PORT} --reload

stop:
	docker compose down --remove-orphans
	@echo "Stopping uvicorn on port ${AGENT_PORT}..."
	@PID=$$(lsof -ti tcp:${AGENT_PORT}); \
	if [ -n "$$PID" ]; then \
		kill $$PID; \
		echo "✅ Uvicorn (PID $$PID) stopped."; \
	else \
		echo "⚠️ No process found on port ${AGENT_PORT}."; \
	fi
