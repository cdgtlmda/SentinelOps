import { BrowserCompatibilityTest } from '@/components/browser-compatibility-test'

export default function BrowserCompatPage() {
  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">Browser Compatibility Test</h1>
      <BrowserCompatibilityTest />
    </div>
  )
}