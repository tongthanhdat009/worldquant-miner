/**
 * PDaC Parser
 * Parses PDaC language files into AST
 */

export interface ASTNode {
  type: string;
  [key: string]: any;
}

export interface ComponentNode extends ASTNode {
  type: 'component';
  name: string;
  props?: PropDef[];
  state?: StateDef[];
  shortcuts?: ShortcutDef[];
  layout?: LayoutDef[];
  behaviors?: BehaviorDef[];
  events?: EventDef[];
}

export interface PropDef {
  name: string;
  type: Type;
  defaultValue?: any;
  required?: boolean;
}

export interface StateDef {
  name: string;
  type: Type;
  defaultValue?: any;
}

export interface ShortcutDef {
  key: string;
  action: string;
}

export interface LayoutDef {
  name: string;
  value: string | LayoutExpression;
}

export interface LayoutExpression {
  type: 'union' | 'grid' | 'stack';
  items: string[];
}

export interface Type {
  name: string;
  isArray?: boolean;
  isOptional?: boolean;
  union?: Type[];
  fields?: { [key: string]: Type };
}

export interface APINode extends ASTNode {
  type: 'api';
  name: string;
  endpoints: EndpointDef[];
}

export interface EndpointDef {
  method: string;
  path: string;
  request?: FieldDef[];
  response?: FieldDef[];
}

export interface FieldDef {
  name: string;
  type: Type;
  required?: boolean;
}

export interface FlowNode extends ASTNode {
  type: 'flow';
  name: string;
  steps: StepDef[];
}

export interface StepDef {
  name: string;
  component?: string;
  action?: string;
  next?: string;
  condition?: string;
}

export interface ModelNode extends ASTNode {
  type: 'model';
  name: string;
  fields: FieldDef[];
}

export interface GameNode extends ASTNode {
  type: 'game';
  name: string;
  modes?: GameModeDef[];
  mechanics?: MechanicDef[];
}

export interface GameModeDef {
  id: string;
  name: string;
  type: 'pvp' | 'pve';
  players: number;
  duration: number;
  initialCapital: number;
}

export interface MechanicDef {
  name: string;
  description: string;
  rules: string[];
}

export class PDaCParser {
  private tokens: string[] = [];
  private current = 0;

  parse(source: string): ASTNode[] {
    // Simple tokenizer (can be enhanced with proper lexer)
    this.tokens = this.tokenize(source);
    this.current = 0;
    
    const ast: ASTNode[] = [];
    
    while (!this.isAtEnd()) {
      const node = this.parseNode();
      if (node) {
        ast.push(node);
      }
    }
    
    return ast;
  }

  private tokenize(source: string): string[] {
    // Simple tokenization - can be improved with proper lexer
    return source
      .split(/\s+|(?=[{}:;=])|(?<=[{}:;=])/)
      .filter(token => token.trim().length > 0);
  }

  private parseNode(): ASTNode | null {
    if (this.match('component')) {
      return this.parseComponent();
    } else if (this.match('api')) {
      return this.parseAPI();
    } else if (this.match('flow')) {
      return this.parseFlow();
    } else if (this.match('model')) {
      return this.parseModel();
    } else if (this.match('game')) {
      return this.parseGame();
    }
    return null;
  }

  private parseComponent(): ComponentNode {
    const name = this.consume('IDENTIFIER');
    this.consume('{');
    
    const component: ComponentNode = {
      type: 'component',
      name,
    };

    while (!this.check('}')) {
      if (this.match('props')) {
        component.props = this.parseProps();
      } else if (this.match('state')) {
        component.state = this.parseState();
      } else if (this.match('shortcuts')) {
        component.shortcuts = this.parseShortcuts();
      } else if (this.match('layout')) {
        component.layout = this.parseLayout();
      } else {
        this.advance();
      }
    }

    this.consume('}');
    return component;
  }

  private parseProps(): PropDef[] {
    this.consume('{');
    const props: PropDef[] = [];
    
    while (!this.check('}')) {
      const name = this.consume('IDENTIFIER');
      this.consume(':');
      const type = this.parseType();
      let defaultValue;
      
      if (this.match('=')) {
        defaultValue = this.parseValue();
      }
      
      props.push({ name, type, defaultValue });
      this.consume(';');
    }
    
    this.consume('}');
    return props;
  }

  private parseState(): StateDef[] {
    return this.parseProps() as StateDef[];
  }

  private parseShortcuts(): ShortcutDef[] {
    this.consume('{');
    const shortcuts: ShortcutDef[] = [];
    
    while (!this.check('}')) {
      const key = this.consume('STRING');
      this.consume(':');
      const action = this.consume('IDENTIFIER');
      shortcuts.push({ key, action });
      this.consume(';');
    }
    
    this.consume('}');
    return shortcuts;
  }

