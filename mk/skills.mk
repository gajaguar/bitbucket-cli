LANG_CHECK_TARGETS += skills-validate

##@ Skills

skills-validate: ## Validate skills/*/SKILL.md against the Agent Skills spec
	@for skill in skills/*/; do \
		$(UV) run agentskills validate "$$skill" || exit 1; \
	done

.PHONY: skills-validate
