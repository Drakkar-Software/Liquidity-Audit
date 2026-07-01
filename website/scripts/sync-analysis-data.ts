import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const websiteRoot = path.resolve(scriptDirectory, '..');
const sourceDirectory = path.resolve(websiteRoot, '..', 'data', 'analysis');
const destinationDirectory = path.resolve(websiteRoot, 'public', 'data', 'analysis');

async function copyDirectoryRecursive(sourcePath: string, destinationPath: string): Promise<void> {
  await fs.mkdir(destinationPath, { recursive: true });
  const directoryEntries = await fs.readdir(sourcePath, { withFileTypes: true });

  for (const directoryEntry of directoryEntries) {
    const entrySourcePath = path.join(sourcePath, directoryEntry.name);
    const entryDestinationPath = path.join(destinationPath, directoryEntry.name);

    if (directoryEntry.isDirectory()) {
      await copyDirectoryRecursive(entrySourcePath, entryDestinationPath);
      continue;
    }

    if (directoryEntry.isFile()) {
      await fs.copyFile(entrySourcePath, entryDestinationPath);
    }
  }
}

async function main(): Promise<void> {
  try {
    await fs.access(sourceDirectory);
  } catch {
    throw new Error(`Source analysis data not found: ${sourceDirectory}`);
  }

  await copyDirectoryRecursive(sourceDirectory, destinationDirectory);
  console.log(`Synced analysis data to ${destinationDirectory}`);
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(message);
  process.exit(1);
});
