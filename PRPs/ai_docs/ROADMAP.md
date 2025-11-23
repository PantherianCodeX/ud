# Vertical-Slice-First Development Roadmap

This roadmap outlines a **vertical-slice-first** approach for the legal intake SaaS platform. We prioritize an end-to-end pipeline (**intake → analyze → compose**) early on, with robust infrastructure and observability from day one. Non-essential features (full UI, admin tools) are deferred until the core workflow is stable. Each phase below represents a milestone with specific priorities, deliverables, and notes on code structure.

---

## Phase 1: Core Infrastructure Setup (Foundation)

### Project Structure (Vertical Slice Architecture)

Initialize the codebase defined in PRPs/ARCHITECTURE.md, organized by **feature domains** rather than technical layers. [1] For example:

```text
src/
  core/        # Cross-cutting modules (db connection, auth, config, logging)
  workflow/
    intake/    # Domain logic for intake (e.g. Azure Speech stub, intake models)
    analysis/  # Domain logic for analysis (LLM orchestration with LangGraph)
    compose/   # Domain logic for output generation (templates, formatting)
    ...        # (Additional slices can be added according to PRPs/ARCHITECTURE.md)
  tests/e2e/   # (E2E test cases)
```

This vertical slice setup ensures each feature encapsulates its own logic end-to-end, reducing cross-module coupling.[1] Core services like database and auth live in `core/` for reuse.

**IMPORTANT** use the tree structures defined in PRPs/ARCHITECURE.md when initializing the repo structure.

### Baseline Modules

Implement foundational modules:

* **Database**
  Set up a PG database (and ORM/models if applicable) to store structured analyses and results. Include migration/seed scripts if needed. Keep it minimal (e.g., a table for cases/analyses) until use-cases expand.

* **Auth**
  Scaffold an authentication module (e.g. JWT or OAuth) in `core/auth`. At this stage it can be a stub or simple user model, since user management isn’t the focus yet.

* **Config Management**
  Establish a configuration system (using environment variables or a config file) to handle keys (e.g. Azure, LLM API keys) and environment-specific settings.

### CI/CD Pipeline

Set up **continuous integration** from the start:

* Configure automated testing, linting, and build on each commit.
* Use GitHub Actions (or similar) to run:

  * Test suites
  * Static analysis
  * Type checks (if applicable)

Early CI/CD hygiene ensures code quality and enables rapid, confident iteration.

### Observability Groundwork

Begin with basic logging and monitoring setup:

* Integrate a **structured logging** library for consistent logs across services (in `core/logging`). Include correlation IDs or request IDs if possible. Will be integrated with structlog.
* Plan for tracing:

  * Incorporate **OpenTelemetry** or similar so that later you can tie into **Langfuse** easily.[2]
  * At minimum, ensure the project can emit trace/span events (even if just to console or a local collector for now).
* If using **LangSmith** from LangChain:

  * Install it and verify you can log a simple trace (e.g. a dummy LLM call) to the LangSmith UI.
  * Full use will come later, but having it available now saves time.

### Dev Environment

* Containerize the app or set up **docker-compose** if multiple services are anticipated.
* Ensure new developers or CI can spin up the whole system easily.
* Include scripts for local setup (e.g., `make dev` to run tests and start services).

### Milestone Deliverable (Phase 1)

A repository with:

* Clear **vertical-slice architecture**
* Core scaffolding in place
* CI pipelines running on push
* The app building and passing a basic test (e.g., a health-check endpoint)

The team has a foundation to implement features without needing to redesign infrastructure.

---

## Phase 2: Pipeline Bootstrapping (Vertical Slice Prototype)

### Implement Core Intake → Analyze → Compose Flow

Develop a thin vertical slice of the primary workflow, stitching together the **intake interview processing** to **one output**:

* **Intake**

  * Create a service in `workflow/intake` to accept raw interview input.
  * For now, **mock the Azure Speech** component:

    * Assume the input is already transcribed text, or
    * Use a simple placeholder function that returns a fixed transcript for a given audio file.
  * This lets development proceed without external dependencies.

