# PDaC Quick Start

Get started with Product Design as Code in 5 minutes.

## Installation

```bash
cd pdac
npm install
npm run build
```

## Your First PDaC Spec

Create `hello.pdac`:

```pdac
component HelloWorld {
  props {
    name: string
  }
  
  state {
    count: number = 0
  }
  
  shortcuts {
    "Enter": increment
  }
}
```

## Compile to React

```bash
npm run dev compile hello.pdac --target react --output ../frontend/src/generated
```

## Generated Code

The compiler generates:

```typescript
// HelloWorld.tsx
import { useState, useEffect } from 'react';
import { useRTSShortcuts } from '@/hooks/useRTSShortcuts';

interface HelloWorldProps {
  name: string;
}

export default function HelloWorld({ name }: HelloWorldProps) {
  const [count, setCount] = useState<number>(0);

  const { registerShortcut, unregisterShortcut } = useRTSShortcuts();

  useEffect(() => {
    const shortcuts = {
      "Enter": () => {
        increment();
      },
    };

    Object.entries(shortcuts).forEach(([key, handler]) => {
      registerShortcut(key, handler);
    });

    return () => {
      Object.keys(shortcuts).forEach((key) => {
        unregisterShortcut(key);
      });
    };
  }, [registerShortcut, unregisterShortcut]);

  return (
    <div className="helloworld">
      {/* Generated from PDaC */}
    </div>
  );
}
```

## Next Steps

1. Read [LANGUAGE_SPEC.md](./LANGUAGE_SPEC.md) for full syntax
2. Check [examples/](./examples/) for real-world specs
3. See [INTEGRATION.md](./INTEGRATION.md) for workflow integration

## Examples Included

- `trading-interface.pdac` - Complete trading UI spec
- `match-api.pdac` - API contract definitions
- `user-flow.pdac` - User journey flows
- `game-mechanics.pdac` - Game rules and systems

## Commands

```bash
# Compile PDaC to code
pdac compile <file> --target <react|nestjs|typescript> --output <dir>

# Validate implementation
pdac validate <spec> --implementation <dir>

# Generate docs
pdac docs <spec> --output <dir>
```

Happy coding! 🚀
