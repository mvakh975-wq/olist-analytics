import {readdirSync, readFileSync, statSync, writeFileSync} from "node:fs";
import {join} from "node:path";

function* htmlFiles(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) yield* htmlFiles(path);
    else if (name.endsWith(".html")) yield path;
  }
}

let count = 0;
for (const file of htmlFiles("dist")) {
  const html = readFileSync(file, "utf8");
  if (!html.includes("<html>")) continue;
  writeFileSync(file, html.replace("<html>", '<html lang="en">'));
  count++;
}
console.log(`postbuild: lang="en" set on ${count} pages`);
