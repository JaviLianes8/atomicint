// Reference answers from the JavaScript runtime for the atomicint oracle tests.
//
// Reads JSON on stdin: a list of cases {"array": <typed array name>, "start": "<int>",
// "ops": [[name, "<int>", ...], ...]} and prints, as JSON, one list of results per case.
// Integer typed arrays use the Atomics functions (store, load, add, sub, exchange,
// compareExchange), which wrap around at the array's width; Uint8ClampedArray uses
// plain assignment, which clamps to 0..255. Values travel as strings so 64-bit ones
// stay exact. Run with: node scripts/oracle/atomics_oracle.js < cases.json
"use strict";

const chunks = [];
process.stdin.on("data", (chunk) => chunks.push(chunk));
process.stdin.on("end", () => {
  const cases = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  process.stdout.write(JSON.stringify(cases.map(runCase)));
});

function runCase({ array, start, ops }) {
  const ta = new globalThis[array](new SharedArrayBuffer(8));
  const big = array.startsWith("Big");
  const num = (text) => (big ? BigInt(text) : Number(text));
  const out = [];
  if (array === "Uint8ClampedArray") {
    ta[0] = num(start);
    out.push(String(ta[0]));
    for (const [name, value] of ops) {
      if (name === "store") ta[0] = num(value);
      else if (name === "add") ta[0] = ta[0] + num(value);
      else throw new Error(name);
      out.push(String(ta[0]));
    }
    return out;
  }
  Atomics.store(ta, 0, num(start));
  out.push(String(Atomics.load(ta, 0)));
  for (const [name, a, b] of ops) {
    let result;
    if (name === "store") {
      Atomics.store(ta, 0, num(a));
      result = Atomics.load(ta, 0);
    } else if (name === "load") result = Atomics.load(ta, 0);
    else if (name === "add") result = Atomics.add(ta, 0, num(a));
    else if (name === "sub") result = Atomics.sub(ta, 0, num(a));
    else if (name === "exchange") result = Atomics.exchange(ta, 0, num(a));
    else if (name === "compareExchange") result = Atomics.compareExchange(ta, 0, num(a), num(b));
    else throw new Error(name);
    out.push(String(result));
  }
  return out;
}
