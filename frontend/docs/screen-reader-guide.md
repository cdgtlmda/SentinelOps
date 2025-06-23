# Screen Reader Testing Guide for SentinelOps

This guide provides instructions for testing the SentinelOps application with screen readers to ensure accessibility compliance.

## Table of Contents

1. [Screen Reader Overview](#screen-reader-overview)
2. [Setting Up Screen Readers](#setting-up-screen-readers)
3. [Essential Keyboard Shortcuts](#essential-keyboard-shortcuts)
4. [Testing Checklist](#testing-checklist)
5. [Common Issues and Solutions](#common-issues-and-solutions)
6. [Testing Workflow](#testing-workflow)

## Screen Reader Overview

Screen readers are assistive technologies that convert digital text into speech or braille output, enabling users who are blind or have visual impairments to interact with applications.

### Popular Screen Readers

1. **NVDA (Windows)** - Free, open-source
   - Download: https://www.nvaccess.org/
   - Most commonly used free screen reader

2. **JAWS (Windows)** - Commercial
   - Website: https://www.freedomscientific.com/
   - Industry standard, comprehensive features

3. **VoiceOver (macOS/iOS)** - Built-in
   - Enable: System Preferences > Accessibility > VoiceOver
   - Press Cmd+F5 to toggle

4. **TalkBack (Android)** - Built-in
   - Enable: Settings > Accessibility > TalkBack

## Setting Up Screen Readers

### VoiceOver (macOS)

1. **Enable VoiceOver**
   ```
   Press Cmd+F5 or go to System Preferences > Accessibility > VoiceOver
   ```

2. **VoiceOver Training**
   - Open VoiceOver Training from the VoiceOver Utility
   - Complete the interactive tutorial

3. **Adjust Settings**
   - Speech rate: VoiceOver Utility > Speech
   - Verbosity: VoiceOver Utility > Verbosity
   - Web settings: VoiceOver Utility > Web

### NVDA (Windows)

1. **Installation**
   - Download from nvaccess.org
   - Run installer with default settings

2. **Start NVDA**
   - Press Ctrl+Alt+N after installation
   - Or start from Start Menu

3. **Configure Settings**
   - NVDA Menu (NVDA+N) > Preferences
   - Adjust speech rate and verbosity

## Essential Keyboard Shortcuts

### General Navigation

| Action | VoiceOver (Mac) | NVDA (Windows) | JAWS (Windows) |
|--------|-----------------|----------------|----------------|
| Start/Stop | Cmd+F5 | Ctrl+Alt+N | N/A |
| Read all | VO+A | NVDA+Down | Insert+Down |
| Stop reading | Ctrl | Ctrl | Ctrl |
| Next item | VO+Right | Down | Down |
| Previous item | VO+Left | Up | Up |
| Activate item | VO+Space | Enter | Enter |

### Web Navigation

| Action | VoiceOver (Mac) | NVDA (Windows) | JAWS (Windows) |
|--------|-----------------|----------------|----------------|
| Next heading | VO+Cmd+H | H | H |
| Next button | VO+Cmd+B | B | B |
| Next link | VO+Cmd+L | K | U |
| Next form field | VO+Cmd+J | F | F |
| Next table | VO+Cmd+T | T | T |
| Landmarks | VO+U (Rotor) | D | R |
| List all headings | VO+U, then select | NVDA+F7 | Insert+F6 |

*Note: VO = Control+Option keys*

## Testing Checklist

### 1. Page Structure

- [ ] **Page title** - Descriptive and unique
- [ ] **Heading hierarchy** - Logical order (h1 → h2 → h3)
- [ ] **Landmarks** - All major sections have landmarks
- [ ] **Skip navigation** - "Skip to main content" link works

### 2. Navigation

- [ ] **Tab order** - Logical flow through interactive elements
- [ ] **Focus indicators** - Visible for all interactive elements
- [ ] **Menu navigation** - Arrow keys work in dropdowns
- [ ] **Breadcrumbs** - Properly announced with navigation role

### 3. Forms

- [ ] **Labels** - All inputs have associated labels
- [ ] **Required fields** - Clearly indicated and announced
- [ ] **Error messages** - Associated with fields and announced
- [ ] **Field descriptions** - Help text is announced
- [ ] **Fieldsets** - Related fields are grouped with legends

### 4. Tables

- [ ] **Captions** - Tables have descriptive captions
- [ ] **Headers** - Column and row headers properly marked
- [ ] **Sorting** - Sort controls are keyboard accessible
- [ ] **Navigation** - Can navigate cells with arrow keys

### 5. Dynamic Content

- [ ] **Live regions** - Updates are announced
- [ ] **Loading states** - "Loading" is announced
- [ ] **Notifications** - Alerts are immediately announced
- [ ] **Status messages** - Non-critical updates announced politely

### 6. Interactive Elements

- [ ] **Buttons** - Purpose is clear from text or label
- [ ] **Links** - Destination is clear from link text
- [ ] **Modals** - Focus trapped, escape key closes
- [ ] **Accordions** - Expanded state announced

## Common Issues and Solutions

### Issue: Content Not Announced

**Symptoms**: Screen reader skips over content

**Solutions**:
- Ensure semantic HTML is used
- Add appropriate ARIA labels
- Check for `aria-hidden="true"` on parent elements
- Verify content isn't visually hidden with CSS

### Issue: Confusing Announcements

**Symptoms**: Screen reader announces incorrect or confusing information

**Solutions**:
- Review ARIA labels for clarity
- Ensure proper heading hierarchy
- Check for redundant or conflicting ARIA attributes
- Use semantic HTML instead of ARIA when possible

### Issue: Focus Lost

**Symptoms**: Tab navigation skips elements or gets stuck

**Solutions**:
- Check `tabindex` values (avoid positive values)
- Ensure all interactive elements are focusable
- Verify modal focus management
- Test for keyboard traps

### Issue: Dynamic Content Not Announced

**Symptoms**: Updates to page content aren't communicated

**Solutions**:
- Implement live regions (`aria-live`)
- Use appropriate politeness levels
- Ensure `aria-atomic` is set correctly
- Consider using status or alert roles

## Testing Workflow

### 1. Initial Page Load

1. Navigate to page
2. Listen to page title announcement
3. Use heading navigation to understand structure
4. Navigate through landmarks
5. Verify skip links work

### 2. Form Testing

1. Tab through all form fields
2. Verify each field's label is announced
3. Check required field indicators
4. Submit form with errors
5. Verify error messages are announced
6. Navigate to error fields from summary

### 3. Table Testing

1. Navigate to table
2. Verify caption is announced
3. Use table navigation commands
4. Check header associations
5. Test sortable columns
6. Verify sort changes are announced

### 4. Interactive Component Testing

1. **Buttons**: Activate and verify result
2. **Links**: Verify destination is clear
3. **Dropdowns**: Test arrow key navigation
4. **Modals**: Check focus management
5. **Tabs**: Verify panel associations

### 5. Dynamic Content Testing

1. Trigger loading states
2. Verify "loading" announcement
3. Confirm completion announcement
4. Test real-time updates
5. Check notification announcements

## Best Practices for Testing

1. **Test Early and Often**
   - Don't wait until the end of development
   - Include in regular testing workflow

2. **Use Multiple Screen Readers**
   - Different screen readers may behave differently
   - Test with at least NVDA and VoiceOver

3. **Test with Actual Users**
   - Nothing replaces testing with real screen reader users
   - Gather feedback on announcement clarity

4. **Document Issues Clearly**
   - Include screen reader and browser versions
   - Provide exact announcement text
   - Include steps to reproduce

5. **Test Different Interaction Modes**
   - Browse mode vs. focus mode (Windows)
   - Quick nav vs. standard navigation

## Automated Testing Tools

While manual testing is essential, these tools can help catch common issues:

1. **axe DevTools** - Browser extension
   - https://www.deque.com/axe/devtools/

2. **WAVE** - Web Accessibility Evaluation Tool
   - https://wave.webaim.org/

3. **Lighthouse** - Built into Chrome DevTools
   - Accessibility audit included

4. **Pa11y** - Command-line tool
   - https://pa11y.org/

## Additional Resources

- [WebAIM Screen Reader Testing Guide](https://webaim.org/articles/screenreader_testing/)
- [MDN ARIA Authoring Practices](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Screen Reader User Survey](https://webaim.org/projects/screenreadersurvey9/)

## SentinelOps-Specific Testing Points

### Incident Dashboard
- Verify incident count announcements
- Test severity badge descriptions
- Check status change notifications

### Agent Management
- Test agent status announcements
- Verify action confirmations
- Check real-time status updates

### Workflow Visualization
- Ensure workflow steps are navigable
- Verify progress announcements
- Test dependency descriptions

### Chat Interface
- Check message announcements
- Test command suggestions
- Verify typing indicators

Remember: The goal is to ensure all users can effectively use SentinelOps, regardless of their visual abilities. Regular testing with screen readers helps maintain an accessible experience for everyone.