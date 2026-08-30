const GO = /\b(go to|open|take me to|navigate)\b/;

export function navPathFromMessage(message: string): string | null {
  const lower = message.trim().toLowerCase();
  if (!GO.test(lower)) return null;
  if (/\b(dashboard|board|home)\b/.test(lower)) return "/";
  if (/\bemployees\b/.test(lower)) return "/employees";
  if (/\bimport\b/.test(lower)) return "/import";
  return null;
}
