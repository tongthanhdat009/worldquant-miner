# PDaC Language Specification

## Grammar

```
Program := (Component | API | Flow | Model | Rule | Game)*

// Components
Component := "component" Identifier "{" ComponentBody "}"
ComponentBody := (Props | State | Shortcuts | Layout | Behavior | Events)*

Props := "props" "{" PropDef* "}"
PropDef := Identifier ":" Type ("=" DefaultValue)?

State := "state" "{" StateDef* "}"
StateDef := Identifier ":" Type ("=" DefaultValue)?

Shortcuts := "shortcuts" "{" ShortcutDef* "}"
ShortcutDef := String ":" Identifier

Layout := "layout" "{" LayoutDef* "}"
LayoutDef := Identifier ":" (ComponentRef | LayoutExpression)

// APIs
API := "api" Identifier "{" Endpoint* "}"
Endpoint := Method Path "{" Request Response "}"

// Flows
Flow := "flow" Identifier "{" Step* "}"
Step := "step" String "{" StepBody "}"
StepBody := (Component | Action | Next | Condition)*

// Models
Model := "model" Identifier "{" Field* "}"
Field := Identifier ":" Type ("?" | "[]")*

// Rules
Rule := "rule" Identifier "{" Condition "=>" Action "}"

// Game Mechanics
Game := "game" Identifier "{" GameBody "}"
GameBody := (Mode | Mechanic | Rule)*
```

## Types

```
Type := 
  | "string"
  | "number"
  | "boolean"
  | "void"
  | Identifier  // Custom type
  | Type "[]"   // Array
  | Type "|" Type  // Union
  | "{" Field* "}"  // Object
  | "(" Type* ")" "=>" Type  // Function
```

## Keywords

- `component`: Define a UI component
- `api`: Define API contract
- `flow`: Define user flow
- `model`: Define data model
- `rule`: Define business rule
- `game`: Define game mechanics
- `props`: Component properties
- `state`: Component state
- `shortcuts`: Keyboard shortcuts
- `layout`: Component layout
- `endpoint`: API endpoint
- `step`: Flow step
- `condition`: Conditional logic
- `action`: Action to perform

## Examples

See [examples/](./examples/) directory for complete examples.