* **Analyze**

  * In `workflow/analysis`, integrate an LLM to transform the intake into structured data.

  * Leverage **LangGraph** to define this as a small agent/workflow graph rather than a monolithic function.[3]

    * Example steps:

      * Parse interview text
      * Extract key facts
      * Call an LLM for classification

  * Using LangGraph from the start ensures the pipeline can grow in complexity (multiple steps, conditionals) without refactoring.[3]

  * Use **LangChain/LangSmith** integration here to start capturing trace data:

    * Enable LangSmith tracing on this LLM call so you can see each step under the hood (inputs, outputs).[4]
    * This helps debug the chain logic early.

  * For LLM calls, consider using **Portkey AI** as a local LLM gateway:

    * Point the LLM API calls to Portkey’s local endpoint (with a dev API key) to simplify switching models and to enable local testing without real API calls.[5]
    * Portkey can route to a small local model for fast tests, and adds retry/fallback logic out-of-the-box.

* **Compose**

  * In `workflow/compose`, implement generation of **one primary output** from the structured analysis.
  * For example, produce:

    * A summary report, or
    * A draft legal memo based on the analysis data.
  * This could involve:

    * A templating step, or
    * An additional LLM prompt (e.g. “Given these structured facts, draft a 1-page summary”).
  * Keep it simple initially:

    * One output format
    * Minimal styling

### End-to-End Integration

Wire the above stages together in a single workflow:

* Create a high-level function (or LangGraph root node) that:

  * Takes an intake ID or input
  * Calls the intake (transcription stub)
  * Passes text to analysis
  * Passes structured data to the composer
  * Returns the final output
* Ensure this can be invoked easily:

  * CLI command, or
  * Temporary API endpoint like `POST /processInterview` for testing
* Verify the vertical slice manually:

  * Input a sample interview (e.g., a text paragraph simulating an interview)
  * Receive the generated output
  * This proves the concept end-to-end.

### Observability Touchpoints

Even in this prototype, use the observability tools:

* Ensure **LangSmith** is recording the LLM call trace (check the dashboard for the request).
* Log key events:

  * When intake starts/ends
  * When analysis is done
  * Include timing info
* If **Langfuse** is already set up:

  * Send a test trace to Langfuse
  * For example, log the input and output of the LLM call via Langfuse’s SDK
  * Langfuse can capture inputs, outputs, and metadata like latency.[2]
  * Seeing a trace of the whole pipeline in Langfuse now will validate your instrumentation approach.

### Quality Notes

Since speed is a goal but quality must remain high, treat this slice as a prototype to refine:

* Write a couple of basic tests:

  * Feed a known input
  * Assert the output contains certain expected fields or phrases
* Code review this slice thoroughly, as it will set patterns for future slices.

### Milestone Deliverable (Phase 2)

A **working vertical slice** of the core pipeline:

* You can run a sample interview through the system
* You get a structured result and one output, all automated
* The pipeline uses the LangChain/LangGraph stack for orchestration
* It logs/traces its behavior (with LangSmith traces, etc.)

This validates the architecture and allows the team to proceed with confidence.

---

## Phase 3: Observability & CI/CD Enhancements (Shoring Up Quality)

### Full Observability Integration

Now that the basic pipeline works, invest in robust observability **before** adding more features (shifting observability left in development).[6]

* **Langfuse**

  * Integrate the Langfuse SDK deeply.
  * Instrument each stage of the pipeline to send trace events to Langfuse (self-hosted or cloud).
  * For each processed interview, ensure Langfuse captures:

    * Transcription (stub) input
    * LLM call details (prompt, response)
    * Output composition result
    * Timing and any errors
  * This gives a single-pane view of the pipeline’s internal behavior and performance.[2]

* **LangSmith**

  * Continue using LangSmith for:

    * Development traces
    * Prompt debugging
  * Start using LangSmith’s evaluation features (if available) to:

    * Score or review outputs
    * Log final outputs and later evaluate them against expectations
    * Support human review via the UI

* **Logging & Metrics**

  * Augment logging to be **production-grade**:

    * Use structlog to ease filtering.
    * Include contextual metadata (user ID, case ID, etc. if available) in log entries.
    * Add performance metrics:

      * Total pipeline execution time
      * LLM token usage
    * Feed these into monitoring dashboards or alerts (e.g., if analysis is taking too long or costs spike).
  * Consider an APM solution or ensure OpenTelemetry spans can be exported:

    * Langfuse is built on OpenTelemetry, which helps integrate with other monitoring.[7]

* **Alerts & Error Handling**

  * Set up basic alerting for critical failures:

    * If an analysis step throws an exception, log it and maybe send a notification (email/Slack) to developers.
  * Define retry logic or fallback behaviors for external calls:

    * If the LLM call fails or times out, retry or return a controlled error.

### CI/CD Maturity

Expand the CI pipeline to catch issues early:

