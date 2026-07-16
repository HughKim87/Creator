#!/usr/bin/env node
// Lifecycle: task-scoped. Keep through v9 calibration review, then remove with the review builder.
import fs from "node:fs";

const path = process.argv[2];
if (!path) throw new Error("HTML path is required");
const document = fs.readFileSync(path, "utf8");
const blocks = [...document.matchAll(/<script>([\s\S]*?)<\/script>/g)];
if (blocks.length !== 1) throw new Error(`expected 1 inline script, found ${blocks.length}`);
new Function(blocks[0][1]);
console.log(`[v9-review-validate] inline script syntax OK: ${path}`);
