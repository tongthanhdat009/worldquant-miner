# Product Design as Code (PDaC)

A declarative language for spec-driven development that bridges product design and implementation.

## Philosophy

PDaC allows designers and developers to write product specifications in a code-like format that can be:
- **Validated** against implementations
- **Compiled** to generate code
- **Documented** automatically
- **Tested** systematically

## Language Features

- **Component Definitions**: Define UI components with props, states, and behaviors
- **User Flows**: Describe user journeys and interactions
- **API Contracts**: Define API endpoints and data structures
- **Business Rules**: Express business logic declaratively
- **Data Models**: Define data structures and relationships
- **Game Mechanics**: Define game rules and systems

## Syntax Overview

```pdac
// Component definition
component TradingInterface {
  props {
    matchId: string
    onExit: () => void
  }
  
  state {
    focusedChart: number = 0
    flashMessage: FlashMessage | null = null
  }
  
  shortcuts {
    "1-4": switchChart
    "B": quickBuy
    "S": quickSell
    "C": closePosition
    "Esc": exit
  }
  
  layout {
    header: Header
    main: MultiChartGrid
    sidebar: OrderPanel | PositionPanel | StatsPanel
    footer: ShortcutHelp
  }
}

// API contract
api MatchAPI {
  endpoint POST /matches {
    request {
      mode: GameMode
      userId: string
    }
    response {
      match: Match
    }
  }
}

// User flow
flow CreateMatch {
  step "Select Mode" {
    component: MatchLobby
    action: selectGameMode
    next: "Create Match"
  }
  
  step "Create Match" {
    action: callAPI(MatchAPI.POST /matches)
    next: "Start Trading"
  }
  
  step "Start Trading" {
    component: TradingInterface
    entry: onMatchStart
  }
}
```

## Installation

```bash
npm install -g @tradr/pdac
```

## Usage

```bash
# Compile PDaC to TypeScript/React
pdac compile spec.pdac --target react --output src/generated

# Validate implementation against spec
pdac validate spec.pdac --implementation src/components

# Generate documentation
pdac docs spec.pdac --output docs/
```

## Documentation

See [LANGUAGE_SPEC.md](./LANGUAGE_SPEC.md) for complete language specification.
