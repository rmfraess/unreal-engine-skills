#!/usr/bin/env node
/**
 * Validates the repository's Hermes discovery contract without external packages.
 * This supplements, rather than replaces, the Agent Skills reference validator.
 */

import { readdir, readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..');
const skillsRoot = path.join(repoRoot, 'skills');
const MAX_NAME_LENGTH = 64;
const MAX_DESCRIPTION_LENGTH = 1024;
const MAX_SKILL_LENGTH = 100_000;
const HERMES_PREVIEW_LENGTH = 57;

async function collectSkillFiles(directory) {
  const files = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const full = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await collectSkillFiles(full)));
    } else if (entry.isFile() && entry.name === 'SKILL.md') {
      files.push(full);
    }
  }
  return files;
}

async function collectMarkdownFiles(directory) {
  const files = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const full = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await collectMarkdownFiles(full)));
    } else if (entry.isFile() && entry.name.toLowerCase().endsWith('.md')) {
      files.push(full);
    }
  }
  return files;
}

function parseHermesMetadata(frontmatter) {
  const lines = frontmatter.split('\n');
  const metadataStart = lines.indexOf('metadata:');
  if (metadataStart < 0) return null;

  let metadataEnd = lines.length;
  for (let index = metadataStart + 1; index < lines.length; index += 1) {
    if (lines[index] && !lines[index].startsWith(' ')) {
      metadataEnd = index;
      break;
    }
  }

  const hermesStart = lines.findIndex(
    (line, index) => index > metadataStart && index < metadataEnd && line === '  hermes:',
  );
  if (hermesStart < 0) return null;

  const hermesLines = [];
  for (let index = hermesStart + 1; index < metadataEnd; index += 1) {
    const line = lines[index];
    if (line && !line.startsWith('    ')) break;
    hermesLines.push(line);
  }
  const hermesBlock = hermesLines.join('\n');
  return {
    tags: hermesBlock.match(/^    tags:\s*\[([^\]]*)\]\s*$/m)?.[1],
    related: hermesBlock.match(/^    related_skills:\s*\[([^\]]*)\]\s*$/m)?.[1],
  };
}

function parseFrontmatter(text, relativePath) {
  if (!text.startsWith('---\n') && !text.startsWith('---\r\n')) {
    throw new Error(`${relativePath}: frontmatter must start at byte 0`);
  }

  text = text.replaceAll('\r\n', '\n');

  const closing = text.indexOf('\n---\n', 4);
  if (closing < 0) {
    throw new Error(`${relativePath}: frontmatter closing delimiter not found`);
  }

  const frontmatter = text.slice(4, closing);
  const body = text.slice(closing + 5).trim();
  const name = frontmatter.match(/^name:\s*([^\n]+)$/m)?.[1]?.trim();
  const descriptionBlock = frontmatter.match(/^description:\s*>-\n((?: {2}[^\n]*\n?)+)/m)?.[1];
  const description = descriptionBlock
    ? descriptionBlock
        .split('\n')
        .map((line) => line.replace(/^ {2}/, '').trim())
        .filter(Boolean)
        .join(' ')
    : frontmatter.match(/^description:\s*([^\n]+)$/m)?.[1]?.trim();
  const license = frontmatter.match(/^license:\s*([^\n]+)$/m)?.[1]?.trim();
  const hermes = parseHermesMetadata(frontmatter);

  return { frontmatter, body, name, description, license, hermes };
}

function parseInlineList(value) {
  if (value === undefined) return null;
  if (!value.trim()) return [];
  return value.split(',').map((item) => item.trim()).filter(Boolean);
}

