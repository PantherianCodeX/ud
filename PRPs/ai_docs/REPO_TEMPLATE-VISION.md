# Repo Template - Vertical Monorepo

Purpose: Provide example to follow when creating an expandable monorepo
combining the best of both vertical architecture and monorepo architecture
to get an efficient blend of both approaches.

Many teams pick the hybrid approach for:

- Top-level: `apps/api`, `apps/web`, `apps/worker` (clean deployables, clean language boundaries).
- Inside each app: `features/<slice>/…` (vertical per app).
- Shared stuff under `packages/` / `shared/`.

---

## 1. Apps vs Features

**Apps** = deployable things:

- `apps/api` – FastAPI backend (HTTP API)
- `apps/worker` – Celery workers / async jobs
- `apps/web` – Next.js SaaS frontend
- `apps/mobile` – React Native / Expo app (later)

**Features (vertical slices)** live *inside* those apps, in a `features/` tree, and are mirrored where it makes sense (api/web/mobile).

Absolute top-level (monorepo-ish) view:

```text
.
├─ apps/
│   ├─ api/             # backend
│   ├─ worker/          # async jobs
│   ├─ web/             # Next.js frontend
│   ├─ admin/           # Streamlit / Next.js / Budibase dashboards/config
│   └─ mobile/          # Mobile client
│
├─ packages/
│   ├─ py-domain/       # shared Python domain models (matters, policy, references…)
│   ├─ py-ai-core/      # LangGraph wrappers, Portkey, registry helpers
│   ├─ ts-api-types/    # shared OpenAPI/SDK types for web/mobile
│   ├─ ts-ui-kit/       # shared React components (buttons, layout)
│   └─ ts-utils/        # tiny generic helpers (keep this small)
│
├─ infra/
├─ ops/
├─ configs/
├─ docs/
├─ tests/e2e/
└─ typings/

```

---

## 2. Bounded contexts

Here are several capabilities grouped into a few **domains**:

1. **Core Workflow**

   - `intake` (upload/transcribe)
   - `analysis` (MatterAnalysis LangGraph)
   - `compose` (summaries/briefs/actions)
   - `matters` (matter lifecycle, parties, etc.)

2. **Governance & Knowledge**

   - `reference_data` – court metadata, forms, statutes, org docs
   - `policy_engine` – OPA bundle generation & evaluation
   - `localization` – jurisdiction/locale-aware logic; court rules per region (NOT basic UI i18n; that stays in Next.js config)

3. **AI Platform**

   - `registry` – providers, models, regions, capabilities (LLM, speech, embeddings, etc.)
   - `assistants` – ai chatbots and “copilot” style flows
   - `llm_evals` – evaluation/eval jobs (LangSmith datasets + Langfuse scores)

4. **Platform & Org**

   - `auth` – login, tenants, RBAC hooks
   - `settings` – org/user/tenant settings (feature flags, defaults, thresholds)
   - `billing` (later)
   - `teams` / `orgs` (later)

5. **Engagement**

   - `notifications` – email/SMS/in-app, webhooks
   - `communications` – conversation logs, email threads, message templates, etc. (if you want this separate)

Each of those is a **slice**, and we *only* add a top-level slice when it’s a real product area, not a little helper.

---

## 3. What the backend will look like with all that

Inside `apps/api`, with vertical feature groups + a tiny `core/`:

