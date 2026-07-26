import assert from "node:assert/strict";

import { selectProfileDelta } from "./select-profile-delta.mjs";

const targetOrigin = "https://notebooklm.google.com";
const launchStartedAt = "2026-07-27T01:00:00.000Z";

function browser(browserId, tabs = []) {
  return { browserId, tabs };
}

function tab(id, url, lastOpened = "2026-07-27T01:00:01.000Z") {
  return { id, providerTabId: `provider-${id}`, url, lastOpened };
}

{
  const result = selectProfileDelta({
    baseline: [browser("old", [tab("old-tab", targetOrigin)])],
    current: [
      browser("old", [tab("old-tab", targetOrigin)]),
      browser("profile-4", [tab("blank", "about:blank")]),
    ],
    targetOrigin,
    launchStartedAt,
  });
  assert.equal(result.status, "selected");
  assert.equal(result.mode, "new_browser");
  assert.equal(result.browserId, "profile-4");
}

{
  const launchedTab = tab("blank", "about:blank");
  const result = selectProfileDelta({
    baseline: [browser("profile-4", [tab("old-tab", targetOrigin)])],
    current: [
      browser("profile-4", [tab("old-tab", targetOrigin), launchedTab]),
    ],
    targetOrigin,
    launchStartedAt,
  });
  assert.equal(result.status, "selected");
  assert.equal(result.mode, "existing_browser_new_tab");
  assert.equal(result.tab, launchedTab);
}

{
  const targetTab = tab("target", `${targetOrigin}/notebook/example`);
  const result = selectProfileDelta({
    baseline: [browser("profile-4")],
    current: [
      browser("profile-4", [
        tab("blank", "about:blank"),
        targetTab,
      ]),
    ],
    targetOrigin,
    launchStartedAt,
  });
  assert.equal(result.status, "selected");
  assert.equal(result.tab, targetTab);
}

{
  const result = selectProfileDelta({
    baseline: [],
    current: [
      browser("profile-4-a", [tab("a", "about:blank")]),
      browser("profile-4-b", [tab("b", "about:blank")]),
    ],
    targetOrigin,
    launchStartedAt,
  });
  assert.equal(result.status, "ambiguous");
  assert.equal(result.reason, "multiple_new_extension_browsers");
}

{
  const result = selectProfileDelta({
    baseline: [browser("profile-4")],
    current: [
      browser("profile-4", [
        tab("a", "about:blank"),
        tab("b", "about:blank"),
      ]),
    ],
    targetOrigin,
    launchStartedAt,
  });
  assert.equal(result.status, "ambiguous");
  assert.equal(result.reason, "multiple_new_target_tabs_in_one_browser");
}

{
  const result = selectProfileDelta({
    baseline: [browser("profile-4", [tab("old", targetOrigin)])],
    current: [browser("profile-4", [tab("old", targetOrigin)])],
    targetOrigin,
    launchStartedAt,
  });
  assert.equal(result.status, "pending");
  assert.equal(result.reason, "no_profile_launch_delta");
}

{
  const baselineTab = {
    id: "old-claim",
    providerTabId: "same-provider-tab",
    url: targetOrigin,
    lastOpened: "2026-07-27T00:30:00.000Z",
  };
  const relistedTab = {
    ...baselineTab,
    id: "new-claim",
  };
  const result = selectProfileDelta({
    baseline: [browser("profile-4", [baselineTab])],
    current: [browser("profile-4", [relistedTab])],
    targetOrigin,
    launchStartedAt,
  });
  assert.equal(result.status, "pending");
  assert.equal(result.reason, "no_profile_launch_delta");
}

{
  const recentTarget = tab(
    "profile-4-target",
    `${targetOrigin}/notebook/example`,
  );
  const result = selectProfileDelta({
    baseline: [],
    current: [
      browser("other-profile", [
        tab(
          "old-blank",
          "about:blank",
          "2026-07-27T00:30:00.000Z",
        ),
      ]),
      browser("profile-4", [recentTarget]),
    ],
    targetOrigin,
    launchStartedAt,
    discoveryMode: "post_launch_initial",
  });
  assert.equal(result.status, "selected");
  assert.equal(result.mode, "post_launch_initial");
  assert.equal(result.browserId, "profile-4");
  assert.equal(result.tab, recentTarget);
}

{
  const result = selectProfileDelta({
    baseline: [],
    current: [
      browser("profile-a", [tab("a", "about:blank")]),
      browser("profile-b", [tab("b", "about:blank")]),
    ],
    targetOrigin,
    launchStartedAt,
    discoveryMode: "post_launch_initial",
  });
  assert.equal(result.status, "ambiguous");
  assert.equal(result.reason, "multiple_recent_profile_launch_candidates");
}

{
  const result = selectProfileDelta({
    baseline: [],
    current: [
      browser("other-profile", [
        tab(
          "old-target",
          targetOrigin,
          "2026-07-27T00:30:00.000Z",
        ),
      ]),
    ],
    targetOrigin,
    launchStartedAt,
    discoveryMode: "post_launch_initial",
  });
  assert.equal(result.status, "pending");
  assert.equal(result.reason, "no_recent_profile_launch_tab");
}

{
  const firstPoll = selectProfileDelta({
    baseline: [],
    current: [browser("other-profile", [])],
    targetOrigin,
    launchStartedAt,
    discoveryMode: "post_launch_initial",
  });
  assert.equal(firstPoll.status, "pending");

  const lateProfileTab = tab("late-profile-4", "about:blank");
  const secondPoll = selectProfileDelta({
    baseline: [],
    current: [
      browser("other-profile", []),
      browser("profile-4", [lateProfileTab]),
    ],
    targetOrigin,
    launchStartedAt,
    discoveryMode: "post_launch_initial",
  });
  assert.equal(secondPoll.status, "selected");
  assert.equal(secondPoll.browserId, "profile-4");
  assert.equal(secondPoll.tab, lateProfileTab);
}

console.log("select-profile-delta tests passed");
