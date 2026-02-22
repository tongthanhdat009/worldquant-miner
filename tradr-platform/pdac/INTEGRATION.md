# PDaC Integration Guide

How to integrate PDaC with your tradr-platform development workflow.

## Workflow

1. **Design in PDaC**: Write specifications in PDaC language
2. **Compile to Code**: Generate TypeScript/React/NestJS code
3. **Implement**: Fill in generated code with business logic
4. **Validate**: Ensure implementation matches spec

## Integration with Frontend

### Step 1: Write Component Spec

Create `specs/trading-interface.pdac`:

```pdac
component TradingInterface {
  props {
    matchId: string
    onExit: () => void
  }
  
  shortcuts {
    "B": quickBuy
    "S": quickSell
  }
}
```

### Step 2: Generate Code

```bash
cd pdac
npm run build
pdac compile examples/trading-interface.pdac --target react --output ../frontend/src/generated
```

### Step 3: Use Generated Code

```typescript
import TradingInterface from '@/generated/TradingInterface';

// Generated component with shortcuts already wired up
<TradingInterface matchId={matchId} onExit={handleExit} />
```

## Integration with Backend

### Step 1: Write API Spec

Create `specs/match-api.pdac`:

```pdac
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
```

### Step 2: Generate Controller

```bash
pdac compile examples/match-api.pdac --target nestjs --output ../backend/src/generated
```

### Step 3: Implement Business Logic

```typescript
import { MatchAPIController } from '@/generated/MatchAPIController';

@Controller('matches')
export class MatchesController extends MatchAPIController {
  // Implement generated methods
  async createMatch(body: CreateMatchRequest): Promise<Match> {
    // Your business logic here
  }
}
```

## Continuous Integration

### Pre-commit Hook

Validate specs before commit:

```bash
# .git/hooks/pre-commit
pdac validate specs/*.pdac --implementation src/
```

### CI Pipeline

```yaml
# .github/workflows/pdac.yml
name: PDaC Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
      - run: npm install -g @tradr/pdac
      - run: pdac validate specs/*.pdac --implementation src/
```

## Best Practices

1. **Keep Specs Updated**: Update PDaC specs when requirements change
2. **Version Control**: Commit both PDaC specs and generated code
3. **Review Specs**: Review PDaC specs in PRs, not just code
4. **Documentation**: Use PDaC as living documentation
5. **Testing**: Generate tests from PDaC specs

## Advanced Usage

### Generate Type Definitions

```bash
pdac compile examples/match-api.pdac --target typescript --output types/
```

### Generate Tests

```bash
pdac test examples/trading-interface.pdac --output tests/
```

### Generate Documentation

```bash
pdac docs examples/*.pdac --output docs/
```

## Example: Full Feature Development

1. **Design**: Write PDaC spec for new feature
2. **Review**: Get design approval on PDaC spec
3. **Generate**: Generate code from spec
4. **Implement**: Fill in business logic
5. **Test**: Write tests based on spec
6. **Validate**: Ensure implementation matches spec

This ensures:
- ✅ Design and implementation stay in sync
- ✅ Code generation reduces boilerplate
- ✅ Specs serve as documentation
- ✅ Changes are traceable
