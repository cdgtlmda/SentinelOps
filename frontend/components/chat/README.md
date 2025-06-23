# AI-Powered Chat Components

This directory contains advanced conversational AI features for the SentinelOps chat interface.

## Components

### ChatInterface (`chat-interface.tsx`)
The main chat interface with integrated AI features:
- Natural language understanding indicators
- Intent recognition display
- Confidence scores for AI responses
- Clarification prompts when intent is unclear
- Integration with all AI components

### ContextManager (`context-manager.tsx`)
Manages conversation context:
- Tracks conversation history and intent
- Displays context summary
- Links related incidents and agents
- Provides context reset functionality
- Shows detected entities and metadata

### SuggestedActions (`suggested-actions.tsx`)
AI-powered action suggestions:
- Quick reply buttons based on context
- Common question templates
- Action predictions from conversation
- Learning from user selections
- Categorized suggestions (quick-reply, action, question, command)

### AutoComplete (`auto-complete.tsx`)
Intelligent command/query completion:
- Context-aware suggestions
- Recent searches tracking
- Entity recognition (incident IDs, agent names)
- Fuzzy matching for typo tolerance
- Real-time filtering as you type

### CommandPalette (`command-palette.tsx`)
Advanced command interface:
- Slash command (/) menu
- Natural language command parsing
- Command builder UI with parameters
- Command history tracking
- Dual mode: structured commands and natural language

## Hooks

### useAIChat (`/hooks/use-ai-chat.ts`)
Core AI functionality:
- Natural language processing
- Intent classification
- Entity extraction
- Context management
- Response generation

## Libraries

### AI Commands (`/lib/ai-commands.ts`)
AI command processing:
- Command registry
- Natural language patterns
- Intent mappings
- Parameter extraction
- Confidence scoring

## Features

### Natural Language Understanding
- **Intent Recognition**: Automatically detects user intent from natural language
- **Entity Extraction**: Identifies key information like incident IDs, agent names, priorities
- **Confidence Scoring**: Shows how confident the AI is about its understanding
- **Clarification Prompts**: Asks for clarification when intent is unclear

### Context Management
- **Conversation Tracking**: Maintains full conversation context
- **Related Linking**: Automatically links mentioned incidents and agents
- **Context Summary**: Provides overview of conversation topic and duration
- **Smart Reset**: Clear context when switching topics

### Intelligent Suggestions
- **Action Predictions**: Suggests next actions based on conversation flow
- **Quick Replies**: One-click responses for common interactions
- **Learning System**: Improves suggestions based on user selections
- **Categorization**: Groups suggestions by type for better organization

### Auto-Complete
- **Fuzzy Matching**: Finds matches even with typos
- **Entity Recognition**: Completes incident IDs, agent names, etc.
- **Recent Searches**: Quick access to previous queries
- **Smart Filtering**: Context-aware suggestion ranking

### Command Palette
- **Dual Interface**: Both structured commands and natural language
- **Parameter Builder**: Visual UI for complex commands
- **Command History**: Quick access to previous commands
- **Keyboard Shortcuts**: ⌘K to open palette

## Usage Examples

### Natural Language
```
"Create a high priority incident for API authentication failures"
"Check the status of incident INC-12345"
"Who's available to help with database issues?"
"Assign this to Alice from the security team"
```

### Structured Commands
```
/incident new priority=high title="API Auth Failure"
/incident status id=INC-12345
/agent list status=online
/agent assign agent=alice task=INC-12345
```

## Keyboard Shortcuts
- `⌘K` or `Ctrl+K`: Open command palette
- `Tab`: Accept auto-complete suggestion
- `↑↓`: Navigate suggestions
- `Enter`: Send message
- `Shift+Enter`: New line in message
- `Esc`: Close suggestions/palette

## Multi-Language Support
The components are structured to support internationalization (i18n):
- All user-facing strings can be externalized
- Intent patterns can be localized
- Entity extraction supports multiple languages
- UI adapts to RTL languages

## Learning & Improvement
The system learns from interactions:
- Tracks which suggestions are selected
- Adjusts confidence scores based on feedback
- Personalizes suggestions over time
- Improves entity recognition accuracy

## Integration
To use these components in your application:

```tsx
import { ChatInterface } from '@/components/chat/chat-interface'

export function MyApp() {
  return (
    <div className="h-screen">
      <ChatInterface />
    </div>
  )
}
```

The chat interface automatically includes all AI features. No additional configuration required.