function relativeResourceLinks(text) {
  const links = [];
  const pattern = /\[[^\]\n]*\]\(([^)\n]+)\)/g;
  for (const match of text.matchAll(pattern)) {
    const rawTarget = match[1].trim();
    if (!rawTarget || /^(?:https?:|mailto:|#)/i.test(rawTarget)) continue;
    const destination = rawTarget.startsWith('<')
      ? rawTarget.slice(1, rawTarget.indexOf('>'))
      : rawTarget.split(/\s+/, 1)[0];
    const target = destination.split('#', 1)[0];
    if (/^(?:\.{0,2}\/|references\/|scripts\/|assets\/|templates\/)/.test(target)
        || /\.[a-z0-9]{1,8}$/i.test(target)) {
      links.push(target);
    }
  }
  return links;
}

async function main() {
  const skillFiles = await collectSkillFiles(skillsRoot);
  const failures = [];
  const records = [];

  if (skillFiles.length === 0) {
    failures.push('skills tree contains no SKILL.md files');
  }

  for (const file of skillFiles.sort()) {
    const relative = path.relative(repoRoot, file).replaceAll('\\', '/');
    const text = await readFile(file, 'utf8');
    let parsed;

    try {
      parsed = parseFrontmatter(text, relative);
    } catch (error) {
      failures.push(error.message);
      continue;
    }

    const { body, name, description, license } = parsed;
    const tags = parseInlineList(parsed.hermes?.tags);
    const related = parseInlineList(parsed.hermes?.related);
    const folder = path.basename(path.dirname(file));

    if (!name) failures.push(`${relative}: missing name`);
    if (name && (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name) || name.length > MAX_NAME_LENGTH)) {
      failures.push(`${relative}: invalid name '${name}'`);
    }
    if (name && name !== folder) failures.push(`${relative}: name must match folder '${folder}'`);
    if (!description) failures.push(`${relative}: missing description`);
    if (description && description.length > MAX_DESCRIPTION_LENGTH) {
      failures.push(`${relative}: description is ${description.length} characters`);
    }
    if (description && !description.startsWith('Use when ')) {
      failures.push(`${relative}: description must start with 'Use when '`);
    }
    let firstTrigger = '';
    if (description) {
      const firstStop = description.indexOf('.');
      if (firstStop < 0 || firstStop + 1 > HERMES_PREVIEW_LENGTH) {
        failures.push(`${relative}: first trigger sentence must finish within ${HERMES_PREVIEW_LENGTH} characters`);
      } else {
        firstTrigger = description.slice(0, firstStop + 1);
      }
    }
    if (name?.startsWith('uds-')) {
      if (!firstTrigger.startsWith('Use when confirmed Ultra Dynamic Sky')) {
        failures.push(`${relative}: first trigger must begin "Use when confirmed Ultra Dynamic Sky"`);
      }
    }
    if (name?.startsWith('udw-')) {
      if (!firstTrigger.startsWith('Use when confirmed Ultra Dynamic Weather')) {
        failures.push(`${relative}: first trigger must begin "Use when confirmed Ultra Dynamic Weather"`);
      }
    }
    if (!license) failures.push(`${relative}: missing explicit license status`);
    if (!parsed.hermes) failures.push(`${relative}: missing metadata.hermes`);
    if (!tags || tags.length < 2) failures.push(`${relative}: metadata.hermes.tags needs at least two tags`);
    if (!related) failures.push(`${relative}: missing metadata.hermes.related_skills`);
    if (!body) failures.push(`${relative}: body is empty`);
    if (text.length > MAX_SKILL_LENGTH) failures.push(`${relative}: file exceeds ${MAX_SKILL_LENGTH} characters`);
    let foundSearchFiles = false;
    let foundReadFile = false;
    for (const markdownFile of await collectMarkdownFiles(path.dirname(file))) {
      const markdownRelative = path.relative(repoRoot, markdownFile).replaceAll('\\', '/');
      const markdown = await readFile(markdownFile, 'utf8');
      foundSearchFiles ||= /\bsearch_files\s*\(/.test(markdown);
      foundReadFile ||= /\bread_file\s*\(/.test(markdown);
      if (/(?:^|[^.\w])(?:Glob|Grep|Read)\s*\(/.test(markdown)) {
        failures.push(`${markdownRelative}: contains non-Hermes pseudo-tool calls`);
      }
      for (const linked of relativeResourceLinks(markdown)) {
        const linkedPath = path.resolve(path.dirname(markdownFile), linked);
        try {
          const linkedStat = await stat(linkedPath);
          if (!linkedStat.isFile()) throw new Error('not a file');
        } catch {
          failures.push(`${markdownRelative}: missing linked resource file '${linked}'`);
        }
      }
    }
    if (name === 'navigating-engine-source' && (!foundSearchFiles || !foundReadFile)) {
      failures.push(`${relative}: source-navigation workflow must use search_files and read_file`);
    }

    records.push({ relative, name, related: related ?? [] });
  }

  const nameCounts = new Map();
  for (const record of records) {
    if (record.name) nameCounts.set(record.name, (nameCounts.get(record.name) ?? 0) + 1);
  }
  for (const [name, count] of nameCounts) {
    if (count > 1) failures.push(`duplicate skill name '${name}' appears ${count} times`);
  }
  const names = new Set(nameCounts.keys());
  for (const record of records) {
    for (const related of record.related) {
      if (!names.has(related)) {
        failures.push(`${record.relative}: related skill '${related}' does not exist`);
      }
      if (related === record.name) {
        failures.push(`${record.relative}: related skill must not reference itself`);
      }
    }
  }

  console.log(`[check-hermes] Skills scanned: ${skillFiles.length}`);
  console.log(`[check-hermes] Unique names: ${names.size}`);

  if (failures.length) {
    console.error(`[check-hermes] FAILED: ${failures.length} issue(s)`);
    for (const failure of failures) console.error(`  - ${failure}`);
    process.exit(1);
  }

  console.log('[check-hermes] OK — discovery metadata, local resource links, and source-navigation tools are valid.');
}

main().catch((error) => {
  console.error('[check-hermes] Failed:', error);
  process.exit(1);
});
