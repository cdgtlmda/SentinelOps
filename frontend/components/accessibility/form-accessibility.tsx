'use client'

import React, { useId } from 'react'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'
import { AlertCircle, Info } from 'lucide-react'
import { ScreenReaderOnly } from './screen-reader-text'

interface AccessibleFormFieldProps {
  children: React.ReactElement
  label: string
  /**
   * Field description or help text
   */
  description?: string
  /**
   * Error message to display
   */
  error?: string
  /**
   * Whether the field is required
   */
  required?: boolean
  /**
   * Additional instructions for screen readers
   */
  srInstructions?: string
  /**
   * Whether to hide the label visually (still accessible to screen readers)
   */
  hideLabel?: boolean
  className?: string
}

/**
 * Accessible form field wrapper that ensures proper labeling,
 * error association, and screen reader announcements
 */
export const AccessibleFormField: React.FC<AccessibleFormFieldProps> = ({
  children,
  label,
  description,
  error,
  required = false,
  srInstructions,
  hideLabel = false,
  className
}) => {
  const fieldId = useId()
  const descriptionId = `${fieldId}-description`
  const errorId = `${fieldId}-error`
  const instructionsId = `${fieldId}-instructions`

  // Build aria-describedby value
  const ariaDescribedBy = [
    description && descriptionId,
    error && errorId,
    srInstructions && instructionsId
  ].filter(Boolean).join(' ') || undefined

  // Clone child element and add accessibility attributes
  const field = React.cloneElement(children, {
    id: fieldId,
    'aria-describedby': ariaDescribedBy,
    'aria-invalid': error ? 'true' : undefined,
    'aria-required': required ? 'true' : undefined,
    ...children.props
  })

  return (
    <div className={cn('space-y-2', className)}>
      <Label 
        htmlFor={fieldId}
        className={cn(
          hideLabel && 'sr-only',
          error && 'text-destructive'
        )}
      >
        {label}
        {required && (
          <span className="ml-1 text-destructive" aria-label="required">
            *
          </span>
        )}
      </Label>

      {field}

      {description && (
        <p id={descriptionId} className="text-sm text-muted-foreground">
          {description}
        </p>
      )}

      {error && (
        <p id={errorId} role="alert" className="text-sm text-destructive flex items-center gap-1">
          <AlertCircle className="h-4 w-4" aria-hidden="true" />
          <span>{error}</span>
        </p>
      )}

      {srInstructions && (
        <ScreenReaderOnly>
          <span id={instructionsId}>{srInstructions}</span>
        </ScreenReaderOnly>
      )}
    </div>
  )
}

interface FormFieldsetProps {
  legend: string
  /**
   * Whether to hide the legend visually (still accessible to screen readers)
   */
  hideLegend?: boolean
  children: React.ReactNode
  className?: string
}

/**
 * Accessible fieldset component for grouping related form fields
 */
export const FormFieldset: React.FC<FormFieldsetProps> = ({
  legend,
  hideLegend = false,
  children,
  className
}) => {
  return (
    <fieldset className={cn('space-y-4 p-4 border rounded-lg', className)}>
      <legend className={cn(
        'text-lg font-medium',
        hideLegend && 'sr-only'
      )}>
        {legend}
      </legend>
      {children}
    </fieldset>
  )
}

interface FormErrorSummaryProps {
  errors: Array<{
    field: string
    message: string
    fieldId?: string
  }>
  title?: string
  className?: string
}

/**
 * Accessible error summary component that announces errors
 * and provides navigation to problematic fields
 */
