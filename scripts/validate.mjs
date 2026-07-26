import { access, readFile } from 'node:fs/promises';
import { constants } from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const root = path.resolve(process.cwd());
const siteRoot = path.join(root, 'site');
const catalogPath = path.join(siteRoot, 'assets', 'catalog.js');
const indexPath = path.join(siteRoot, 'index.html');
const requiredFiles = [
  'index.html',
  'assets/site.css',
  'assets/site.js',
  'assets/catalog.js',
  'content/research/distributed-llm-inference-survey.html',
  'content/research/fine-grained-gpu-scheduling-survey.html',
  'content/research/leo-satellite-networking-survey.html',
  'content/resources/open-source-llm-inference-shortlist.html',
  'downloads/llm-inference-simulation-platform-slides.pptx'
];

const fail = (message) => {
  console.error(`✗ ${message}`);
  process.exitCode = 1;
};

for (const relativePath of requiredFiles) {
  try {
    await access(path.join(siteRoot, relativePath), constants.R_OK);
    console.log(`✓ ${relativePath}`);
  } catch {
    fail(`Missing required file: ${relativePath}`);
  }
}

const index = await readFile(indexPath, 'utf8');
for (const asset of ['assets/site.css', 'assets/catalog.js', 'assets/site.js']) {
  if (!index.includes(asset)) fail(`Homepage does not load ${asset}`);
}

const catalog = await readFile(catalogPath, 'utf8');
const hrefMatches = [...catalog.matchAll(/href:\s*'([^']+)'/g)].map((match) => match[1]);
if (hrefMatches.length === 0) fail('No content links found in catalog.js');

for (const href of hrefMatches) {
  if (/^(?:https?:|mailto:|#)/.test(href)) continue;
  try {
    await access(path.resolve(siteRoot, href), constants.R_OK);
    console.log(`✓ catalog link: ${href}`);
  } catch {
    fail(`Catalog link does not exist: ${href}`);
  }
}

if (process.exitCode) {
  console.error('\nValidation failed.');
} else {
  console.log(`\nValidation passed: ${hrefMatches.length} catalog links and ${requiredFiles.length} required files checked.`);
}
