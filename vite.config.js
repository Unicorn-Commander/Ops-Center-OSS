import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import { visualizer } from 'rollup-plugin-visualizer'
import { imagetools } from 'vite-imagetools'

export default defineConfig({
  plugins: [
    react({
      // Ensure React loads first
      babel: {
        plugins: []
      }
    }),
    // Image optimization - generates WebP variants
    imagetools({
      defaultDirectives: (url) => {
        // Only process images from /logos directory
        if (url.pathname.includes('/logos/')) {
          return new URLSearchParams({
            format: 'webp',
            quality: '80'
          })
        }
        return new URLSearchParams()
      }
    }),
    // Bundle analyzer - generates stats.html after build
    visualizer({
      open: false,
      gzipSize: true,
      brotliSize: true,
      filename: `${process.env.BUILD_OUT_DIR || 'dist'}/stats.html`,
    }),
    VitePWA({
      registerType: 'prompt', // Changed from autoUpdate to prompt for manual control
      injectRegister: false, // Disable automatic SW registration
      includeAssets: ['favicon.ico', 'robots.txt', 'logos/**/*.png', 'logos/**/*.svg'],
      manifest: {
        name: 'Ops-Center',
        short_name: 'Ops-Center',
        description: 'Operations Center — System Administration Dashboard',
        theme_color: '#7c3aed',
        background_color: '#0f172a',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: '/logos/uc-logo-192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any maskable'
          },
          {
            src: '/logos/uc-logo-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable'
          }
        ]
      },
      workbox: {
        // Increase cache size limit for large bundles
        maximumFileSizeToCacheInBytes: 10 * 1024 * 1024, // 10 MB

        // Cache all static assets (exclude bundle analyzer stats)
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2,woff,ttf,eot}'],
        globIgnores: ['**/stats.html', '**/node_modules/**'],

        // Runtime caching strategies
        runtimeCaching: [
          {
            // API responses - Network First (fresh data priority)
            urlPattern: /^https?:\/\/[^/]+\/api\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 5 // 5 minutes
              },
              cacheableResponse: {
                statuses: [0, 200]
              },
              networkTimeoutSeconds: 10
            }
          },
          {
            // Static API data (rarely changes) - Cache First
            urlPattern: /^https?:\/\/[^/]+\/api\/v1\/(system\/status|branding\/config|deployment\/config)/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'static-api-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 // 1 hour
              }
            }
          },
          {
            // External fonts - Cache First (rarely changes)
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365 // 1 year
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            // Font files
            urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-webfonts',
              expiration: {
                maxEntries: 30,
                maxAgeSeconds: 60 * 60 * 24 * 365 // 1 year
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            // Images - Cache First with size limit
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|ico)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'image-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 * 30 // 30 days
              }
            }
          }
        ],

        // Clean up old caches
        cleanupOutdatedCaches: true,

        // Skip waiting to activate immediately
        skipWaiting: true,
        clientsClaim: true
      },

      // Development options
      devOptions: {
        enabled: false, // Disable in dev mode for easier debugging
        type: 'module'
      }
    })
  ],
  server: {
    port: 8084,
    proxy: {
      '/api': {
        target: 'http://localhost:8085',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8085',
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    // Increase chunk size warning limit
    chunkSizeWarningLimit: 1000,
    // Inline assets smaller than 4KB as base64
    assetsInlineLimit: 4096,
    // Disable modulePreload to prevent wrong load order
    modulePreload: false,
    // Minification
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.log in production
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.debug']
      }
    },
    rollupOptions: {
      output: {
        // Ensure vendor-react loads first by making it the earliest chunk
        chunkFileNames: (chunkInfo) => {
          if (chunkInfo.name === 'vendor-react') {
            return 'assets/0-vendor-react-[hash].js'; // Prefix with 0 to load first
          }
          return 'assets/[name]-[hash].js';
        },
        // Chunk splitting - keep React (and the long tail of React libraries)
        // in the first-loading vendor-react chunk, but split the two biggest
        // independent trees (MUI, charting) into their own cacheable chunks.
        manualChunks: (id) => {
          // Node modules vendor chunks
          if (id.includes('node_modules')) {
            // Swagger UI - Load only when ApiDocumentation tab 0 is active (lazy loaded)
            if (id.includes('swagger-ui-react')) {
              return 'vendor-swagger'
            }

            // ReDoc - Load only when ApiDocumentation tab 1 is active (lazy loaded)
            if (id.includes('redoc')) {
              return 'vendor-redoc'
            }

            // NOTE: MUI and charting libs are deliberately NOT split into
            // their own eager chunks. They read React hooks (e.g. MUI's
            // useEnhancedEffect -> React.useLayoutEffect) at module-eval time;
            // in a separate eager chunk React can be undefined when they run,
            // crashing the whole app before login renders. Keep them together
            // with React in vendor-react. Only truly lazy-loaded trees
            // (swagger-ui-react, redoc) are split above.

            // Bundle EVERYTHING else with React to ensure correct load order
            // This includes: react, react-dom, react-router-dom, Emotion,
            // Framer Motion, all remaining React component libraries, etc.
            return 'vendor-react'
          }
        },
      },
    },

    // Optimize dependencies
    commonjsOptions: {
      include: [/node_modules/],
      transformMixedEsModules: true,
    },
  },

  // Dependency optimization
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@mui/material',
      '@mui/icons-material',
    ],
    exclude: [
      'swagger-ui-react', // Lazy loaded
      'redoc',            // Lazy loaded
    ],
  },
})