```text
apps/api/
  src/
    core/
      config.py
      db.py
      security.py
      tracing.py
      opa_client.py      # thin wrapper for talking to OPA sidecar if used
      mailer.py          # low-level email client, used by notifications
      ...

    workflow/
      intake/
        api.py          # POST /intakes, upload audio, start pipeline
        service.py      # orchestrates: store file, enqueue transcription
        models.py       # Pydantic schemas for Intake, Transcript stub
        repository.py
        tests/

      analysis/
        api.py          # POST /matters/{id}/analyze
        graph.py        # Analyze LangGraph definition
        service.py      # wraps LangGraph, LangSmith/Langfuse integration
        models.py       # MatterAnalysis, entities, issues, timeline, actions
        repository.py
        tests/

      compose/
        api.py          # POST /matters/{id}/compose
        graph.py        # Compose LangGraph (uses MatterAnalysis)
        templates.py    # prompt templates, output structuring
        service.py
        repository.py
        tests/

      matters/
        api.py          # CRUD, linking transcripts to matters
        models.py
        repository.py
        tests/

    governance/
      reference_data/
        api.py          # CRUD / sync for courts, forms, statutes
        ingesters.py    # loaders for external sources (CSV, APIs, etc.)
        models.py       # Court, CourtForm, Regulation, SourceReference...
        repository.py
        tests/

      policy_engine/
        api.py          # endpoints to preview/test policies, dry-run decisions
        bundler.py      # generates OPA bundles from reference_data + org rules
        compiler.py     # compiles Rego, validates bundles
        evaluator.py    # high-level "should we allow X" wrapper, calls OPA
        models.py       # Policy, Rule, DecisionLog...
        repository.py
        tests/

      localization/
        api.py          # maybe admin endpoints: define jurisdictions/locales
        service.py      # "given tenant + court, pick correct locale/rules"
        models.py       # LocaleConfig, Jurisdiction, CourtLocaleMapping...
        repository.py
        tests/

    ai/
      registry/
        api.py          # Configure providers/models per tenant
        service.py      # selects provider/model, resolves keys (Portkey)
        models.py       # Provider, ModelConfig, Capability (llm, stt, embeddings)
        repository.py
        tests/

      assistants/
        api.py          # /chat, /assistants/{id}/messages
        flows.py        # multi-turn flows using LangGraph
        routers.py      # conversation routing (e.g. which assistant to use)
        models.py       # ChatSession, Message, ToolCall, etc.
        repository.py
        tests/

      llm_evals/
        api.py          # trigger eval runs, list eval results
        service.py      # glue LangSmith datasets + eval jobs
        models.py
        repository.py
        tests/

    platform/
      auth/
        api.py          # login/logout, token refresh, user info
        service.py      # integration with Keycloak / OIDC
        models.py
        repository.py
        tests/

      settings/
        api.py          # GET/PUT org & user settings
        service.py      # hierarchical resolution: defaults → org → user
        models.py       # Setting, SettingScope, FeatureFlag...
        repository.py
        tests/

    engagement/
      notifications/
        api.py          # list notification prefs, maybe send-test
        service.py      # schedule notifications, topic abstraction
        models.py       # NotificationTemplate, DeliveryChannel, EventSubscription...
        repository.py
        tests/

      communications/
        api.py          # log inbound/outbound messages, threads
        service.py      # email sending, reply handling, link to matters
        models.py
        repository.py
        tests/
  tests/
    integration/        # cross-feature integration tests within backend boundary
      test_full_matter_pipeline.py      # hits /intakes, /matters, /analyze, /compose
      test_policy_decision_flow.py      # reference_data + policy_engine + OPA
      test_ai_registry_resolution.py    # registry + analysis using Portkey client
```

---

## 4. Worker: same features, no extra bloat

`apps/worker` reuses the same domain code but only cares about background jobs:

```text
apps/worker/
  src/
    core/
      config.py
      db.py
      tracing.py
      celery_app.py
    workflow/
      intake/
        tasks.py        # async audio → transcript → enqueue analysis
      analysis/
        tasks.py        # run Analyze LangGraph in background
      compose/
        tasks.py        # generate outputs
      ...
    governance/  
      policy_engine/
        tasks.py        # rebuild OPA bundles on schedule
      ...
    ai/
      llm_evals/
        tasks.py        # scheduled eval jobs
      ...
    engagement/
      notifications/
        tasks.py        # send queued notifications (email/SMS/push)
      ...
    ...
```

Each worker `tasks.py` just wraps the same `service.py` from `apps/api` or shared `packages/py-domain` to avoid duplication.

---

## 5. Frontend and mobile: mirrored slices, grouped not sprayed

For `apps/web`, we mirror the main slices, but regroup into fewer top-level “domains” to keep navigation sane:

