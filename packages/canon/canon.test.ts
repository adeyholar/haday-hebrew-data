import assert from "node:assert/strict";
import { canon } from "./canon.ts";

const samples = ["בְּרֵאשִׁ֖ית", "הָאָֽרֶץ", "וְהָאָ֗רֶץ", "תֹ֨הוּ֙", "אֱלֹהִ֤ים ׀"];
for (const sample of samples) {
  assert.equal(canon(canon(sample)), canon(sample), sample);
}
// Shin dot, then dagesh, then vowel, then accent. Source order of the accents stays.
assert.equal(canon("בְּ"), "בְּ");
console.log("canon.ts ok");
