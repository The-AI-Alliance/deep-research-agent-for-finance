
pages_url       := https://the-ai-alliance.github.io/deep-research-agent-for-finance/
docs_dir        := docs
site_dir        := ${docs_dir}/_site
clean_code_dirs := logs output src/output ${src_dir}/.hypothesis
clean_doc_dirs  := ${site_dir} ${docs_dir}/.sass-cache
clean_dirs      := ${clean_code_dirs} ${clean_doc_dirs}
src_dir         := src
app_dir         := finance_deep_search

## Environment variables
MAKEFLAGS           ?= # -w --warn-undefined-variables
MAKEFLAGS_RECURSIVE ?= # --print-directory (only useful for recursive makes...)
UNAME               ?= $(shell uname)
ARCHITECTURE        ?= $(shell uname -m)

## App defaults
# Hack: on the command line, use `make APP_ARGS='--foo bar' target` to pass other 
# command-line arguments, e.g., '--help', to commands executed when building targets
# that run the app command.

MAIN_APP                   ?= main_finance.py
TICKER                     ?= META
COMPANY_NAME               ?= Meta Platforms, Inc.
REPORTING_CURRENCY         ?= USD
RESEARCH_MODEL             ?= gpt-4o
EXCEL_WRITER_MODEL         ?= o4-mini
INFERENCE_PROVIDER         ?= openai
TEMPLATES_DIR              ?= ${app_dir}/templates
FIN_RESEARCH_PROMPT_FILE   ?= financial_research_agent.md
EXCEL_WRITER_PROMPT_FILE   ?= excel_writer_agent.md
MARKDOWN_YAML_HEADER_FILE  ?= github_pages_header.yaml
OUTPUT_DIR                 ?= ${PWD}/output/${TICKER}
OUTPUT_REPORT              ?= ${TICKER}_report.md
OUTPUT_SPREADSHEET         ?= ${TICKER}_financials.xlsx
TEMPERATURE                ?= 0.7
MAX_ITERATIONS             ?= 25
# Might be expensive on some inference services!
MAX_TOKENS                 ?= 500000
MAX_COST_DOLLARS           ?= 2.0
MAX_TIME_MINUTES           ?= 15
UX                         ?= rich
APP_ARGS                   ?=

# Override when running `make view-local` using e.g., `JEKYLL_PORT=8000 make view-local`
JEKYLL_PORT         ?= 4000

# Used for version tagging release artifacts.
GIT_HASH            ?= $(shell git show --pretty="%H" --abbrev-commit |head -1)
NOW                 ?= $(shell date +"%Y%m%d-%H%M%S")

## Define messages

define help_message
Quick help for this make process

Targets for the application:

make all                # Run the application by building "app-run".
make app-run            # Run the application with default arguments.
make app-run-rich       # Run the application with the Rich console UI (also the default).
make app-run-md         # Run the application with the streaming Markdown "UI".
make app-run-markdown   # Same as "make app-run-md".
make app-help           # Run the application with --help to see the support arguments.
                        # Also prints the default invocation used by "app-run".
make app-setup          # One-time setup of the application dependences.
make test               # Run the automated tests. ("make tests" is a synonym...)

Targets for the GitHub pages documentation:

make view-pages         # View the published GitHub pages in a browser.
make view-local         # View the pages locally. Makes 'setup-jekyll' and 'run-jekyll'.
                        # Tip: "JEKYLL_PORT=8000 make view-local" uses port 8000 instead of 4000.
make run-jekyll         # Used by "view-local"; assumes everything is already setup.
                        # Tip: "JEKYLL_PORT=8000 make run-jekyll" uses port 8000 instead of 4000.
make setup-jekyll       # Install Jekyll. Ruby 3.X must be installed already. 
                        # Only needed once for local viewing of the document.

Miscellaneous make targets for help, debugging, etc.:

make help               # Prints this output.
make print-info         # Print all the current values of some make and env. variables.
make print-app-info     # Print just the values related to the app.
make print-make-info    # Print just the values related to make, etc.
make print-docs-info    # Print just the values related to the GitHub Pages docs.
make clean_code         # Deletes these directories: ${clean_code_dirs}
make clean_docs         # Deletes these directories: ${clean_docs_dirs}
make clean              # Deletes these directories: ${clean_dirs}
endef

define app_help_footer
TIPS:
1. Use 'make print-app-info' to see some make variables you can override.
2. Use 'make --just-print app-run' to see the arguments passed BY THIS MAKEFILE.
   Some argument values will be different in the Makefile than the hard-coded defaults
   in the application itself, which are shown in the help output above!!
3. To pass additional arguments, use 'make APP_ARGS="..." app-run'. (Note the quotes.)
endef		

define missing_uv_message
ERROR: The Python dependency manager \'uv\' is used. Please visit https://docs.astral.sh/uv/ to install it.
endef

define missing_mcp_agent_message
ERROR: The Python dependency \'mcp-agent\' is not installed. Either run \'make app-setup\' or \'uv add mcp-agent\'.
endef
foo:
	@echo ${missing_mcp_agent_message}

