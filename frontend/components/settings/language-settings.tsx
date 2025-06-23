"use client"

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { Globe, Calendar, Hash, DollarSign, Clock } from 'lucide-react'

interface LanguageSettings {
  language: string
  region: string
  dateFormat: string
  timeFormat: '12h' | '24h'
  numberFormat: string
  currency: string
  firstDayOfWeek: 'sunday' | 'monday'
  measurementUnit: 'metric' | 'imperial'
}

export default function LanguageSettings() {
  const [settings, setSettings] = useState<LanguageSettings>({
    language: 'en-US',
    region: 'US',
    dateFormat: 'MM/DD/YYYY',
    timeFormat: '12h',
    numberFormat: '1,234.56',
    currency: 'USD',
    firstDayOfWeek: 'sunday',
    measurementUnit: 'imperial'
  })

  const languages = [
    { value: 'en-US', label: 'English (United States)' },
    { value: 'en-GB', label: 'English (United Kingdom)' },
    { value: 'es-ES', label: 'Español (España)' },
    { value: 'es-MX', label: 'Español (México)' },
    { value: 'fr-FR', label: 'Français (France)' },
    { value: 'de-DE', label: 'Deutsch (Deutschland)' },
    { value: 'it-IT', label: 'Italiano (Italia)' },
    { value: 'pt-BR', label: 'Português (Brasil)' },
    { value: 'ja-JP', label: '日本語 (日本)' },
    { value: 'ko-KR', label: '한국어 (대한민국)' },
    { value: 'zh-CN', label: '中文 (简体)' },
    { value: 'zh-TW', label: '中文 (繁體)' },
  ]

  const regions = [
    { value: 'US', label: 'United States' },
    { value: 'GB', label: 'United Kingdom' },
    { value: 'CA', label: 'Canada' },
    { value: 'AU', label: 'Australia' },
    { value: 'DE', label: 'Germany' },
    { value: 'FR', label: 'France' },
    { value: 'ES', label: 'Spain' },
    { value: 'IT', label: 'Italy' },
    { value: 'JP', label: 'Japan' },
    { value: 'CN', label: 'China' },
    { value: 'BR', label: 'Brazil' },
    { value: 'IN', label: 'India' },
  ]

  const dateFormats = [
    { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY', example: '03/15/2024' },
    { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY', example: '15/03/2024' },
    { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD', example: '2024-03-15' },
    { value: 'DD.MM.YYYY', label: 'DD.MM.YYYY', example: '15.03.2024' },
    { value: 'DD-MMM-YYYY', label: 'DD-MMM-YYYY', example: '15-Mar-2024' },
  ]

  const numberFormats = [
    { value: '1,234.56', label: '1,234.56 (US/UK)' },
    { value: '1.234,56', label: '1.234,56 (EU)' },
    { value: "1'234.56", label: "1'234.56 (CH)" },
    { value: '1 234.56', label: '1 234.56 (FR)' },
  ]

  const currencies = [
    { value: 'USD', label: 'USD - US Dollar', symbol: '$' },
    { value: 'EUR', label: 'EUR - Euro', symbol: '€' },
    { value: 'GBP', label: 'GBP - British Pound', symbol: '£' },
    { value: 'JPY', label: 'JPY - Japanese Yen', symbol: '¥' },
    { value: 'CNY', label: 'CNY - Chinese Yuan', symbol: '¥' },
    { value: 'CAD', label: 'CAD - Canadian Dollar', symbol: '$' },
    { value: 'AUD', label: 'AUD - Australian Dollar', symbol: '$' },
    { value: 'CHF', label: 'CHF - Swiss Franc', symbol: 'Fr' },
  ]

  const updateSetting = <K extends keyof LanguageSettings>(
    key: K,
    value: LanguageSettings[K]
  ) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  const getExampleDate = () => {
    const date = new Date(2024, 2, 15) // March 15, 2024
    const format = settings.dateFormat
    
    switch (format) {
      case 'MM/DD/YYYY':
        return '03/15/2024'
      case 'DD/MM/YYYY':
        return '15/03/2024'
      case 'YYYY-MM-DD':
        return '2024-03-15'
      case 'DD.MM.YYYY':
        return '15.03.2024'
      case 'DD-MMM-YYYY':
        return '15-Mar-2024'
      default:
        return '03/15/2024'
    }
  }

  const getExampleTime = () => {
    return settings.timeFormat === '12h' ? '2:30 PM' : '14:30'
  }

  const getExampleNumber = () => {
    return settings.numberFormat
  }

  const getExampleCurrency = () => {
    const currency = currencies.find(c => c.value === settings.currency)
    const amount = settings.numberFormat.replace(/\d/g, '').split('')
    const thousands = amount[0] || ','
    const decimal = amount[amount.length - 1] || '.'
    return `${currency?.symbol}1${thousands}234${decimal}56`
  }

  return (
    <div className="space-y-6">
      {/* Language Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="w-5 h-5" />
            Language & Region
          </CardTitle>
          <CardDescription>
            Set your preferred language and regional settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label>Display Language</Label>
            <Select value={settings.language} onValueChange={(value) => updateSetting('language', value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {languages.map(lang => (
                  <SelectItem key={lang.value} value={lang.value}>
                    {lang.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">
              The language used throughout the interface
            </p>
          </div>

          <div className="space-y-2">
            <Label>Region</Label>
            <Select value={settings.region} onValueChange={(value) => updateSetting('region', value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {regions.map(region => (
                  <SelectItem key={region.value} value={region.value}>
                    {region.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">
              Your location for regional defaults
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Date & Time Formats */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Date & Time Format
          </CardTitle>
          <CardDescription>
            Customize how dates and times are displayed
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label>Date Format</Label>
            <Select value={settings.dateFormat} onValueChange={(value) => updateSetting('dateFormat', value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {dateFormats.map(format => (
                  <SelectItem key={format.value} value={format.value}>
                    <span className="flex items-center justify-between gap-4">
                      <span>{format.label}</span>
                      <span className="text-muted-foreground">{format.example}</span>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-3">
            <Label>Time Format</Label>
            <RadioGroup value={settings.timeFormat} onValueChange={(value: any) => updateSetting('timeFormat', value)}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="12h" id="12h" />
                <Label htmlFor="12h" className="cursor-pointer">
                  12-hour (2:30 PM)
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="24h" id="24h" />
                <Label htmlFor="24h" className="cursor-pointer">
                  24-hour (14:30)
                </Label>
              </div>
            </RadioGroup>
          </div>

          <div className="space-y-3">
            <Label>First Day of Week</Label>
            <RadioGroup 
              value={settings.firstDayOfWeek} 
              onValueChange={(value: any) => updateSetting('firstDayOfWeek', value)}
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="sunday" id="sunday" />
                <Label htmlFor="sunday" className="cursor-pointer">Sunday</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="monday" id="monday" />
                <Label htmlFor="monday" className="cursor-pointer">Monday</Label>
              </div>
            </RadioGroup>
          </div>
        </CardContent>
      </Card>

      {/* Number & Currency Format */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Hash className="w-5 h-5" />
            Number & Currency Format
          </CardTitle>
          <CardDescription>
            Set your preferred number and currency display format
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label>Number Format</Label>
            <Select value={settings.numberFormat} onValueChange={(value) => updateSetting('numberFormat', value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {numberFormats.map(format => (
                  <SelectItem key={format.value} value={format.value}>
                    {format.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Currency</Label>
            <Select value={settings.currency} onValueChange={(value) => updateSetting('currency', value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {currencies.map(currency => (
                  <SelectItem key={currency.value} value={currency.value}>
                    <span className="flex items-center gap-2">
                      <span className="font-mono">{currency.symbol}</span>
                      <span>{currency.label}</span>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-3">
            <Label>Measurement Units</Label>
            <RadioGroup 
              value={settings.measurementUnit} 
              onValueChange={(value: any) => updateSetting('measurementUnit', value)}
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="metric" id="metric" />
                <Label htmlFor="metric" className="cursor-pointer">
                  Metric (kilometers, celsius)
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="imperial" id="imperial" />
                <Label htmlFor="imperial" className="cursor-pointer">
                  Imperial (miles, fahrenheit)
                </Label>
              </div>
            </RadioGroup>
          </div>
        </CardContent>
      </Card>

      {/* Format Preview */}
      <Card>
        <CardHeader>
          <CardTitle>Format Preview</CardTitle>
          <CardDescription>
            See how your settings will appear
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 p-4 bg-muted rounded-lg">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="font-medium mb-1">Date</div>
                <div className="text-muted-foreground">{getExampleDate()}</div>
              </div>
              <div>
                <div className="font-medium mb-1">Time</div>
                <div className="text-muted-foreground">{getExampleTime()}</div>
              </div>
              <div>
                <div className="font-medium mb-1">Number</div>
                <div className="text-muted-foreground">{getExampleNumber()}</div>
              </div>
              <div>
                <div className="font-medium mb-1">Currency</div>
                <div className="text-muted-foreground">{getExampleCurrency()}</div>
              </div>
            </div>

            <div className="pt-4 border-t">
              <div className="font-medium mb-2">Sample Text</div>
              <p className="text-sm text-muted-foreground">
                Incident #1{settings.numberFormat.charAt(1)}234 was reported on {getExampleDate()} at {getExampleTime()}.
                The estimated impact is {getExampleCurrency()} in revenue.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Apply Button */}
      <div className="flex justify-end">
        <Button>Apply Language Settings</Button>
      </div>
    </div>
  )
}