/** Same mark order as builder/canon.py. Do not Unicode-normalize Hebrew. */

const SHIN = new Set([0x05c1, 0x05c2]);
const HARD = new Set([0x034f, 0x200d, 0x200c]);
const STOPS = new Set([" ", "\t", "\n", "\r", "\u05BE", "\u05C0", "\u05C3"]);

function letter(cp: number): boolean {
  return cp >= 0x05d0 && cp <= 0x05ea;
}

function rank(cp: number): number {
  if (SHIN.has(cp)) return 1;
  if (cp === 0x05bc) return 2;
  if (cp === 0x05bf) return 3;
  if ((cp >= 0x05b0 && cp <= 0x05bb) || cp === 0x05c7) return 4;
  if (cp === 0x05bd) return 5;
  if (cp >= 0x0591 && cp <= 0x05af) return 6;
  if (cp === 0x05c4 || cp === 0x05c5) return 7;
  return 8;
}

export function canon(text: string): string {
  const chars = Array.from(text);
  const out: string[] = [];
  let i = 0;
  while (i < chars.length) {
    const cp = chars[i].codePointAt(0) ?? 0;
    if (HARD.has(cp) || !letter(cp)) {
      out.push(chars[i]);
      i += 1;
      continue;
    }
    const marks: { rank: number; at: number; ch: string }[] = [];
    let j = i + 1;
    while (j < chars.length) {
      const cp2 = chars[j].codePointAt(0) ?? 0;
      if (HARD.has(cp2) || letter(cp2) || STOPS.has(chars[j])) break;
      marks.push({ rank: rank(cp2), at: j, ch: chars[j] });
      j += 1;
    }
    marks.sort((a, b) => a.rank - b.rank || a.at - b.at);
    out.push(chars[i], ...marks.map((mark) => mark.ch));
    i = j;
  }
  return out.join("");
}
