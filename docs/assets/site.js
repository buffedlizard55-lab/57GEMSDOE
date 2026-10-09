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
  const status = document.getElementById('feed-status');
  if (!status) return;
  try {
    const response = await fetch('data/leaderboard_snapshot.json', {cache: 'no-cache'});
    if (!response.ok) throw new Error('snapshot not reachable');
    const snapshot = await response.json();
    const value = snapshot.top_public_dti;
    if (!Number.isFinite(value) || value < 0 || value > 1) throw new Error('invalid snapshot');
    document.getElementById('leaderboard-top').textContent = value.toFixed(4);
    const context = document.getElementById('leaderboard-context');
    if (context) context.textContent = 'top public DTI in the last successful organizer snapshot';
    if (!snapshot.retrieved_utc) {
      status.textContent = `Checked ${snapshot.retrieved_date_utc || 'at an unknown time'} (date precision only). This is a cached public snapshot, not a submission receipt.`;
      status.classList.add('stale');
    } else {
      const checked = new Date(snapshot.retrieved_utc);
      if (!Number.isFinite(checked.getTime())) throw new Error('invalid check timestamp');
      const age = Date.now() - checked.getTime();
      const stale = age > 26 * 60 * 60 * 1000 || age < -5 * 60 * 1000;
      status.classList.toggle('stale', stale);
      status.textContent = `${stale ? 'STALE — ' : ''}Last successful organizer check: ${checked.toISOString()}. Not a submission-page receipt.`;
    }
    const attempt = await fetch('data/feed_refresh_status.json', {cache: 'no-cache'});
    if (attempt.ok) {
      const result = await attempt.json();
      if (result.ok === false) {
        status.classList.add('stale');
        status.textContent += ' Latest automatic refresh failed; retained the last successful snapshot. Open the official board for current context.';
      }
    }
  } catch {
    status.classList.add('stale');
    status.textContent = 'Feed could not be verified. Cached page values are not current or file-specific score evidence; open the official leaderboard.';
  }
}
refreshFeedDisplay();
