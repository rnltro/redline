/* Debug why clause 5 (REMEDIES) rules do not fire. */
import { extractEntities, tokenize } from "../src/lib/redline/hybridClient";
import { FIXTURES } from "../src/lib/redline/fixtures";

const nda = FIXTURES.find((f) => f.id === "nda")!.text;
const ents = extractEntities(nda);
const { tokenized } = tokenize(nda, ents);

const blocks = tokenized.split(/\n\s*\n/);
console.log("block count:", blocks.length);
for (const b of blocks) {
  const line = b.trim().split("\n")[0] ?? "";
  const m = line.match(/^(\d+(?:\.\d+)*)\.\s+([^.]{2,60})/);
  console.log(
    `block starts: "${line.slice(0, 40)}" -> ${m ? `clause ${m[1]} "${m[2].trim()}"` : "NOT A CLAUSE"}`
  );
}
