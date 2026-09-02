import { PREPARED_SCENARIOS } from "../src/preparedDemo.js";

const APP_NAME = "Byzantium AutoClaims";

export function GET() {
  const checks = {
    runtime: true,
    preparedExperience:
      PREPARED_SCENARIOS.length > 0 &&
      PREPARED_SCENARIOS.every(
        (scenario) =>
          scenario.analysis &&
          scenario.receipt &&
          Array.isArray(scenario.pipeline_events) &&
          scenario.pipeline_events.length > 0,
      ),
  };
  const healthy = Object.values(checks).every(Boolean);

  return Response.json(
    {
      contractVersion: 1,
      status: healthy ? "ok" : "error",
      app: APP_NAME,
      checks,
      capabilities: {
        liveBackendConfigured: Boolean(process.env.VITE_API_URL),
      },
      checkedAt: new Date().toISOString(),
    },
    {
      status: healthy ? 200 : 503,
      headers: {
        "Cache-Control": "no-store",
      },
    },
  );
}
