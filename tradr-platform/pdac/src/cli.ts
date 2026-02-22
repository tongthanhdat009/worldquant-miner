#!/usr/bin/env node

import { Command } from 'commander';
import * as fs from 'fs-extra';
import * as path from 'path';
import chalk from 'chalk';
import { PDaCParser } from './parser';
import { CodeGenerator } from './generator';

const program = new Command();

program
  .name('pdac')
  .description('Product Design as Code - Spec-driven development')
  .version('1.0.0');

program
  .command('compile')
  .description('Compile PDaC files to code')
  .argument('<input>', 'PDaC file or directory')
  .option('-t, --target <target>', 'Target framework', 'react')
  .option('-o, --output <dir>', 'Output directory', 'generated')
  .action(async (input, options) => {
    try {
      console.log(chalk.blue('🔨 Compiling PDaC...'));

      const inputPath = path.resolve(input);
      const outputPath = path.resolve(options.output);

      // Read PDaC file
      const source = await fs.readFile(inputPath, 'utf-8');
      
      // Parse
      const parser = new PDaCParser();
      const ast = parser.parse(source);
      
      console.log(chalk.green(`✓ Parsed ${ast.length} definitions`));

      // Generate code
      const generator = new CodeGenerator({
        target: options.target as any,
        outputDir: outputPath,
      });

      const files = generator.generate(ast);
      
      // Write files
      await fs.ensureDir(outputPath);
      for (const [filename, content] of files) {
        const filePath = path.join(outputPath, filename);
        await fs.writeFile(filePath, content);
        console.log(chalk.green(`✓ Generated ${filename}`));
      }

      console.log(chalk.blue(`\n✨ Generated ${files.size} files in ${outputPath}`));
    } catch (error: any) {
      console.error(chalk.red(`❌ Error: ${error.message}`));
      process.exit(1);
    }
  });

program
  .command('validate')
  .description('Validate implementation against PDaC spec')
  .argument('<spec>', 'PDaC specification file')
  .argument('<implementation>', 'Implementation directory')
  .action(async (spec, impl) => {
    console.log(chalk.blue('🔍 Validating implementation...'));
    // TODO: Implement validation
    console.log(chalk.yellow('⚠ Validation not yet implemented'));
  });

program
  .command('docs')
  .description('Generate documentation from PDaC spec')
  .argument('<spec>', 'PDaC specification file')
  .option('-o, --output <dir>', 'Output directory', 'docs')
  .action(async (spec, options) => {
    console.log(chalk.blue('📚 Generating documentation...'));
    // TODO: Implement docs generation
    console.log(chalk.yellow('⚠ Documentation generation not yet implemented'));
  });

program.parse();
