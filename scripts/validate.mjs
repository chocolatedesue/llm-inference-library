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
  'content/research/ai-job-projects-2026.html',
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


// PDF entries should have first-page covers for the waterfall gallery.
const pdfHrefs = hrefMatches.filter((href) => /\.pdf$/i.test(href) && !/^(?:https?:|mailto:|#)/.test(href));
for (const href of pdfHrefs) {
  const slug = path.basename(href, '.pdf');
  const cover = path.join('assets', 'covers', `${slug}.jpg`);
  try {
    await access(path.join(siteRoot, cover), constants.R_OK);
    console.log(`✓ pdf cover: ${cover}`);
  } catch {
    fail(`Missing PDF cover for ${href} (expected ${cover}). Run: npm run covers`);
  }
}

// The reader page and its script must exist for PDF cards to have a target.
for (const relativePath of ['reader.html', 'assets/reader.js']) {
  try {
    await access(path.join(siteRoot, relativePath), constants.R_OK);
    console.log(`✓ ${relativePath}`);
  } catch {
    fail(`Missing required file: ${relativePath}`);
  }
}

// Runs published by scripts/publish-run.py must carry their files.
const manualList = path.join(root, 'scripts', 'manual-papers.txt');
let manualSlugs = [];
try {
  manualSlugs = (await readFile(manualList, 'utf8'))
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('#'));
} catch { /* no manual runs yet */ }

for (const slug of manualSlugs) {
  for (const rel of [`downloads/${slug}.pdf`, `assets/covers/${slug}.jpg`, `downloads/runs/${slug}-run.zip`]) {
    try {
      await access(path.join(siteRoot, rel), constants.R_OK);
      console.log(`✓ manual run: ${rel}`);
    } catch {
      fail(`Manual run ${slug} is missing ${rel} (re-run scripts/publish-run.py)`);
    }
  }
  if (!catalog.includes(`id: '${slug}'`)) fail(`Manual run ${slug} has no catalog entry`);
}

// Sidebar grouping is hand-maintained; ungrouped papers still render, so warn only.
const groupedIds = new Set([...catalog.matchAll(/window\.PAPER_GROUPS[\s\S]*$/g)]
  .flatMap((match) => [...match[0].matchAll(/'([a-z0-9-]+)'/g)].map((m) => m[1])));
const paperSlugs = pdfHrefs
  .map((href) => path.basename(href, '.pdf'))
  .filter((slug) => slug !== 'llm-inference-simulation-platform-slides');
const ungrouped = paperSlugs.filter((slug) => !groupedIds.has(slug));
if (ungrouped.length) {
  console.warn(`⚠ 未登记到 window.PAPER_GROUPS 的论文（阅读器里会落到「未分组」）: ${ungrouped.join(', ')}`);
} else {
  console.log('✓ every paper PDF is placed in PAPER_GROUPS');
}

if (process.exitCode) {
  console.error('\nValidation failed.');
} else {
  console.log(`\nValidation passed: ${hrefMatches.length} catalog links and ${requiredFiles.length} required files checked.`);
}
