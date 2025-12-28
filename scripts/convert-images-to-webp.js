#!/usr/bin/env node

/**
 * Image Optimization Script
 *
 * Converts PNG/JPG images to WebP format for better compression
 * Only converts images larger than 50KB
 */

import sharp from 'sharp';
import { readdir, stat, mkdir } from 'fs/promises';
import { join, extname, basename, dirname } from 'path';
import { fileURLToPath } from 'url';
import { existsSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const publicDir = join(__dirname, '..', 'public');

// Configuration
const CONFIG = {
  minSizeKB: 50, // Only convert images larger than 50KB
  quality: 80, // WebP quality (0-100)
  effort: 6, // Compression effort (0-6, higher = better compression but slower)
  extensions: ['.png', '.jpg', '.jpeg'],
  excludeDirs: ['node_modules', 'dist', '.git']
};

/**
 * Get all image files from a directory recursively
 */
async function getImageFiles(dir, files = []) {
  const entries = await readdir(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = join(dir, entry.name);

    if (entry.isDirectory()) {
      // Skip excluded directories
      if (!CONFIG.excludeDirs.includes(entry.name)) {
        await getImageFiles(fullPath, files);
      }
    } else if (entry.isFile()) {
      const ext = extname(entry.name).toLowerCase();
      if (CONFIG.extensions.includes(ext)) {
        const stats = await stat(fullPath);
        const sizeKB = stats.size / 1024;

        if (sizeKB >= CONFIG.minSizeKB) {
          files.push({
            path: fullPath,
            size: stats.size,
            sizeKB: sizeKB.toFixed(2)
          });
        }
      }
    }
  }

  return files;
}

/**
 * Convert image to WebP format
 */
async function convertToWebP(imagePath, quality = CONFIG.quality) {
  const ext = extname(imagePath);
  const webpPath = imagePath.replace(ext, '.webp');

  // Skip if WebP already exists
  if (existsSync(webpPath)) {
    console.log(`⏭️  Skipping ${basename(imagePath)} (WebP already exists)`);
    return null;
  }

  try {
    const info = await sharp(imagePath)
      .webp({ quality, effort: CONFIG.effort })
      .toFile(webpPath);

    const originalSize = (await stat(imagePath)).size;
    const webpSize = info.size;
    const savings = ((originalSize - webpSize) / originalSize * 100).toFixed(2);

    return {
      original: imagePath,
      webp: webpPath,
      originalSize,
      webpSize,
      savings
    };
  } catch (error) {
    console.error(`❌ Error converting ${basename(imagePath)}:`, error.message);
    return null;
  }
}

/**
 * Format bytes to human-readable size
 */
function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

/**
 * Main execution
 */
async function main() {
  console.log('🔍 Scanning for images to optimize...\n');

  // Get all image files
  const imageFiles = await getImageFiles(publicDir);

  if (imageFiles.length === 0) {
    console.log('✅ No images found that need optimization (all < 50KB)');
    return;
  }

  console.log(`📦 Found ${imageFiles.length} images to convert:\n`);

  // Sort by size (largest first)
  imageFiles.sort((a, b) => b.size - a.size);

  // Show files to be converted
  imageFiles.forEach(file => {
    const relativePath = file.path.replace(publicDir, '');
    console.log(`  • ${relativePath} (${file.sizeKB} KB)`);
  });

  console.log(`\n🚀 Converting images to WebP (quality: ${CONFIG.quality})...\n`);

  // Convert all images
  const results = [];
  for (const file of imageFiles) {
    const result = await convertToWebP(file.path, CONFIG.quality);
    if (result) {
      results.push(result);

      const originalName = basename(result.original);
      console.log(
        `✅ ${originalName}: ${formatBytes(result.originalSize)} → ${formatBytes(result.webpSize)} (${result.savings}% smaller)`
      );
    }
  }

  // Summary
  console.log('\n📊 Conversion Summary:\n');

  const totalOriginalSize = results.reduce((sum, r) => sum + r.originalSize, 0);
  const totalWebPSize = results.reduce((sum, r) => sum + r.webpSize, 0);
  const totalSavings = ((totalOriginalSize - totalWebPSize) / totalOriginalSize * 100).toFixed(2);

  console.log(`  Images converted: ${results.length}`);
  console.log(`  Total original size: ${formatBytes(totalOriginalSize)}`);
  console.log(`  Total WebP size: ${formatBytes(totalWebPSize)}`);
  console.log(`  Total savings: ${formatBytes(totalOriginalSize - totalWebPSize)} (${totalSavings}%)`);

  console.log('\n✨ Image optimization complete!\n');
  console.log('📝 Next steps:');
  console.log('  1. Use OptimizedImage component for all images');
  console.log('  2. Build frontend: npm run build');
  console.log('  3. Test in browser to verify WebP is being served\n');
}

// Run the script
main().catch(console.error);
