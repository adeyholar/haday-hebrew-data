// Full-corpus parity: canon.ts must give the same string as builder/canon.py for every input.
import { readFileSync } from "node:fs";
import { canon } from "./canon.ts";

const file = process.argv[2];
if (!file) throw new Error("usage: parity.ts <pairs.json>");
const pairs: [string, string][] = JSON.parse(readFileSync(file, "utf-8"));
let bad = 0;
for (const [input, expected] of pairs) {
  const got = canon(input);
  if (got !== expected) {
    bad += 1;
    if (bad <= 5) console.error("differs:", JSON.stringify(input), JSON.stringify(got), JSON.stringify(expected));
  }
}
if (pairs.length < 100000) throw new Error(`only ${pairs.length} strings`);
if (bad) throw new Error(`canon.ts differs from canon.py on ${bad} of ${pairs.length}`);
console.log(`canon parity ok: ${pairs.length} strings`);
