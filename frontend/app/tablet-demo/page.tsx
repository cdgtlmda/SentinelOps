"use client"

import { useState } from 'react'
import Link from 'next/link'
import { TabletLayout, TabletGridLayout } from '@/components/tablet/tablet-layout'
import { AdaptivePanels, PanelStack } from '@/components/tablet/adaptive-panels'
import { MasterDetailView } from '@/components/tablet/master-detail-view'
import { TabletNavigation } from '@/components/tablet/tablet-navigation'
import { useOrientation, useOptimalLayout } from '@/hooks/use-orientation'
import { Card } from '@/components/ui/card'
import { 
  Smartphone, 
  Tablet, 
  Monitor, 
  RotateCcw, 
  Layers, 
  Grid3x3, 
  Columns,
  PanelLeft,
  PanelRight,
  ArrowRight,
  Settings
} from 'lucide-react'

// Demo data
const demoItems = [
  { id: '1', title: 'Item 1', description: 'Description for item 1', category: 'A' },
  { id: '2', title: 'Item 2', description: 'Description for item 2', category: 'B' },
  { id: '3', title: 'Item 3', description: 'Description for item 3', category: 'A' },
  { id: '4', title: 'Item 4', description: 'Description for item 4', category: 'C' },
  { id: '5', title: 'Item 5', description: 'Description for item 5', category: 'B' },
]

