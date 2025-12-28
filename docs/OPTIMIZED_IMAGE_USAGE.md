# OptimizedImage Component - Usage Guide

**Component**: `src/components/OptimizedImage.jsx`
**Purpose**: Lazy loading, WebP-optimized image component for performance
**Created**: October 24, 2025

---

## Quick Start

### Basic Usage

```jsx
import { OptimizedImage } from '@/components/OptimizedImage';

function MyComponent() {
  return (
    <OptimizedImage
      src="/logos/Center-Deep.png"
      alt="Center Deep Logo"
      width="200"
      height="100"
    />
  );
}
```

**What happens automatically**:
1. ✅ Tries to load `/logos/Center-Deep.webp` (89% smaller!)
2. ✅ Falls back to `/logos/Center-Deep.png` if WebP not available
3. ✅ Shows blur placeholder while loading
4. ✅ Only loads when image scrolls into viewport (lazy loading)

---

## Component Props

### Required Props

| Prop | Type | Description |
|------|------|-------------|
| `src` | `string` | Path to image (e.g., `/logos/logo.png`) |
| `alt` | `string` | Alt text for accessibility (required!) |

### Optional Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `className` | `string` | `''` | CSS classes to apply |
| `width` | `string \| number` | `'100%'` | Image width |
| `height` | `string \| number` | `'auto'` | Image height |
| `loading` | `'lazy' \| 'eager'` | `'lazy'` | Loading strategy |
| `placeholder` | `boolean` | `true` | Show blur placeholder |
| `objectFit` | `'contain' \| 'cover' \| 'fill' \| 'none' \| 'scale-down'` | `'contain'` | CSS object-fit |

---

## Usage Examples

### Example 1: Logo in Header (Critical - Load Immediately)

```jsx
<OptimizedImage
  src="/logos/magic_unicorn_logo.png"
  alt="Magic Unicorn Logo"
  width="150"
  height="50"
  loading="eager"  // Load immediately (above-the-fold)
/>
```

### Example 2: Service Card Icon (Lazy Load)

```jsx
<OptimizedImage
  src="/logos/Center-Deep.png"
  alt="Center Deep Search Engine"
  width="64"
  height="64"
  className="service-icon"
  objectFit="contain"
/>
```

### Example 3: Full-Width Banner

```jsx
<OptimizedImage
  src="/logos/UC-Authentik-background.jpeg"
  alt="Authentication Background"
  width="100%"
  height="400"
  objectFit="cover"  // Cover entire area
  placeholder={false}  // No placeholder for background
/>
```

### Example 4: Avatar/Profile Picture

```jsx
<OptimizedImage
  src="/logos/The_Colonel.png"
  alt="The Colonel Avatar"
  width="48"
  height="48"
  className="rounded-full"
  objectFit="cover"
/>
```

### Example 5: Gallery/Grid Images

```jsx
const images = [
  { src: '/logos/Gunny_Logo.png', alt: 'Gunny' },
  { src: '/logos/The_General_Logo.png', alt: 'The General' },
  { src: '/logos/Hopper_Nichols.png', alt: 'Hopper Nichols' }
];

return (
  <div className="grid grid-cols-3 gap-4">
    {images.map((img) => (
      <OptimizedImage
        key={img.src}
        src={img.src}
        alt={img.alt}
        width="300"
        height="200"
        objectFit="cover"
      />
    ))}
  </div>
);
```

---

## When to Use

### ✅ Use OptimizedImage for:

- Service logos and icons
- User avatars and profile pictures
- Dashboard banners and backgrounds
- Service card images
- Gallery/grid images
- Any PNG/JPG image > 10 KB

### ❌ Don't use for:

- SVG icons (use regular `<img>` or inline SVG)
- Tiny images < 5 KB (overhead not worth it)
- Base64-encoded images
- External images (e.g., from other domains)

---

## Migration Guide

### Before (Old Way)

```jsx
// ❌ Not optimized
<img
  src="/logos/Center-Deep.png"
  alt="Center Deep"
  className="logo"
  width="200"
/>
```