```text
apps/web/
  src/
    app/
      intake/
        page.tsx              # /intake
      matters/
        [matterId]/
          page.tsx            # /matters/:id
      policy/
        page.tsx              # /policy (admin / OPA inspection)
      settings/
        page.tsx              # /settings
      admin/
        page.tsx              # superadmin stuff
      chat/
        page.tsx              # /chat (assistants)
      notifications/
        page.tsx              # /notifications (user inbox)
      ...

    shared/
      ui/                     # generic UI kit
      lib/                    # generic utilities
      config/
        env.ts
        routes.ts
        i18n.ts               # Next.js locale / next-intl setup

    workflow/
      intake/
        components/
          IntakeForm.tsx
          IntakeUpload.tsx
        api/
          useCreateIntake.ts
          useIntakeStatus.ts
        tests/

      analysis/
        components/
          AnalysisTimeline.tsx
          PartiesIssuesPanel.tsx
        api/
          useAnalysis.ts
          useRunAnalysis.ts
        tests/

      compose/
        components/
          ClientSummaryView.tsx
          LawyerBriefView.tsx
        api/
          useCompose.ts
        tests/

      matters/
        components/
          MattersList.tsx
          MatterDetail.tsx
        api/
          useMatters.ts
        tests/

    governance/
      reference_data/
        components/
          CourtsTable.tsx
          FormsTable.tsx
        api/
          useCourts.ts
          useForms.ts
        tests/

      policy_engine/
        components/
          PolicyList.tsx
          PolicyDecisionLog.tsx
        api/
          usePolicies.ts
          useDryRunDecision.ts
        tests/

      localization/
        components/
          LocaleMatrix.tsx
        api/
          useLocales.ts
        tests/

    ai/
      registry/
        components/
          ProviderList.tsx
          ModelConfigForm.tsx
        api/
          useProviders.ts
          useModels.ts
        tests/

      assistants/
        components/
          ChatWindow.tsx
          SuggestedQuestions.tsx
        api/
          useChatSession.ts
        tests/

    platform/
      settings/
        components/
          OrgSettingsForm.tsx
          UserSettingsForm.tsx
        api/
          useOrgSettings.ts
          useUserSettings.ts
        tests/

    engagement/
      notifications/
        components/
          NotificationList.tsx
        api/
          useNotifications.ts
        tests/
  tests/
    integration/                # cross-feature integration tests
      IntakePage.test.tsx       # mounts /intake page, checks overall flow with mocked API
      MatterDetailPage.test.tsx
```

For **mobile** (`apps/mobile`), we repeat only what matters to that client (intake, matters, chat, notifications), with the same feature names, reusing `ts-api-types` for typing.

---

## 6. Testing (E2E) & Typings

```text
tests/
  e2e/
    playwright.config.ts
    helpers/
      auth.ts
      seed.ts
    specs/
      intake_to_analysis.e2e.spec.ts
      policy_admin.e2e.spec.ts
      chatbot_matter_assistant.e2e.spec.ts
typings/
  third_party/
    portkey/
      __init__.pyi
      client.pyi
    opa_client/
      __init__.pyi
```

---

## 7. Avoiding folder bloat: rules of thumb

Here’s how we keep it from exploding:

1. **Promote only “big rocks”:**
   New *top-level* feature folder (`<group>/foo`) only if:

   - It has its own API endpoints **and**
   - It has meaningful domain logic and/or data models **and**
   - It will likely show up in the UI as a visible capability (page/section).

   A “helper that formats Rego strings” lives in `policy_engine/utils.py`, not `governance/rego_formatter`.

2. **Shared code goes in packages, not “god folders”.**

   - OPA helpers? → `packages/py-domain` or `packages/py-policy-core`, then used by `policy_engine`.
   - AI provider adapters? → `packages/py-ai-core`.
   - Generic React components? → `packages/ts-ui-kit`.

   This stops `core/` from turning into a junk drawer.

3. **Tests live next to features** (like your original example).
   That’s more directories, but they’re predictable: when you open `governance/policy_engine/`, you see code + tests together. Editors collapse `tests/` easily, so it doesn’t feel bloated.

4. **Limit depth to ~3–4 levels.**
   e.g., `governance/policy_engine/bundler.py` is okay.
   `governance/policy_engine/bundles/generators/v2/forms/alberta/*` is… not. Deeper taxonomy is handled in code & DB, not in folders.

5. **Consistent naming across apps.**
   Same slice names in backend, worker, web, mobile. That mental map matters more than shaving one folder.

---

## 8. How adding a new thing actually feels

- “We need AI chatbots” → add `assistants/` slice:

  - Backend: `engagement/assistants/{api.py, flows.py, models.py, repository.py, tests/}`
  - Web: `engagement/assistants/{components/, api/, tests/}`
  - (Optionally mobile: `engagement/assistants/` screens and hooks)

- “We want to onboard a new LLM provider” → no new slice:

  - Update `ai/registry` data + maybe `py-ai-core` adapters.
  - The rest of the system just sees a new provider option.

- “We need to ingest a new court’s forms” → no new slice:

  - Add a new ingester in `reference_data/ingesters.py`.
  - Optionally a bit of UI in `governance/reference_data` to trigger it or show stats.

- “We need SMS notifications” → no new slice:

  - Add an SMS channel implementation in `notifications/service.py` + some config in `settings`.

Everything is either:

- A **new feature slice** (big rock), or
- A **new file inside an existing slice**, or
- A **change to a shared package**.

So the tree grows, but in **chunky, predictable blocks**, not a flat sea of micro-features.