export default function TabletDemoPage() {
  const orientation = useOrientation()
  const layout = useOptimalLayout()
  const [selectedItemId, setSelectedItemId] = useState<string>('1')
  const [activeDemo, setActiveDemo] = useState<string>('adaptive-panels')

  const demos = {
    'adaptive-panels': {
      title: 'Adaptive Panels',
      icon: Layers,
      description: 'Dynamic panel resizing and collapsing'
    },
    'master-detail': {
      title: 'Master-Detail View',
      icon: Columns,
      description: 'List and detail views with animations'
    },
    'grid-layout': {
      title: 'Grid Layout',
      icon: Grid3x3,
      description: 'Responsive grid system'
    },
    'panel-stack': {
      title: 'Panel Stack',
      icon: PanelRight,
      description: 'Multiple collapsible panels'
    }
  }

  const renderDemo = () => {
    switch (activeDemo) {
      case 'adaptive-panels':
        return (
          <AdaptivePanels
            orientation={orientation.orientation}
            primaryPanel={
              <div className="p-6">
                <h3 className="text-lg font-semibold mb-4">Primary Panel</h3>
                <p className="text-gray-600 mb-4">
                  This is the primary panel content. It remains visible while the secondary panel can be resized or collapsed.
                </p>
                <div className="space-y-3">
                  {[1, 2, 3].map(i => (
                    <Card key={i} className="p-4">
                      <h4 className="font-medium">Card {i}</h4>
                      <p className="text-sm text-gray-600 mt-1">
                        Sample content for demonstration purposes.
                      </p>
                    </Card>
                  ))}
                </div>
              </div>
            }
            secondaryPanel={
              <div className="p-6">
                <h3 className="text-lg font-semibold mb-4">Secondary Panel</h3>
                <p className="text-gray-600 mb-4">
                  Drag the resize handle to adjust the panel width. Click the collapse button to hide this panel.
                </p>
                <div className="space-y-2">
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm font-medium text-blue-900">Tip:</p>
                    <p className="text-sm text-blue-700">
                      The panel automatically adjusts its layout based on orientation.
                    </p>
                  </div>
                </div>
              </div>
            }
            defaultSecondaryWidth={400}
            minSecondaryWidth={300}
            maxSecondaryWidth={600}
          />
        )

      case 'master-detail':
        return (
          <MasterDetailView
            items={demoItems}
            selectedId={selectedItemId}
            onSelectItem={(item) => setSelectedItemId(item.id)}
            renderListItem={(item, isSelected) => (
              <div className="p-4">
                <h4 className="font-medium">{item.title}</h4>
                <p className="text-sm text-gray-600">{item.description}</p>
                <span className="inline-block mt-2 px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                  Category {item.category}
                </span>
              </div>
            )}
            renderDetail={(item) => (
              <div className="p-6">
                <h2 className="text-2xl font-bold mb-4">{item.title}</h2>
                <p className="text-gray-600 mb-6">{item.description}</p>
                <div className="space-y-4">
                  <div>
                    <h3 className="font-medium mb-2">Details</h3>
                    <Card className="p-4">
                      <dl className="space-y-2">
                        <div className="flex justify-between">
                          <dt className="text-sm text-gray-600">ID:</dt>
                          <dd className="text-sm font-medium">{item.id}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-sm text-gray-600">Category:</dt>
                          <dd className="text-sm font-medium">{item.category}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-sm text-gray-600">Created:</dt>
                          <dd className="text-sm font-medium">Today</dd>
                        </div>
                      </dl>
                    </Card>
                  </div>
                </div>
              </div>
            )}
            getItemId={(item) => item.id}
            listTitle="Items"
            detailTitle={(item) => item.title}
          />
        )

      case 'grid-layout':
        return (
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">Responsive Grid Layout</h3>
            <p className="text-gray-600 mb-6">
              The grid automatically adjusts columns based on orientation and screen size.
            </p>
            <TabletGridLayout columns={{ portrait: 2, landscape: 3 }}>
              {[1, 2, 3, 4, 5, 6].map(i => (
                <Card key={i} className="p-6">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                    <Grid3x3 className="w-6 h-6 text-blue-600" />
                  </div>
                  <h4 className="font-medium mb-2">Grid Item {i}</h4>
                  <p className="text-sm text-gray-600">
                    Content adapts to available space in the grid.
                  </p>
                </Card>
              ))}
            </TabletGridLayout>
          </div>
        )

      case 'panel-stack':
        return (
          <PanelStack
            orientation={orientation.orientation}
            panels={[
              {
                id: 'panel1',
                title: 'Primary Panel',
                priority: 3,
                content: (
                  <div>
                    <p className="text-gray-600 mb-4">
                      This panel has the highest priority and appears first.
                    </p>
                    <Card className="p-4">
                      <h5 className="font-medium">Important Content</h5>
                      <p className="text-sm text-gray-600 mt-1">
                        Critical information is displayed here.
                      </p>
                    </Card>
                  </div>
                )
              },
              {
                id: 'panel2',
                title: 'Secondary Panel',
                priority: 2,
                content: (
                  <div>
                    <p className="text-gray-600 mb-4">
                      Secondary information with medium priority.
                    </p>
                    <div className="space-y-2">
                      <div className="p-3 bg-gray-50 rounded">
                        <p className="text-sm">Additional details</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded">
                        <p className="text-sm">Supporting information</p>
                      </div>
                    </div>
                  </div>
                )
              },
              {
                id: 'panel3',
                title: 'Tertiary Panel',
                priority: 1,
                content: (
                  <div>
                    <p className="text-gray-600 mb-4">
                      Optional content with lower priority.
                    </p>
                    <ul className="space-y-2 text-sm text-gray-600">
                      <li>• Reference material</li>
                      <li>• Help documentation</li>
                      <li>• Additional resources</li>
                    </ul>
                  </div>
                )
              }
            ]}
          />
        )

      default:
        return null
    }
  }

  // Info panel content
  const infoPanel = (
    <div className="p-6">
      <h3 className="text-lg font-semibold mb-4">Device Information</h3>
      <div className="space-y-4">
        <Card className="p-4">
          <div className="flex items-center gap-3 mb-3">
            {layout.isMobile ? <Smartphone className="w-5 h-5" /> : 
             layout.isTablet ? <Tablet className="w-5 h-5" /> : 
             <Monitor className="w-5 h-5" />}
            <h4 className="font-medium">Current Device</h4>
          </div>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-600">Type:</dt>
              <dd className="font-medium">
                {layout.isMobile ? 'Mobile' : layout.isTablet ? 'Tablet' : 'Desktop'}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Orientation:</dt>
              <dd className="font-medium capitalize">{orientation.orientation}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Dimensions:</dt>
              <dd className="font-medium">{orientation.width} × {orientation.height}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Aspect Ratio:</dt>
              <dd className="font-medium">{orientation.aspectRatio.toFixed(2)}</dd>
            </div>
          </dl>
        </Card>

        <Card className="p-4">
          <h4 className="font-medium mb-3">Layout Configuration</h4>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-600">Columns:</dt>
              <dd className="font-medium">{layout.columns}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Sidebar:</dt>
              <dd className="font-medium">{layout.showSidebar ? 'Visible' : 'Hidden'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Navigation:</dt>
              <dd className="font-medium capitalize">{layout.navigationPosition}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Padding:</dt>
              <dd className="font-medium">{layout.contentPadding}px</dd>
            </div>
          </dl>
        </Card>

        <div className="p-3 bg-blue-50 rounded-lg">
          <div className="flex items-center gap-2 mb-1">
            <RotateCcw className="w-4 h-4 text-blue-600" />
            <p className="text-sm font-medium text-blue-900">Try rotating your device</p>
          </div>
          <p className="text-sm text-blue-700">
            The layout will automatically adapt to the new orientation.
          </p>
        </div>
      </div>
    </div>
  )

  return (
    <TabletLayout
      sidebar={
        <div className="h-full flex flex-col">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold">Tablet Demos</h2>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            <div className="space-y-2">
              {Object.entries(demos).map(([key, demo]) => {
                const Icon = demo.icon
                return (
                  <button
                    key={key}
                    onClick={() => setActiveDemo(key)}
                    className={cn(
                      "w-full text-left p-3 rounded-lg transition-colors",
                      activeDemo === key 
                        ? "bg-blue-50 text-blue-700" 
                        : "hover:bg-gray-100"
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className="w-5 h-5" />
                      <div className="flex-1">
                        <p className="font-medium">{demo.title}</p>
                        <p className="text-xs text-gray-600 mt-0.5">{demo.description}</p>
                      </div>
                      {activeDemo === key && <ArrowRight className="w-4 h-4" />}
                    </div>
                  </button>
                )
              })}
            </div>
            
            <div className="mt-6 pt-6 border-t">
              <Link
                href="/dashboard"
                className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700"
              >
                <ArrowRight className="w-4 h-4" />
                Back to Dashboard
              </Link>
            </div>
          </div>
        </div>
      }
      secondaryPanel={layout.showSecondaryPanel && infoPanel}
    >
      <div className="h-full flex flex-col">
        <div className="px-6 py-4 border-b bg-white">
          <h1 className="text-2xl font-bold">Tablet Layout Demo</h1>
          <p className="text-gray-600 mt-1">
            Explore adaptive layouts optimized for tablet devices
          </p>
        </div>
        
        <div className="flex-1 overflow-hidden bg-gray-50">
          {renderDemo()}
        </div>
      </div>
    </TabletLayout>
  )
}

// Helper function
function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}