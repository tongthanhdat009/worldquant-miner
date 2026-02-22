/**
 * PDaC Code Generator
 * Generates code from PDaC AST
 */

import {
  ASTNode,
  ComponentNode,
  APINode,
  FlowNode,
  ModelNode,
  GameNode,
} from './parser';

export interface GeneratorOptions {
  target: 'react' | 'vue' | 'angular' | 'nestjs' | 'typescript';
  outputDir: string;
  format?: boolean;
}

export class CodeGenerator {
  constructor(private options: GeneratorOptions) {}

  generate(ast: ASTNode[]): Map<string, string> {
    const files = new Map<string, string>();

    for (const node of ast) {
      switch (node.type) {
        case 'component':
          if (this.options.target === 'react') {
            files.set(
              `${node.name}.tsx`,
              this.generateReactComponent(node as ComponentNode)
            );
          }
          break;
        case 'api':
          if (this.options.target === 'nestjs') {
            files.set(
              `${node.name}.controller.ts`,
              this.generateNestJSController(node as APINode)
            );
          }
          break;
        case 'model':
          files.set(
            `${node.name}.ts`,
            this.generateTypeScriptModel(node as ModelNode)
          );
          break;
        case 'game':
          files.set(
            `${node.name}.ts`,
            this.generateGameConfig(node as GameNode)
          );
          break;
      }
    }

    return files;
  }

  private generateReactComponent(component: ComponentNode): string {
    const props = component.props || [];
    const state = component.state || [];
    const shortcuts = component.shortcuts || [];

    const propsInterface = props
      .map((p) => `  ${p.name}${p.type.isOptional ? '?' : ''}: ${this.typeToTS(p.type)}`)
      .join('\n');

    const stateHooks = state
      .map((s) => {
        const defaultValue = s.defaultValue !== undefined 
          ? ` = ${JSON.stringify(s.defaultValue)}`
          : '';
        return `  const [${s.name}, set${this.capitalize(s.name)}] = useState<${this.typeToTS(s.type)}>(${defaultValue});`;
      })
      .join('\n');

    const shortcutHandlers = shortcuts
      .map((s) => {
        return `    "${s.key}": () => {
      ${s.action}();
    },`;
      })
      .join('\n');

    return `import { useState, useEffect } from 'react';
import { useRTSShortcuts } from '@/hooks/useRTSShortcuts';

interface ${component.name}Props {
${propsInterface}
}

export default function ${component.name}({ ${props.map(p => p.name).join(', ')} }: ${component.name}Props) {
${stateHooks}

  const { registerShortcut, unregisterShortcut } = useRTSShortcuts();

  useEffect(() => {
    const shortcuts = {
${shortcutHandlers}
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
    <div className="${component.name.toLowerCase()}">
      {/* Generated from PDaC */}
    </div>
  );
}
`;
  }

  private generateNestJSController(api: APINode): string {
    const endpoints = api.endpoints
      .map((endpoint) => {
        const requestType = endpoint.request
          ? this.generateRequestType(endpoint.request)
          : 'void';
        const responseType = endpoint.response
          ? this.generateResponseType(endpoint.response)
          : 'void';

        return `
  @${endpoint.method.toUpperCase()}('${endpoint.path}')
  async ${this.endpointToMethodName(endpoint)}(
    @Body() body: ${requestType}
  ): Promise<${responseType}> {
    // Generated from PDaC
    throw new Error('Not implemented');
  }`;
      })
      .join('\n');

    return `import { Controller, ${api.endpoints.some(e => e.request) ? 'Body, ' : ''}${api.endpoints.some(e => e.method === 'GET') ? 'Get, ' : ''}${api.endpoints.some(e => e.method === 'POST') ? 'Post, ' : ''} } from '@nestjs/common';

@Controller('${api.name.toLowerCase()}')
export class ${api.name}Controller {
${endpoints}
}
`;
  }

  private generateTypeScriptModel(model: ModelNode): string {
    const fields = model.fields
      .map((f) => {
        const optional = f.type.isOptional ? '?' : '';
        return `  ${f.name}${optional}: ${this.typeToTS(f.type)};`;
      })
      .join('\n');

    return `export interface ${model.name} {
${fields}
}
`;
  }

  private generateGameConfig(game: GameNode): string {
    const modes = game.modes || [];
    const modesCode = modes
      .map((mode) => {
        return `  ${mode.id}: {
    name: '${mode.name}',
    type: '${mode.type}',
    players: ${mode.players},
    duration: ${mode.duration},
    initialCapital: ${mode.initialCapital},
  },`;
      })
      .join('\n');

    return `export const ${game.name}Config = {
${modesCode}
};
`;
  }

  private typeToTS(type: any): string {
    let tsType = type.name;
    
    if (type.isArray) {
      tsType = `${tsType}[]`;
    }
    
    if (type.isOptional) {
      tsType = `${tsType} | undefined`;
    }
    
    return tsType;
  }

  private generateRequestType(fields: any[]): string {
    return `{ ${fields.map(f => `${f.name}: ${this.typeToTS(f.type)}`).join('; ')} }`;
  }

  private generateResponseType(fields: any[]): string {
    return `{ ${fields.map(f => `${f.name}: ${this.typeToTS(f.type)}`).join('; ')} }`;
  }

  private endpointToMethodName(endpoint: any): string {
    const pathParts = endpoint.path.split('/').filter((p: string) => p && !p.startsWith(':'));
    return pathParts.map((p: string) => this.capitalize(p)).join('') || 'handle';
  }

  private capitalize(str: string): string {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }
}
