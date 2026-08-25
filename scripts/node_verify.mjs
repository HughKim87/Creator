const [major] = process.versions.node.split(".").map(Number);
const supported = major >= 20 && major < 22;
const result = {
  capability: "node-runtime",
  runtime: process.version,
  status: supported ? "ready" : "unavailable",
  supported_range: ">=20 <22",
};
console.log(JSON.stringify(result));
process.exitCode = supported ? 0 : 1;