ifndef docs_dir
$(error ERROR: There is no ${docs_dir} directory!)
endif

define gem-error-message

ERROR: Did the gem command fail with a message like this?
ERROR: 	 "You don't have write permissions for the /Library/Ruby/Gems/2.6.0 directory."
ERROR: To run the "gem install ..." command for the MacOS default ruby installation requires "sudo".
ERROR: Instead, use Homebrew (https://brew.sh) to install ruby and make sure "/usr/local/.../bin/gem"
ERROR: is on your PATH before "user/bin/gem".
ERROR:
ERROR: Or did the gem command fail with a message like this?
ERROR:   Bundler found conflicting requirements for the RubyGems version:
ERROR:     In Gemfile:
ERROR:       foo-bar (>= 3.0.0) was resolved to 3.0.0, which depends on
ERROR:         RubyGems (>= 3.3.22)
ERROR:   
ERROR:     Current RubyGems version:
ERROR:       RubyGems (= 3.3.11)
ERROR: In this case, try "brew upgrade ruby" to get a newer version.

endef

define bundle-error-message

ERROR: Did the bundle command fail with a message like this?
ERROR: 	 "/usr/local/opt/ruby/bin/bundle:25:in `load': cannot load such file -- /usr/local/lib/ruby/gems/3.1.0/gems/bundler-X.Y.Z/exe/bundle (LoadError)"
ERROR: Check that the /usr/local/lib/ruby/gems/3.1.0/gems/bundler-X.Y.Z directory actually exists. 
ERROR: If not, try running the clean-jekyll command first:
ERROR:   make clean-jekyll setup-jekyll
ERROR: Answer "y" (yes) to the prompts and ignore any warnings that you can't uninstall a "default" gem.

endef

define ruby_installation_message
See ruby-lang.org for installation instructions.
endef

## Define targets

.PHONY: all view-pages view-local clean clean_code clean_docs help 
.PHONY: setup-jekyll run-jekyll
.PHONY: app-run app-run-rich app-run-md app-run-markdown do-app-run app-setup app-check uv-check uv-cmd-check venv-check
.PHONY: mcp-agent-check test tests
.PHONY: print-info print-app-info print-make-info print-docs-info show-output-files

all:: app-run

app-run-md app-run-markdown:: 
	$(MAKE) UX=markdown app-run
app-run-rich:: app-run
app-run:: app-check do-app-run show-output-files
do-app-run::
	cd ${src_dir} && uv run ${MAIN_APP} \
		--ticker "${TICKER}" \
		--company-name "${COMPANY_NAME}" \
		--output-dir "${OUTPUT_DIR}" \
		--markdown-report "${OUTPUT_REPORT}" \
		--markdown-yaml-header "${MARKDOWN_YAML_HEADER_FILE}" \
		--output-spreadsheet "${OUTPUT_SPREADSHEET}" \
		--reporting-currency "${REPORTING_CURRENCY}" \
		--templates-dir "${TEMPLATES_DIR}" \
		--financial-research-prompt-path "${FIN_RESEARCH_PROMPT_FILE}" \
		--excel-writer-agent-prompt-path "${EXCEL_WRITER_PROMPT_FILE}" \
		--research-model "${RESEARCH_MODEL}" \
		--excel-writer-model "${EXCEL_WRITER_MODEL}" \
		--provider "${INFERENCE_PROVIDER}" \
		--temperature ${TEMPERATURE} \
		--max-iterations ${MAX_ITERATIONS} \
		--max-tokens ${MAX_TOKENS} \
		--max-cost-dollars ${MAX_COST_DOLLARS} \
		--max-time-minutes ${MAX_TIME_MINUTES} \
		--verbose \
		--ux ${UX} \
		${APP_ARGS}
show-output-files::
	@echo
	@echo "Output files in ${OUTPUT_DIR}:"
	@cd ${OUTPUT_DIR} && find . -type f -exec ls -lh {} \;

test tests:: uv-check
	cd ${src_dir} && uv run python -m unittest discover

app-check:: uv-check mcp-agent-check

uv-check:: uv-cmd-check venv-check
uv-cmd-check::
	@command -v uv > /dev/null || ( echo ${missing_uv_message} && exit 1 )
venv-check::
	[[ -d .venv ]] || uv venv

mcp-agent-check::
	@uv pip freeze | grep mcp-agent > /dev/null || ( echo ${missing_mcp_agent_message} && exit 1 )

app-setup:: uv-check venv-check
	uv add mcp-agent

.PHONY: app-help app-help-prefix app-help-footer

app-help:: app-help-prefix app-help-footer
app-help-prefix::
	@echo "Application help provided by ${src_dir}/${app_dir}/${MAIN_APP}:"
	cd ${src_dir} && uv run ${MAIN_APP} --help
	@echo
app-help-footer::
	$(info ${app_help_footer})
	@echo

help::
	$(info ${help_message})
	@echo
	@echo "Run make app-help for more help on running the app."
	@echo

print-info: print-app-info print-make-info print-docs-info
print-app-info:
	@echo "Company:"
	@echo "  TICKER                   ${TICKER}"
	@echo "  COMPANY_NAME             ${COMPANY_NAME}"
	@echo "  REPORTING_CURRENCY       ${REPORTING_CURRENCY}"
	@echo "Models:"
	@echo "  RESEARCH_MODEL           ${RESEARCH_MODEL}"
	@echo "  EXCEL_WRITER_MODEL       ${EXCEL_WRITER_MODEL}"
	@echo "Templates (for prompts, etc.):"
	@echo "  TEMPLATES_DIR            ${TEMPLATES_DIR}"
	@echo "  FIN_RESEARCH_PROMPT_FILE ${FIN_RESEARCH_PROMPT_FILE}"
	@echo "  EXCEL_WRITER_PROMPT_FILE ${EXCEL_WRITER_PROMPT_FILE}"
	@echo "OUTPUT_DIR                ${OUTPUT_DIR}"
	@echo "  OUTPUT_REPORT            ${OUTPUT_REPORT} (under OUTPUT_DIR)"
	@echo "  OUTPUT_SPREADSHEET       ${OUTPUT_SPREADSHEET} (under OUTPUT_DIR)"
	@echo "APP_ARGS                   ${APP_ARGS}"
	@echo

print-make-info:
	@echo "MAKEFLAGS:                 ${MAKEFLAGS}"
	@echo "MAKEFLAGS_RECURSIVE:       ${MAKEFLAGS_RECURSIVE}"
	@echo "JEKYLL_PORT:               ${JEKYLL_PORT}"
	@echo "UNAME:                     ${UNAME}"
	@echo "ARCHITECTURE:              ${ARCHITECTURE}"
	@echo "GIT_HASH:                  ${GIT_HASH}"
	@echo "NOW:                       ${NOW}"
	@echo "clean code directories:    ${clean_code_dirs} (deleted by 'make clean_code')"
	@echo "clean docs directories:    ${clean_docs_dirs} (deleted by 'make clean_docs')"
	@echo "clean directories:         ${clean_dirs} (deleted by 'make clean')"
	@echo

print-docs-info:
	@echo "For the GitHub Pages website:"
	@echo "  GitHub Pages URL:        ${pages_url}"
	@echo "  docs dir:                ${docs_dir}"
	@echo "  site dir:                ${site_dir}"
	@echo


clean_code:: clean_code clean_docs
clean_code::
	rm -rf ${clean_code_dirs} 
clean_docs::
	rm -rf ${clean_docs_dirs} 


## The rest of this Makefile is for running the GitHub Pages documentation 
## website locally for testing and proofreading.

view-pages::
	@uname | grep -q Darwin && open ${pages_url} || \
		(echo "I could not open the GitHub Pages URL myself. Try ⌘-click or ^-click on this URL, or copy and paste it into a browser:" && \
		echo "  ${pages_url}")

view-local:: setup-jekyll run-jekyll

# Passing --baseurl '' allows us to use `localhost:4000` rather than require
# `localhost:4000/The-AI-Alliance/REPO_NAME` when running locally.
run-jekyll: clean
	@echo
	@echo "Once you see the http://127.0.0.1:${JEKYLL_PORT}/ URL printed, open it with command+click..."
	@echo
	cd ${docs_dir} && \
		bundle exec jekyll serve --port ${JEKYLL_PORT} --baseurl '' --incremental || \
		${MAKE} jekyll-error

setup-jekyll:: ruby-installed-check ruby-gem-installation bundle-command-check bundle-installation

.PHONY: ruby-installed-check ruby-gem-installation bundle-command-check bundle-installation
.PHONY: jekyll-error ruby-missing-error gem-missing-error gem-error bundle-error bundle-missing-error

ruby-gem-installation::
	@echo "Updating Ruby gems required for local viewing of the docs, including jekyll."
	gem install jekyll bundler jemoji || ${MAKE} gem-error

bundle-installation::
	bundle install || ${MAKE} bundle-error
	bundle update html-pipeline || ${MAKE} bundle-error

ruby-installed-check:
	@command -v ruby > /dev/null || ${MAKE} ruby-missing-error
	@command -v gem  > /dev/null || ${MAKE} gem-missing-error

bundle-command-check:
	@command -v bundle > /dev/null || \
		${MAKE} bundle-missing-error 

# NOTE: We call make to run these %-error targets, because if you try
# some_command || $(error "didn't work"), the $(error ...) function is always
# invoked, independent of the shell script logic. Hence, the only way to make
# this invocation conditional is to use a make target invocation, as shown above.
jekyll-error:
	$(error "ERROR: Failed to run Jekyll. Try running 'make setup-jekyll'.")
ruby-missing-error:
	$(error "ERROR: 'ruby' is required. ${ruby_installation_message}")
gem-missing-error:
	$(error "ERROR: Ruby's 'gem' is required. ${ruby_installation_message}")
gem-error:
	$(error ${gem-error-message})
bundle-error:
	$(error ${bundle-error-message})
bundle-missing-error:
	$(error "ERROR: Ruby gem command 'bundle' is required. I tried 'gem install bundle', but it apparently didn't work!")
