// Minimal Markdown: split into blocks, "## " marks a heading. Mirrors the
// prototype's blocksOf(); the admin editor writes exactly this format.
export function blocksOf(str) {
  return String(str || '')
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)
    .map((line) => {
      const head = line.startsWith('## ');
      return { head, text: head ? line.slice(3).trim() : line };
    });
}