* **Automated Testing**

  * Develop a more comprehensive test suite now that core logic is defined.
  * Include unit tests for non-trivial logic (text parsing, data structuring, etc.).
  * Add integration tests that run the whole pipeline with simulated inputs:

    * Use a fake LLM via Portkey AI or a small model for fast tests.
  * Test both happy paths and failure scenarios (e.g., LLM returns unexpected output).

* **Continuous Deployment**

  * Configure a **staging deployment** for each merge:

    * Automatically deploy main-branch builds to a staging environment.
    * Connect observability tools (Langfuse/LangSmith) to staging.

* **Code Quality**

  * Add linting rules and type checking (TypeScript or Python type hints).
  * Integrate static security scans, since this app handles legal data.

### Performance Check

With observability in place, use Langfuse and logs to assess baseline performance:

* How long does the pipeline take per case?
* What’s the token usage?
* Use this data to inform scaling decisions later.
* If obvious bottlenecks appear (e.g., slow LLM calls), note them but delay heavy optimizations until features are complete, unless trivial.

### Milestone Deliverable (Phase 3)

A **highly observable and reliable** core pipeline:

* Full visibility into behavior (tracing, metrics)
* Safety net of tests and CI checks
* Problems found and fixed early[6]
* Pipeline is essentially production-ready in terms of quality (though not feature-complete)

---

## Phase 4: Feature Expansion & Pipeline Hardening

### Multiple Output Types (Vertical Slice Iterations)

With the core pipeline solid, implement additional outputs the platform needs, one by one, as new vertical slices:

* Treat each new output or analysis feature as its own mini-project. Examples:

  * Client letter
  * Legal brief
  * Internal risk assessment

For each:

* Add necessary logic in `workflow/compose` (or a new domain if appropriate) to generate that output from the structured analysis:

  * New prompts (possibly via LangGraph)
  * New templates
* Reuse existing analysis data as much as possible:

  * Store structured analysis in the database
  * Pass it to each generator to avoid repeating analysis work
* Maintain modularity:

  * If outputs are complex, create subfolders or separate modules per output type.
  * This aligns with vertical slice architecture by feature.
* Update tests:

  * Ensure each output generates correctly for known inputs.
  * Verify via LangSmith/Langfuse that new steps are traced and logged properly.

These increments should be done rapidly but carefully. With observability and CI in place, you can:

* Add an output
* Run tests
* Inspect traces
* Confirm it works and doesn’t break existing functionality

### Real Azure Speech Integration

Replace the intake stub with the real **Azure Cognitive Services Speech API**:

* Implement a service (or use Azure SDK) in `workflow/intake` that:

  * Takes an audio file
  * Calls Azure’s Speech-to-Text
  * Returns the transcript
* Ensure it runs **asynchronously** if needed:

  * Speech recognition may be slow for long interviews.
  * Integrate a job queue:

    * Web request stores the file and enqueues a job.
    * Worker service pulls the job, calls Azure, and continues the pipeline.
* Consider Portkey if it supports Azure OpenAI endpoints, but Azure Speech is often separate.
* Handle API keys securely.
* Implement error handling (e.g., transcription failures).

Update the pipeline flow:

* Use real Azure Speech in production mode.
* Retain stub for dev/testing (e.g., via environment flag).
* This allows local testing without constant Azure calls.

### Pipeline Robustness

As features expand, reinforce robustness and scalability:

* **Background Workers**

  * Move heavy **analysis & compose** steps to a background worker service:

    * Frontend (Phase 5) calls an API to start processing.
    * Heavy LLM work happens in a separate process to avoid request timeouts.
  * Use a message broker or task queue:

    * RabbitMQ
    * Celery
    * Azure Service Bus
  * This is where you introduce practical **multi-service architecture**:

    * “Processing worker” separate from “web API”
    * Keep domain logic sharable (same code used by worker and synchronous paths).

* **Caching & Reuse**

  * Only run analysis once per interview:

    * Store results in DB for reuse across multiple outputs.
  * Avoid repeated LLM calls when unnecessary.

* **Error Handling**

  * One failing output generation should not crash the whole pipeline.
  * Consider **partial success**:

    * Some outputs return successfully
    * Others fail and are flagged for review

* **Security**

  * With real data and external calls, double-check:

    * Logs/traces don’t leak sensitive data
    * Access to Langfuse/LangSmith data is secured
    * Encryption and secrets management are in place

### Folder Structure & Code Organization