**Issues**:
- Loads 1.8 MB PNG file
- No lazy loading (blocks initial load)
- No WebP support (wasted bandwidth)

### After (Optimized Way)

```jsx
// ✅ Optimized
import { OptimizedImage } from '@/components/OptimizedImage';

<OptimizedImage
  src="/logos/Center-Deep.png"
  alt="Center Deep"
  className="logo"
  width="200"
/>
```

**Benefits**:
- Loads 48 KB WebP file (97% smaller!)
- Lazy loads when scrolled into view
- Shows blur placeholder while loading
- Automatic fallback for older browsers

---

## Advanced Usage

### Custom Loading State

```jsx
import { OptimizedImage } from '@/components/OptimizedImage';
import { CircularProgress } from '@mui/material';

function ImageWithCustomLoader() {
  const [loading, setLoading] = useState(true);

  return (
    <div style={{ position: 'relative' }}>
      {loading && (
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>
          <CircularProgress />
        </div>
      )}
      <OptimizedImage
        src="/logos/large-image.png"
        alt="Large Image"
        onLoad={() => setLoading(false)}
      />
    </div>
  );
}
```

### Responsive Images (Future)

```jsx
// Coming in Phase 2: Responsive image support
<OptimizedImage
  src="/logos/logo.png"
  alt="Responsive Logo"
  srcSet="/logos/logo-400w.webp 400w, /logos/logo-800w.webp 800w"
  sizes="(max-width: 600px) 400px, 800px"
/>
```

---

## Performance Tips

### 1. Preload Critical Images

For above-the-fold images, add to `index.html`:

```html
<!-- index.html -->
<link rel="preload" as="image" href="/logos/magic_unicorn_logo.webp" type="image/webp" />
```

Then use `loading="eager"` in component:

```jsx
<OptimizedImage
  src="/logos/magic_unicorn_logo.png"
  alt="Logo"
  loading="eager"
/>
```

### 2. Use Correct objectFit

- **`contain`**: For logos (maintain aspect ratio, fit inside)
- **`cover`**: For backgrounds (fill area, may crop)
- **`fill`**: Stretch to fill (may distort)

```jsx
// Logo - maintain aspect
<OptimizedImage src="/logo.png" alt="Logo" objectFit="contain" />

// Background - fill area
<OptimizedImage src="/bg.jpg" alt="Background" objectFit="cover" />
```

### 3. Specify Dimensions

Always provide `width` and `height` to prevent layout shift:

```jsx
// ❌ Bad - causes layout shift
<OptimizedImage src="/logo.png" alt="Logo" />

// ✅ Good - reserves space
<OptimizedImage src="/logo.png" alt="Logo" width="200" height="100" />
```

### 4. Disable Placeholder for Backgrounds

For background images, disable placeholder to avoid flicker:

```jsx
<OptimizedImage
  src="/background.jpg"
  alt="Background"
  placeholder={false}
  objectFit="cover"
/>
```

---

## Browser Compatibility

### WebP Support

| Browser | WebP Support | Fallback |
|---------|--------------|----------|
| Chrome 23+ | ✅ Yes | - |
| Firefox 65+ | ✅ Yes | - |
| Safari 14+ | ✅ Yes | - |
| Edge 18+ | ✅ Yes | - |
| IE 11 | ❌ No | PNG/JPG |
| Safari < 14 | ❌ No | PNG/JPG |

**Global Coverage**: 95%+ of users will get WebP

### Lazy Loading Support

| Browser | Native Lazy Load | Polyfill |
|---------|------------------|----------|
| Chrome 76+ | ✅ Yes | - |
| Firefox 75+ | ✅ Yes | - |
| Safari 15.4+ | ✅ Yes | - |
| Edge 79+ | ✅ Yes | - |
| Older browsers | ❌ No | Intersection Observer |

**Global Coverage**: 100% (component includes polyfill)

---

## Troubleshooting

### Image Not Loading

**Problem**: Image shows broken icon