  private parseLayout(): LayoutDef[] {
    this.consume('{');
    const layout: LayoutDef[] = [];
    
    while (!this.check('}')) {
      const name = this.consume('IDENTIFIER');
      this.consume(':');
      const value = this.consume('IDENTIFIER');
      layout.push({ name, value });
      this.consume(';');
    }
    
    this.consume('}');
    return layout;
  }

  private parseType(): Type {
    if (this.match('string', 'number', 'boolean', 'void')) {
      return { name: this.previous() };
    }
    
    const name = this.consume('IDENTIFIER');
    const type: Type = { name };
    
    if (this.match('[]')) {
      type.isArray = true;
    }
    
    if (this.match('?')) {
      type.isOptional = true;
    }
    
    return type;
  }

  private parseAPI(): APINode {
    const name = this.consume('IDENTIFIER');
    this.consume('{');
    
    const endpoints: EndpointDef[] = [];
    
    while (!this.check('}')) {
      if (this.match('endpoint')) {
        endpoints.push(this.parseEndpoint());
      } else {
        this.advance();
      }
    }
    
    this.consume('}');
    return { type: 'api', name, endpoints };
  }

  private parseEndpoint(): EndpointDef {
    const method = this.consume('IDENTIFIER');
    const path = this.consume('STRING');
    this.consume('{');
    
    const endpoint: EndpointDef = { method, path };
    
    if (this.match('request')) {
      endpoint.request = this.parseFields();
    }
    
    if (this.match('response')) {
      endpoint.response = this.parseFields();
    }
    
    this.consume('}');
    return endpoint;
  }

  private parseFields(): FieldDef[] {
    this.consume('{');
    const fields: FieldDef[] = [];
    
    while (!this.check('}')) {
      const name = this.consume('IDENTIFIER');
      this.consume(':');
      const type = this.parseType();
      fields.push({ name, type });
      this.consume(';');
    }
    
    this.consume('}');
    return fields;
  }

  private parseFlow(): FlowNode {
    const name = this.consume('IDENTIFIER');
    this.consume('{');
    
    const steps: StepDef[] = [];
    
    while (!this.check('}')) {
      if (this.match('step')) {
        steps.push(this.parseStep());
      } else {
        this.advance();
      }
    }
    
    this.consume('}');
    return { type: 'flow', name, steps };
  }

  private parseStep(): StepDef {
    const name = this.consume('STRING');
    this.consume('{');
    
    const step: StepDef = { name };
    
    while (!this.check('}')) {
      if (this.match('component')) {
        this.consume(':');
        step.component = this.consume('IDENTIFIER');
      } else if (this.match('action')) {
        this.consume(':');
        step.action = this.consume('IDENTIFIER');
      } else if (this.match('next')) {
        this.consume(':');
        step.next = this.consume('STRING');
      } else {
        this.advance();
      }
    }
    
    this.consume('}');
    return step;
  }

  private parseModel(): ModelNode {
    const name = this.consume('IDENTIFIER');
    this.consume('{');
    
    const fields = this.parseFields();
    
    this.consume('}');
    return { type: 'model', name, fields };
  }

  private parseGame(): GameNode {
    const name = this.consume('IDENTIFIER');
    this.consume('{');
    
    const game: GameNode = { type: 'game', name };
    
    while (!this.check('}')) {
      if (this.match('mode')) {
        if (!game.modes) game.modes = [];
        game.modes.push(this.parseGameMode());
      } else {
        this.advance();
      }
    }
    
    this.consume('}');
    return game;
  }

  private parseGameMode(): GameModeDef {
    this.consume('{');
    const mode: any = {};
    
    while (!this.check('}')) {
      const key = this.consume('IDENTIFIER');
      this.consume(':');
      const value = this.parseValue();
      mode[key] = value;
      this.consume(';');
    }
    
    this.consume('}');
    return mode as GameModeDef;
  }

  // Helper methods
  private match(...types: string[]): boolean {
    for (const type of types) {
      if (this.check(type)) {
        this.advance();
        return true;
      }
    }
    return false;
  }

  private check(type: string): boolean {
    if (this.isAtEnd()) return false;
    return this.peek() === type;
  }

  private advance(): string {
    if (!this.isAtEnd()) this.current++;
    return this.previous();
  }

  private isAtEnd(): boolean {
    return this.current >= this.tokens.length;
  }

  private peek(): string {
    return this.tokens[this.current];
  }

  private previous(): string {
    return this.tokens[this.current - 1];
  }

  private consume(type: string): string {
    if (this.check(type)) return this.advance();
    throw new Error(`Expected ${type}, got ${this.peek()}`);
  }

  private parseValue(): any {
    const token = this.peek();
    if (token.startsWith('"')) {
      return this.consume('STRING').slice(1, -1);
    }
    if (!isNaN(Number(token))) {
      return Number(this.consume('NUMBER'));
    }
    return this.consume('IDENTIFIER');
  }
}
