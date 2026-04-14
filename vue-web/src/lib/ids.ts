export function shortId() {
  // good enough for thread_id; backend treats as TEXT
  return Math.random().toString(16).slice(2, 10) + Math.random().toString(16).slice(2, 10);
}