With more features and possibly more services, update documentation:

* If you add a new microservice `registry`, it might live under `ai/registry/`, reusing code via a shared library or DB.

* `workflow/compose` might have subfolders or files per output:

  ```text
  compose/summary.ts
  compose/clientLetter.ts
  ...
  ```

* Document in the README how everything is modularized by feature so new contributors can onboard quickly.

### Milestone Deliverable (Phase 4)

The platform’s **feature set is complete**:

* All intended outputs from an intake interview are generated by the pipeline.
* The core workflow handles **real audio input** via Azure Speech.
* The system may now include multiple processes/services but retains clear domain-driven structure.
* Each new feature has been delivered with:

  * Tests
  * Observability
  * Proper error handling

---

## Phase 5: Minimal User Interface (Next.js Frontend & API Layer)

### Next.js Frontend Kickoff

With a stable backend, build the user-facing component:

* Set up a **Next.js** project (if not already).
* This will be the SaaS web application where legal professionals or clients:

  * Upload interviews
  * View results

Start with core functionality:

* **Interview Page**

  * Form to upload an audio file (or record via microphone)
  * Submit button to initiate processing

* **Results Page**

  * Displays structured analysis findings
  * Shows sections or links for each generated output:

    * Summary
    * Letter
    * Brief
    * Etc.

Use React components to organize UI, but avoid excessive polish initially—focus on correctness.

### API Integration

Design a clean API between frontend and backend:

* If backend is separate:

  * Create an endpoint, e.g., `POST /api/interviews`:

    * Accepts file or reference
    * Returns an identifier (`interview_id`)
  * Frontend then polls:

    * `GET /api/interviews/{id}` for status and results
    * Or uses WebSockets / SSE if you want live updates later.

* Ensure **authentication**:

  * Use JWT or session cookies so only authorized users can:

    * Submit interviews
    * View data
  * Integrate auth module:

    * Next.js login page obtains a token
    * Token attached to API calls
    * Backend verifies token (e.g., middleware in `core/auth`)

### User Experience for Long-Running Processes

LLM analysis may take time, especially for:

* Multiple outputs
* Long interviews

Implement:

* **Processing state** UI:

  * Show “Processing…” after submission
  * Optionally show finer-grained statuses:

    * “Transcribing audio…”
    * “Analyzing interview…”
    * “Generating reports…”
  * Backend can expose status from pipeline (e.g., LangGraph stage info)

* Polling or push:

  * Simple polling is fine for v1
  * Later you can move to WebSockets or SSE

### CI/CD for Frontend

Extend CI/CD:

* Build and test steps for Next.js:

  * Lint the code
  * Run unit tests (if applicable)
* Optional preview deployments:

  * Vercel, Netlify, or static previews per PR
* Environment configuration:

  * Manage API base URLs, keys, etc. via:

    * `.env` files
    * Platform-specific env settings

### Milestone Deliverable (Phase 5)

A **functional web application** for the main use case:

* Users can log in
* Submit an interview
* Receive generated outputs via a simple interface
* Frontend is minimal but sufficient
* Communicates securely with backend

This is your **end-to-end user-facing MVP**.

---

## Phase 6: Admin Tools and Final Polishing

### Admin & Internal Tools

Now address internal-facing features postponed earlier:

Build an **admin dashboard** (could be a section in the Next.js app, behind admin role) with features like:

* Viewing a list of all intake cases:

  * Statuses
  * Timestamps
* Re-running or adjusting outputs:

  * E.g., if an output had an error, admins can trigger regeneration
* User management (if needed):

  * View users
  * Reset passwords
  * Manage roles
* Monitoring metrics:

  * Aggregated data from Langfuse or custom logs, e.g.:

    * Analyses per day
    * Average processing time

Implement incrementally:

* Start with the simplest necessary views (e.g., case list and status)
* Add advanced actions and reports over time

### Fine-Tune Observability for Production

Before (or as) you go to production, ensure top-notch observability and reliability:

* **Alerts & Dashboards**

  * Set up dashboards for production metrics:

    * Use Langfuse alerting for:

      * Model usage anomalies
      * Cost spikes[8]
    * Integrate with APMs to:

      * Alert on error rates
      * High latency

* **SLOs**

  * Define Service Level Objectives for critical flows, e.g.:

    * “90% of interviews processed in < X minutes”
  * Monitor them with appropriate tooling.[9]

