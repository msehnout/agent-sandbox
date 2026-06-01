.PHONY: format-code lint fix type-check check help

help:                ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

format-code:         ## Auto-format the code
	uv run ruff format .

lint:                ## Lint without modifying files
	uv run ruff check .

fix:                 ## Lint and apply safe autofixes
	uv run ruff check --fix .

type-check:          ## Static type checking
	uv run ty check

check: lint type-check   ## Run ruff lint + type-check together
