#!/usr/bin/env node

/**
 * Bundle size analyzer for SentinelOps
 * Analyzes the production build and reports on bundle sizes
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const BUILD_DIR = path.join(__dirname, '../.next');
const TARGET_SIZE = 250; // Target bundle size in KB

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getFileSize(filePath) {
  try {
    const stats = fs.statSync(filePath);
    return stats.size;
  } catch (error) {
    return 0;
  }
}

function analyzeBundles() {
  console.log('🔍 Analyzing bundle sizes...\n');

  // Check if build directory exists
  if (!fs.existsSync(BUILD_DIR)) {
    console.error('❌ Build directory not found. Run "npm run build" first.');
    process.exit(1);
  }

  const results = {
    mainBundle: 0,
    chunks: [],
    totalSize: 0,
    loadTime3G: 0,
    loadTime4G: 0
  };

  // Find all JavaScript files in the build
  const staticDir = path.join(BUILD_DIR, 'static', 'chunks');
  
  if (fs.existsSync(staticDir)) {
    const files = fs.readdirSync(staticDir, { withFileTypes: true });
    
    files.forEach(file => {
      if (file.isFile() && file.name.endsWith('.js')) {
        const filePath = path.join(staticDir, file.name);
        const size = getFileSize(filePath);
        
        if (file.name.includes('main')) {
          results.mainBundle = size;
        }
        
        results.chunks.push({
          name: file.name,
          size: size,
          sizeFormatted: formatBytes(size)
        });
        
        results.totalSize += size;
      }
    });
  }

  // Calculate estimated load times
  // 3G: ~50KB/s, 4G: ~300KB/s
  results.loadTime3G = (results.totalSize / (50 * 1024)).toFixed(2);
  results.loadTime4G = (results.totalSize / (300 * 1024)).toFixed(2);

  // Display results
  console.log('📊 Bundle Analysis Results\n');
  console.log('═══════════════════════════════════════');
  console.log(`Main Bundle: ${formatBytes(results.mainBundle)}`);
  console.log(`Total Size: ${formatBytes(results.totalSize)}`);
  console.log(`Target Size: ${TARGET_SIZE} KB`);
  console.log('═══════════════════════════════════════\n');

  console.log('📦 Individual Chunks:');
  results.chunks
    .sort((a, b) => b.size - a.size)
    .forEach(chunk => {
      const percentage = ((chunk.size / results.totalSize) * 100).toFixed(1);
      console.log(`  ${chunk.name}: ${chunk.sizeFormatted} (${percentage}%)`);
    });

  console.log('\n⏱️  Estimated Load Times:');
  console.log(`  3G Network: ~${results.loadTime3G}s`);
  console.log(`  4G Network: ~${results.loadTime4G}s`);
  console.log(`  Target: < 3s`);

  console.log('\n🎯 Performance Target:');
  const totalSizeKB = results.totalSize / 1024;
  if (totalSizeKB <= TARGET_SIZE) {
    console.log(`  ✅ PASS - Bundle size (${totalSizeKB.toFixed(0)} KB) is within target`);
  } else {
    console.log(`  ❌ FAIL - Bundle size (${totalSizeKB.toFixed(0)} KB) exceeds target by ${(totalSizeKB - TARGET_SIZE).toFixed(0)} KB`);
  }

  // Recommendations
  if (totalSizeKB > TARGET_SIZE) {
    console.log('\n💡 Recommendations:');
    console.log('  1. Enable code splitting for large components');
    console.log('  2. Lazy load heavy dependencies');
    console.log('  3. Tree-shake unused imports');
    console.log('  4. Use dynamic imports for below-fold content');
    console.log('  5. Optimize images and fonts');
  }

  console.log('\n');
  return results;
}

// Run the analyzer
if (require.main === module) {
  analyzeBundles();
}