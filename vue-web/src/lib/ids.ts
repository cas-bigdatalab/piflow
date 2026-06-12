export function shortId() {
  // good enough for thread_id; backend treats as TEXT
  return Math.random().toString(16).slice(2, 10) + Math.random().toString(16).slice(2, 10);
}

export function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

