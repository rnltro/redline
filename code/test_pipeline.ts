/* Full NDA pipeline test: extract -> tokenize -> analyze. */
import { extractEntities, tokenize, analyzeTokenized } from "../src/lib/redline/hybridClient";
import { FIXTURES } from "../src/lib/redline/fixtures";

const nda = FIXTURES.find((f) => f.id === "nda")!.text;
const ents = extractEntities(nda);
const { tokenized, map } = tokenize(nda, ents);
console.log("tokens:", map.map((m) => `${m.token}=${m.value}`).join(" | "));
console.log("---- findings ----");
const res = analyzeTokenized(tokenized);
for (const f of res.findings) {
  console.log(`[${f.severity}] ${f.clauseRef} :: ${f.issue}`);
}
console.log("clause refs parsed:", [...tokenized.matchAll(/^\d+(?:\.\d+)*\./gm)].length);
console.log("has 'liquidated damages':", /liquidated damages/i.test(tokenized));
console.log("has FINANCIAL token:", /\[FINANCIAL_VALUE/.test(tokenized));