**Solutions**:
1. Check file exists: `ls public/logos/your-image.png`
2. Check WebP exists: `ls public/logos/your-image.webp`
3. Convert if missing: `node scripts/convert-images-to-webp.js`

### WebP Not Loading (Fallback to PNG)

**Problem**: Browser loads PNG instead of WebP

**Cause**: WebP file doesn't exist or is corrupt

**Solution**:
```bash
# Re-convert images
node scripts/convert-images-to-webp.js

# Check WebP file
file public/logos/your-image.webp
# Should output: "Web/P image data"
```

### Layout Shift on Load

**Problem**: Page content jumps when image loads

**Solution**: Always specify dimensions:
```jsx
<OptimizedImage
  src="/logo.png"
  alt="Logo"
  width="200"   // ← Add this
  height="100"  // ← And this
/>
```

### Image Too Small/Large

**Problem**: Image doesn't fit correctly

**Solution**: Use `objectFit` prop:
```jsx
// For logos (maintain aspect ratio)
<OptimizedImage src="/logo.png" alt="Logo" objectFit="contain" />

// For backgrounds (fill space)
<OptimizedImage src="/bg.jpg" alt="BG" objectFit="cover" />
```

---

## Adding New Images

### Step-by-Step Process

1. **Add image to public/logos/**
   ```bash
   cp your-new-image.png public/logos/
   ```

2. **Convert to WebP**
   ```bash
   node scripts/convert-images-to-webp.js
   ```

3. **Use in component**
   ```jsx
   <OptimizedImage
     src="/logos/your-new-image.png"
     alt="Your Image Description"
     width="200"
     height="100"
   />
   ```

4. **Build and deploy**
   ```bash
   npm run build
   cp -r dist/* public/
   docker restart ops-center-direct
   ```

---

## API Reference

### Component Signature

```typescript
function OptimizedImage(props: OptimizedImageProps): JSX.Element

interface OptimizedImageProps {
  // Required
  src: string;              // Image source path
  alt: string;              // Alt text (accessibility)

  // Optional
  className?: string;       // CSS classes
  width?: string | number;  // Image width
  height?: string | number; // Image height
  loading?: 'lazy' | 'eager'; // Loading strategy
  placeholder?: boolean;    // Show blur placeholder
  objectFit?: 'contain' | 'cover' | 'fill' | 'none' | 'scale-down';

  // Additional HTML img attributes
  ...props: React.ImgHTMLAttributes<HTMLImageElement>;
}
```

### Internal Behavior

1. **Intersection Observer** checks if image is in viewport
2. **WebP Detection** generates `.webp` path from original extension
3. **Picture Element** uses `<source>` for WebP, `<img>` for fallback
4. **Lazy Loading** only loads when `isInView` becomes true
5. **Blur Placeholder** shows animated gradient until image loads
6. **Error Handling** falls back to original format if WebP fails

---

## Best Practices

### ✅ DO

- Always provide `alt` text for accessibility
- Specify `width` and `height` to prevent layout shift
- Use `loading="eager"` for above-the-fold images
- Use `loading="lazy"` (default) for below-the-fold images
- Convert images to WebP before using

### ❌ DON'T

- Don't use for SVG files (use regular `<img>` or inline SVG)
- Don't use for tiny images < 5 KB (overhead not worth it)
- Don't forget `alt` text (breaks accessibility)
- Don't use external image URLs (WebP detection won't work)

---

## Related Files

- **Component**: `src/components/OptimizedImage.jsx`
- **Conversion Script**: `scripts/convert-images-to-webp.js`
- **Vite Config**: `vite.config.js` (imagetools plugin)
- **Documentation**: `docs/ASSET_OPTIMIZATION_REPORT.md`
- **WebP Images**: `public/logos/*.webp` (22 files)

---

## Support

For issues or questions:
1. Check this guide first
2. Review `ASSET_OPTIMIZATION_REPORT.md`
3. Check browser console for errors
4. Verify WebP files exist in `public/logos/`

**Last Updated**: October 24, 2025
**Component Version**: 1.0.0