* **Security Audit**

  * Since legal data is sensitive, verify:

    * TLS everywhere
    * Database encryption at rest (if applicable)
    * Secure storage of API keys (vaults, secrets management)
    * Observability data (logs, traces) is handled safely (no PII leaks where inappropriate)

* **LLM Guardrails**

  * If not already in place, add safeguards:

    * Prompt templates that reduce risk
    * Optional content filters

### Performance & Scaling

Do a round of performance testing:

* Simulate higher load:

  * Concurrent interview processing
* Identify bottlenecks:

  * Increase worker processes or instances
  * Move to more robust queues if needed
* Optimize:

  * Chunk or parallelize Azure Speech if it’s slow
  * Use cheaper models or caching when possible for repeated queries
* Confirm you can handle expected peak loads:

  * Make a scaling plan (vertical scaling, horizontal scaling, both)

### UX and UI Enhancements

With core functionality complete, polish UX:

* Improve design and accessibility:

  * Styling
  * Better form validations
  * Clear instructions for users
* Consider adding:

  * Ability to edit transcribed text before analysis

    * Improves output quality
    * Easier now that pipeline is stable
  * Download links or PDF exports for generated documents
* Write user-facing documentation, onboarding guides, and help content.

### Deployment Ready

Set up **production deployment workflows**:

* Configure infrastructure:

  * Cloud services
  * Containers
  * Databases
  * Use Infrastructure as Code where possible (Terraform, etc.)
* Implement deployment strategies:

  * Blue-green deployments
  * Canary releases
  * Feature flags for progressive rollout
* Ensure **rollback** procedures are in place.

### Milestone Deliverable (Phase 6)

A **production-ready platform**, fully featured and polished:

* All core scenarios handled
* Tools for both users and admins
* System is observable, secure, and scalable
* Development team can move into:

  * Maintenance
  * Iterative improvements
  * Experimentation

---

## Conclusion

Throughout this roadmap, the guiding principle is delivering value in **vertical slices** – completing thin end-to-end features – rather than building broad technical layers in isolation. This approach, combined with early observability and CI/CD, ensures rapid development without sacrificing quality.[10] [4]

By the time of full launch:

* The core pipeline (**intake → analyze → compose**) has been **battle-tested**.
* Supporting infrastructure is in place:

  * LangGraph orchestration[3]
  * Langfuse tracing[2]
  * Portkey-managed LLM calls[5]
* The result is a reliable, scalable service ready for real-world legal teams.

---

## References

[1] Vertical Slice Architecture | DevIQ
[https://deviq.com/architecture/vertical-slice-architecture/](https://deviq.com/architecture/vertical-slice-architecture/)

[2] LLM Observability & Application Tracing (open source) - Langfuse
[https://langfuse.com/docs/observability/overview](https://langfuse.com/docs/observability/overview)

[3] What is LangGraph? | IBM
[https://www.ibm.com/think/topics/langgraph](https://www.ibm.com/think/topics/langgraph)

[4] Finally figured out the LangChain vs LangGraph vs LangSmith confusion - here's what I learned : r/Rag
[https://www.reddit.com/r/Rag/comments/1mxs81z/finally_figured_out_the_langchain_vs_langgraph_vs/](https://www.reddit.com/r/Rag/comments/1mxs81z/finally_figured_out_the_langchain_vs_langgraph_vs/)

[5] Supercharging Open-source LLMs: Your Gateway to 250+ Models
[https://portkey.ai/blog/gateway-to-open-source-models/](https://portkey.ai/blog/gateway-to-open-source-models/)

[6] The Power of Observability During Development | Honeycomb
[https://www.honeycomb.io/blog/power-observability-during-development](https://www.honeycomb.io/blog/power-observability-during-development)

[7] LLM Observability & Application Tracing (open source) - Langfuse (OpenTelemetry context)
[https://langfuse.com/docs/observability/overview](https://langfuse.com/docs/observability/overview)

[8] LLM Observability & Application Tracing (open source) - Langfuse (Alerts & costs)
[https://langfuse.com/docs/observability/overview](https://langfuse.com/docs/observability/overview)

[9] The Power of Observability During Development | Honeycomb (SLOs)
[https://www.honeycomb.io/blog/power-observability-during-development](https://www.honeycomb.io/blog/power-observability-during-development)

[10] The Power of Observability During Development | Honeycomb (development velocity)
[https://www.honeycomb.io/blog/power-observability-during-development](https://www.honeycomb.io/blog/power-observability-during-development)

```text
::contentReference[oaicite:0]{index=0}
```
