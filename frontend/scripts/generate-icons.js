const fs = require('fs')
const path = require('path')

// Simple SVG icon template
const createIcon = (size) => {
  const padding = size * 0.1
  const innerSize = size - (padding * 2)
  
  return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="${size}" height="${size}" fill="#09090b" rx="${size * 0.1}"/>
  
  <!-- Shield Icon -->
  <g transform="translate(${size/2}, ${size/2})">
    <path 
      d="M0 -${innerSize * 0.4} 
         C-${innerSize * 0.3} -${innerSize * 0.3} -${innerSize * 0.35} -${innerSize * 0.1} -${innerSize * 0.35} ${innerSize * 0.1}
         C-${innerSize * 0.35} ${innerSize * 0.3} -${innerSize * 0.2} ${innerSize * 0.4} 0 ${innerSize * 0.45}
         C${innerSize * 0.2} ${innerSize * 0.4} ${innerSize * 0.35} ${innerSize * 0.3} ${innerSize * 0.35} ${innerSize * 0.1}
         C${innerSize * 0.35} -${innerSize * 0.1} ${innerSize * 0.3} -${innerSize * 0.3} 0 -${innerSize * 0.4}
         Z"
      fill="#3b82f6"
      stroke="#60a5fa"
      stroke-width="${size * 0.02}"
    />
    
    <!-- S Letter -->
    <text 
      x="0" 
      y="${innerSize * 0.1}" 
      font-family="Arial, sans-serif" 
      font-size="${innerSize * 0.5}" 
      font-weight="bold" 
      fill="white" 
      text-anchor="middle"
    >S</text>
  </g>
</svg>`
}

// Icon sizes to generate
const sizes = [72, 96, 128, 144, 152, 180, 192, 384, 512]

// Ensure public directory exists
const publicDir = path.join(__dirname, '..', 'public')
if (!fs.existsSync(publicDir)) {
  fs.mkdirSync(publicDir, { recursive: true })
}

// Generate icons
sizes.forEach(size => {
  const svg = createIcon(size)
  const filename = path.join(publicDir, `icon-${size}x${size}.svg`)
  fs.writeFileSync(filename, svg)
  console.log(`Generated ${filename}`)
})

console.log('Icon generation complete!')

// Note: In a production environment, you would convert these SVGs to PNGs
// using a tool like sharp or imagemagick