// Service Worker for SentinelOps PWA
const CACHE_NAME = 'sentinelops-v1'
const urlsToCache = [
  '/',
  '/dashboard',
  '/incidents',
  '/offline.html',
  '/manifest.json'
]

// Install event - cache essential files
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache')
        return cache.addAll(urlsToCache)
      })
      .then(() => self.skipWaiting())
  )
})

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName)
            return caches.delete(cacheName)
          }
        })
      )
    }).then(() => self.clients.claim())
  )
})

// Fetch event - network-first strategy with selective caching
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return

  const url = new URL(event.request.url)
  
  // Skip caching for API calls, WebSocket connections, and external resources
  if (url.pathname.startsWith('/api/') || 
      url.pathname.startsWith('/ws/') ||
      url.pathname.startsWith('/_next/') ||
      url.hostname !== self.location.hostname) {
    return
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Don't cache non-successful responses
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response
        }

        // Only cache specific file types
        const shouldCache = url.pathname.match(/\.(html|css|js|svg|png|jpg|jpeg|webp|woff2?)$/i) ||
                          url.pathname === '/' ||
                          urlsToCache.includes(url.pathname)

        if (shouldCache) {
          const responseToCache = response.clone()
          caches.open(CACHE_NAME)
            .then((cache) => {
              cache.put(event.request, responseToCache)
            })
        }

        return response
      })
      .catch(() => {
        // Return cached response if available
        return caches.match(event.request)
          .then((response) => {
            if (response) {
              return response
            }

            // Return offline page for navigation requests
            if (event.request.mode === 'navigate') {
              return caches.match('/offline.html')
            }

            // Return a basic offline response for other requests
            return new Response('Offline', {
              status: 503,
              statusText: 'Service Unavailable',
              headers: new Headers({
                'Content-Type': 'text/plain'
              })
            })
          })
      })
  )
})

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-incidents') {
    event.waitUntil(syncIncidents())
  }
})

async function syncIncidents() {
  try {
    const cache = await caches.open(CACHE_NAME)
    const requests = await cache.keys()
    
    // Filter for pending incident updates
    const pendingUpdates = requests.filter(req => 
      req.url.includes('/api/incidents') && req.method !== 'GET'
    )

    // Retry sending updates
    for (const request of pendingUpdates) {
      try {
        await fetch(request)
        await cache.delete(request)
      } catch (error) {
        console.error('Failed to sync:', error)
      }
    }
  } catch (error) {
    console.error('Sync failed:', error)
  }
}

// Push notifications with enhanced support
self.addEventListener('push', (event) => {
  let notificationData = {
    title: 'SentinelOps Alert',
    body: 'New notification',
    type: 'info',
    priority: 'medium',
    id: Date.now().toString()
  }

  // Parse push data
  if (event.data) {
    try {
      const data = event.data.json()
      notificationData = { ...notificationData, ...data }
    } catch (e) {
      notificationData.body = event.data.text()
    }
  }

  // Process notification options based on type
  const options = processNotificationOptions(notificationData)

  event.waitUntil(
    self.registration.showNotification(notificationData.title, options)
  )
})

// Enhanced notification click handler
self.addEventListener('notificationclick', (event) => {
  const notification = event.notification
  const data = notification.data || {}
  
  notification.close()

  event.waitUntil(
    handleNotificationClick(event.action, data)
  )
})

// Notification close handler
self.addEventListener('notificationclose', (event) => {
  const data = event.notification.data || {}
  
  // Track notification dismissal
  fetch('/api/analytics/notification-dismiss', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      notificationId: data.id,
      type: data.type,
      timestamp: new Date().toISOString()
    })
  }).catch(console.error)
})

// Process notification options based on type and priority
function processNotificationOptions(data) {
  const baseOptions = {
    body: data.body,
    icon: '/icon-192x192.svg',
    badge: '/icon-72x72.svg',
    vibrate: [200, 100, 200],
    timestamp: Date.now(),
    requireInteraction: false,
    silent: false,
    tag: data.tag || `notification-${data.id}`,
    renotify: true,
    data: data
  }

  // Customize based on notification type
  switch (data.type) {
    case 'incident':
      return {
        ...baseOptions,
        icon: data.priority === 'critical' ? '/icon-192x192.svg' : baseOptions.icon,
        requireInteraction: data.priority === 'critical',
        vibrate: data.priority === 'critical' ? [500, 200, 500] : baseOptions.vibrate,
        actions: [
          { action: 'view', title: 'View Incident', icon: '/icon-72x72.svg' },
          { action: 'acknowledge', title: 'Acknowledge', icon: '/icon-72x72.svg' }
        ]
      }
    
    case 'alert':
      return {
        ...baseOptions,
        vibrate: [300, 200, 300],
        actions: [
          { action: 'view', title: 'View Alert', icon: '/icon-72x72.svg' },
          { action: 'snooze', title: 'Snooze 30m', icon: '/icon-72x72.svg' }
        ]
      }
    
    case 'update':
      return {
        ...baseOptions,
        silent: true,
        requireInteraction: false,
        actions: [
          { action: 'view', title: 'View Update', icon: '/icon-72x72.svg' }
        ]
      }
    
    case 'approval':
      return {
        ...baseOptions,
        requireInteraction: true,
        actions: [
          { action: 'approve', title: '✓ Approve', icon: '/icon-72x72.svg' },
          { action: 'reject', title: '✗ Reject', icon: '/icon-72x72.svg' }
        ]
      }
    
    default:
      return baseOptions
  }
}

// Handle notification click actions
async function handleNotificationClick(action, data) {
  // Send message to all clients about the click
  const clients = await self.clients.matchAll({ type: 'window' })
  
  for (const client of clients) {
    client.postMessage({
      type: 'notification-click',
      action: action,
      data: data
    })
  }

  // Handle specific actions
  if (action === 'acknowledge') {
    // Acknowledge the notification
    return fetch(`/api/notifications/${data.id}/acknowledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
  } else if (action === 'snooze') {
    // Snooze for 30 minutes
    return fetch(`/api/notifications/${data.id}/snooze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        until: new Date(Date.now() + 30 * 60 * 1000).toISOString() 
      })
    })
  } else if (action === 'approve' || action === 'reject') {
    // Handle approval actions
    return fetch(`/api/approvals/${data.id}/${action}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
  }

  // Default action - open or focus the app
  const urlToOpen = data.url || '/'
  const targetUrl = new URL(urlToOpen, self.location.origin).href

  // Check if there's already a window open
  for (const client of clients) {
    if (client.url === targetUrl && 'focus' in client) {
      return client.focus()
    }
  }

  // Open new window if no matching client found
  if (self.clients.openWindow) {
    return self.clients.openWindow(targetUrl)
  }
}

// Handle background sync for notifications
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-incidents') {
    event.waitUntil(syncIncidents())
  } else if (event.tag === 'sync-notifications') {
    event.waitUntil(syncNotifications())
  }
})

// Sync notifications with server
async function syncNotifications() {
  try {
    // Check for any pending notification acknowledgments
    const cache = await caches.open('notification-actions')
    const requests = await cache.keys()
    
    for (const request of requests) {
      try {
        const response = await fetch(request)
        if (response.ok) {
          await cache.delete(request)
        }
      } catch (error) {
        console.error('Failed to sync notification action:', error)
      }
    }
  } catch (error) {
    console.error('Notification sync failed:', error)
  }
}