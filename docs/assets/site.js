'use strict';

// The site is read-only. It does not train, place dots, upload or use a slot.
for (const button of document.querySelectorAll('[data-copy]')) {
  button.addEventListener('click', async () => {
    const source = document.getElementById(button.dataset.copy);
    if (!source) return;
    try {
      await navigator.clipboard.writeText(source.textContent);
      button.textContent = 'Copied';
    } catch {
      button.textContent = 'Copy unavailable — select the note above';
    }
  });
}

async function refreshFeedDisplay() {
  const statusNode = document.getElementById('feed-status');
  if (!statusNode) return;
  try {
    const snapshotResponse = await fetch('data/leaderboard_snapshot.json', {cache: 'no-cache'});
    if (!snapshotResponse.ok) throw new Error('snapshot not reachable');
    const snapshot = await snapshotResponse.json();
    const value = snapshot.top_public_dti;
    if (!Number.isFinite(value) || value < 0 || value > 1) throw new Error('invalid snapshot');
    const top = document.getElementById('leaderboard-top');
    if (top) top.textContent = value.toFixed(4);

    const statusResponse = await fetch('data/feed_refresh_status.json', {cache: 'no-cache'});
    const attempt = statusResponse.ok ? await statusResponse.json() : {};
    const retrieved = new Date(snapshot.retrieved_utc || '');
    if (!Number.isFinite(retrieved.getTime())) throw new Error('invalid snapshot timestamp');
    const age = Date.now() - retrieved.getTime();
    let stale = age > 26 * 60 * 60 * 1000 || age < -5 * 60 * 1000;
    const method = attempt.method || snapshot.retrieval_method || 'retrieval method not recorded';
    let message = `${stale ? 'STALE / CLOCK-SKEWED SNAPSHOT — ' : ''}Public snapshot retrieved ${retrieved.toISOString()}. Capture method: ${method}.`;
    if (attempt.ok === false) {
      stale = true;
      message += ` Latest refresh failed; prior snapshot retained=${Boolean(attempt.retained_previous_snapshot)}. ${attempt.error || 'No error detail recorded.'}`;
    }
    if (attempt.full_table_captured === false || snapshot.raw_html_retained === false) {
      message += ' Selected rows only; raw organizer HTML was not retained.';
    }
    message += ' Not a submission-page receipt. Do not infer exact-file attribution or causality.';
    statusNode.classList.toggle('stale', stale);
    statusNode.textContent = message;
  } catch {
    statusNode.classList.add('stale');
    statusNode.textContent = 'Feed could not be verified. Cached page values are not current or file-specific score evidence; open the official leaderboard.';
  }
}
refreshFeedDisplay();