export const FormErrorSummary: React.FC<FormErrorSummaryProps> = ({
  errors,
  title = 'Please fix the following errors:',
  className
}) => {
  if (errors.length === 0) return null

  return (
    <div
      role="alert"
      aria-live="assertive"
      className={cn(
        'p-4 border border-destructive bg-destructive/10 rounded-lg',
        className
      )}
    >
      <h2 className="text-lg font-medium text-destructive mb-2 flex items-center gap-2">
        <AlertCircle className="h-5 w-5" aria-hidden="true" />
        {title}
      </h2>
      <ul className="list-disc list-inside space-y-1">
        {errors.map((error, index) => (
          <li key={index}>
            {error.fieldId ? (
              <a
                href={`#${error.fieldId}`}
                className="text-destructive underline hover:no-underline"
                onClick={(e) => {
                  e.preventDefault()
                  const field = document.getElementById(error.fieldId!)
                  if (field) {
                    field.focus()
                    field.scrollIntoView({ behavior: 'smooth', block: 'center' })
                  }
                }}
              >
                {error.field}: {error.message}
              </a>
            ) : (
              <span>
                {error.field}: {error.message}
              </span>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

interface RequiredFieldIndicatorProps {
  /**
   * Show explanation text about required fields
   */
  showExplanation?: boolean
  className?: string
}

/**
 * Component to indicate and explain required fields
 */
export const RequiredFieldIndicator: React.FC<RequiredFieldIndicatorProps> = ({
  showExplanation = true,
  className
}) => {
  return (
    <p className={cn('text-sm text-muted-foreground', className)}>
      <span className="text-destructive" aria-label="required">*</span>
      {showExplanation && ' indicates required fields'}
    </p>
  )
}

interface FormInstructionsProps {
  children: React.ReactNode
  icon?: React.ReactNode
  className?: string
}

/**
 * Component for providing form instructions or help text
 */
export const FormInstructions: React.FC<FormInstructionsProps> = ({
  children,
  icon = <Info className="h-4 w-4" />,
  className
}) => {
  return (
    <div className={cn(
      'flex items-start gap-2 p-3 bg-muted rounded-lg text-sm',
      className
    )}>
      <span className="text-muted-foreground mt-0.5" aria-hidden="true">
        {icon}
      </span>
      <div>{children}</div>
    </div>
  )
}

interface AccessibleRadioGroupProps {
  legend: string
  name: string
  options: Array<{
    value: string
    label: string
    description?: string
    disabled?: boolean
  }>
  value?: string
  onChange?: (value: string) => void
  required?: boolean
  error?: string
  className?: string
}

/**
 * Accessible radio button group with proper fieldset and labels
 */
export const AccessibleRadioGroup: React.FC<AccessibleRadioGroupProps> = ({
  legend,
  name,
  options,
  value,
  onChange,
  required = false,
  error,
  className
}) => {
  const groupId = useId()
  const errorId = `${groupId}-error`

  return (
    <fieldset 
      className={cn('space-y-3', className)}
      aria-required={required ? 'true' : undefined}
      aria-invalid={error ? 'true' : undefined}
      aria-describedby={error ? errorId : undefined}
    >
      <legend className="text-base font-medium">
        {legend}
        {required && (
          <span className="ml-1 text-destructive" aria-label="required">
            *
          </span>
        )}
      </legend>

      <div className="space-y-2">
        {options.map((option) => {
          const optionId = `${groupId}-${option.value}`
          const descriptionId = `${optionId}-description`

          return (
            <div key={option.value} className="flex items-start">
              <input
                type="radio"
                id={optionId}
                name={name}
                value={option.value}
                checked={value === option.value}
                onChange={(e) => onChange?.(e.target.value)}
                disabled={option.disabled}
                aria-describedby={option.description ? descriptionId : undefined}
                className="mt-1"
              />
              <div className="ml-3">
                <Label htmlFor={optionId} className="font-normal">
                  {option.label}
                </Label>
                {option.description && (
                  <p id={descriptionId} className="text-sm text-muted-foreground">
                    {option.description}
                  </p>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {error && (
        <p id={errorId} role="alert" className="text-sm text-destructive flex items-center gap-1">
          <AlertCircle className="h-4 w-4" aria-hidden="true" />
          <span>{error}</span>
        </p>
      )}
    </fieldset>
  )
}

interface AccessibleCheckboxGroupProps {
  legend: string
  options: Array<{
    value: string
    label: string
    description?: string
    disabled?: boolean
    checked?: boolean
  }>
  onChange?: (value: string, checked: boolean) => void
  error?: string
  className?: string
}

/**
 * Accessible checkbox group with proper fieldset and labels
 */
export const AccessibleCheckboxGroup: React.FC<AccessibleCheckboxGroupProps> = ({
  legend,
  options,
  onChange,
  error,
  className
}) => {
  const groupId = useId()
  const errorId = `${groupId}-error`

  return (
    <fieldset 
      className={cn('space-y-3', className)}
      aria-invalid={error ? 'true' : undefined}
      aria-describedby={error ? errorId : undefined}
    >
      <legend className="text-base font-medium">{legend}</legend>

      <div className="space-y-2">
        {options.map((option) => {
          const optionId = `${groupId}-${option.value}`
          const descriptionId = `${optionId}-description`

          return (
            <div key={option.value} className="flex items-start">
              <input
                type="checkbox"
                id={optionId}
                value={option.value}
                checked={option.checked}
                onChange={(e) => onChange?.(option.value, e.target.checked)}
                disabled={option.disabled}
                aria-describedby={option.description ? descriptionId : undefined}
                className="mt-1"
              />
              <div className="ml-3">
                <Label htmlFor={optionId} className="font-normal">
                  {option.label}
                </Label>
                {option.description && (
                  <p id={descriptionId} className="text-sm text-muted-foreground">
                    {option.description}
                  </p>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {error && (
        <p id={errorId} role="alert" className="text-sm text-destructive flex items-center gap-1">
          <AlertCircle className="h-4 w-4" aria-hidden="true" />
          <span>{error}</span>
        </p>
      )}
    </fieldset>
  )
}