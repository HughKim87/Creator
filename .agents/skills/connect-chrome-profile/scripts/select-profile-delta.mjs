function nonemptyText(value) {
  return typeof value === "string" && value.length > 0;
}

function tabIdentity(tab) {
  if (nonemptyText(tab?.providerTabId)) {
    return `provider:${tab.providerTabId}`;
  }
  if (nonemptyText(tab?.id)) {
    return `claim:${tab.id}`;
  }
  return null;
}

function normalizedOrigin(value) {
  try {
    return new URL(value).origin;
  } catch {
    return null;
  }
}

function tabPriority(tab, targetOrigin) {
  if (tab?.url === "about:blank") {
    return 1;
  }
  return normalizedOrigin(tab?.url) === targetOrigin ? 2 : 0;
}

function openedAt(tab) {
  const parsed = Date.parse(tab?.lastOpened ?? "");
  return Number.isFinite(parsed) ? parsed : null;
}

function selectTab(tabs, targetOrigin, launchStartedAt) {
  const ranked = tabs
    .map((tab) => ({ tab, priority: tabPriority(tab, targetOrigin) }))
    .filter(({ priority }) => priority > 0);
  if (ranked.length === 0) {
    return { status: "none" };
  }

  const highestPriority = Math.max(...ranked.map(({ priority }) => priority));
  const preferred = ranked
    .filter(({ priority }) => priority === highestPriority)
    .map(({ tab }) => tab);
  if (preferred.length === 1) {
    return { status: "selected", tab: preferred[0] };
  }

  const launchMs = Date.parse(launchStartedAt ?? "");
  if (Number.isFinite(launchMs)) {
    const recent = preferred.filter((tab) => {
      const openedMs = openedAt(tab);
      return openedMs !== null && openedMs >= launchMs - 2000;
    });
    if (recent.length === 1) {
      return { status: "selected", tab: recent[0] };
    }
  }

  return { status: "ambiguous", tabs: preferred };
}

function selectPostLaunchInitial(current, targetOrigin, launchStartedAt) {
  const launchMs = Date.parse(launchStartedAt ?? "");
  if (!Number.isFinite(launchMs)) {
    throw new TypeError(
      "launchStartedAt must be valid for post_launch_initial discovery",
    );
  }

  const selected = [];
  const ambiguous = [];
  for (const browser of current) {
    const eligible = browser.tabs.filter(
      (tab) =>
        tabPriority(tab, targetOrigin) > 0 &&
        openedAt(tab) !== null &&
        openedAt(tab) >= launchMs - 2000,
    );
    const tabResult = selectTab(eligible, targetOrigin, launchStartedAt);
    if (tabResult.status === "selected") {
      selected.push({ browserId: browser.browserId, tab: tabResult.tab });
    } else if (tabResult.status === "ambiguous") {
      ambiguous.push({
        browserId: browser.browserId,
        candidateCount: tabResult.tabs.length,
      });
    }
  }

  if (selected.length === 1 && ambiguous.length === 0) {
    return {
      status: "selected",
      mode: "post_launch_initial",
      browserId: selected[0].browserId,
      tab: selected[0].tab,
      reason: "one_recent_target_tab_after_profile_launch",
    };
  }
  if (selected.length + ambiguous.length > 1) {
    return {
      status: "ambiguous",
      mode: "post_launch_initial",
      reason: "multiple_recent_profile_launch_candidates",
      candidateCount: selected.length + ambiguous.length,
    };
  }
  if (ambiguous.length === 1) {
    return {
      status: "ambiguous",
      mode: "post_launch_initial",
      reason: "multiple_recent_target_tabs_in_one_browser",
      candidateCount: ambiguous[0].candidateCount,
    };
  }

  return {
    status: "pending",
    mode: "post_launch_initial",
    reason: "no_recent_profile_launch_tab",
    candidateCount: 0,
  };
}

function requireSnapshot(snapshot, field) {
  if (!Array.isArray(snapshot)) {
    throw new TypeError(`${field} must be an array`);
  }
  for (const [index, browser] of snapshot.entries()) {
    if (!nonemptyText(browser?.browserId)) {
      throw new TypeError(`${field}[${index}].browserId must be non-empty`);
    }
    if (!Array.isArray(browser?.tabs)) {
      throw new TypeError(`${field}[${index}].tabs must be an array`);
    }
  }
}

/**
 * Select the Chrome extension browser created or changed by one official
 * profile-targeted launch. The function is pure and keeps opaque identifiers
 * only in memory.
 */
export function selectProfileDelta({
  baseline,
  current,
  targetOrigin,
  launchStartedAt,
  discoveryMode = "baseline_delta",
}) {
  requireSnapshot(baseline, "baseline");
  requireSnapshot(current, "current");
  const normalizedTarget = normalizedOrigin(targetOrigin);
  if (normalizedTarget === null) {
    throw new TypeError("targetOrigin must be an absolute URL");
  }
  if (discoveryMode === "post_launch_initial") {
    return selectPostLaunchInitial(
      current,
      normalizedTarget,
      launchStartedAt,
    );
  }
  if (discoveryMode !== "baseline_delta") {
    throw new TypeError(
      "discoveryMode must be baseline_delta or post_launch_initial",
    );
  }

  const baselineByBrowser = new Map(
    baseline.map((browser) => [browser.browserId, browser]),
  );
  const newBrowsers = current.filter(
    (browser) => !baselineByBrowser.has(browser.browserId),
  );

  if (newBrowsers.length === 1) {
    return {
      status: "selected",
      mode: "new_browser",
      browserId: newBrowsers[0].browserId,
      tab: null,
      reason: "one_new_extension_browser",
    };
  }
  if (newBrowsers.length > 1) {
    return {
      status: "ambiguous",
      mode: "new_browser",
      reason: "multiple_new_extension_browsers",
      candidateCount: newBrowsers.length,
    };
  }

  const selected = [];
  const ambiguous = [];
  for (const browser of current) {
    const baselineBrowser = baselineByBrowser.get(browser.browserId);
    if (baselineBrowser === undefined) {
      continue;
    }
    const baselineTabIds = new Set(
      baselineBrowser.tabs.map(tabIdentity).filter(Boolean),
    );
    const newTabs = browser.tabs.filter((tab) => {
      const identity = tabIdentity(tab);
      return identity !== null && !baselineTabIds.has(identity);
    });
    const tabResult = selectTab(newTabs, normalizedTarget, launchStartedAt);
    if (tabResult.status === "selected") {
      selected.push({ browserId: browser.browserId, tab: tabResult.tab });
    } else if (tabResult.status === "ambiguous") {
      ambiguous.push({
        browserId: browser.browserId,
        candidateCount: tabResult.tabs.length,
      });
    }
  }

  if (selected.length === 1 && ambiguous.length === 0) {
    return {
      status: "selected",
      mode: "existing_browser_new_tab",
      browserId: selected[0].browserId,
      tab: selected[0].tab,
      reason: "one_existing_browser_with_one_new_target_tab",
    };
  }
  if (selected.length + ambiguous.length > 1) {
    return {
      status: "ambiguous",
      mode: "existing_browser_new_tab",
      reason: "multiple_existing_browser_candidates",
      candidateCount: selected.length + ambiguous.length,
    };
  }
  if (ambiguous.length === 1) {
    return {
      status: "ambiguous",
      mode: "existing_browser_new_tab",
      reason: "multiple_new_target_tabs_in_one_browser",
      candidateCount: ambiguous[0].candidateCount,
    };
  }
  return {
    status: "pending",
    mode: "none",
    reason: "no_profile_launch_delta",
    candidateCount: 0,
  };
}
