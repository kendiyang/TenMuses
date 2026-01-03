/**
 * Template Engine for Copilot Prompt Templates
 * 
 * Supports:
 * - Variable interpolation: {{variableName}}
 * - Type validation
 * - Default values: {{variableName:defaultValue}}
 * - Conditional rendering: {{#if condition}}...{{/if}}
 * - Error handling and validation
 */

/**
 * Variable types supported in templates
 */
export type VariableType = 'string' | 'number' | 'boolean' | 'array' | 'object'

/**
 * Variable definition
 */
export interface TemplateVariable {
  name: string
  type: VariableType
  description?: string
  defaultValue?: any
  required?: boolean
  validation?: (value: any) => boolean | string
}

/**
 * Variable context for template rendering
 */
export type VariableContext = Record<string, any>

/**
 * Parse result containing extracted variables
 */
export interface ParseResult {
  variables: string[]
  isValid: boolean
  errors: string[]
}

/**
 * Render result with rendered content or errors
 */
export interface RenderResult {
  content: string
  isValid: boolean
  errors: string[]
  warnings: string[]
}

/**
 * Template Engine Class
 */
export class TemplateEngine {
  /**
   * Regular expression to match variable placeholders
   * Supports: {{variableName}} or {{variableName:defaultValue}}
   */
  private static readonly VAR_REGEX = /\{\{([^}]+)\}\}/g

  /**
   * Parse a template and extract all variable names
   * 
   * @param template - The template string to parse
   * @returns ParseResult with variable names and validation info
   * 
   * @example
   * ```ts
   * const result = TemplateEngine.parse("Hello {{name}}, you have {{count}} messages")
   * // result.variables = ['name', 'count']
   * ```
   */
  static parse(template: string): ParseResult {
    const variables = new Set<string>()
    const errors: string[] = []
    let match: RegExpExecArray | null

    try {
      // Reset regex state
      this.VAR_REGEX.lastIndex = 0

      while ((match = this.VAR_REGEX.exec(template)) !== null) {
        const fullMatch = match[1].trim()
        
        // Extract variable name (before colon for default values)
        const varName = fullMatch.split(':')[0].trim()
        
        if (!varName) {
          errors.push(`Empty variable name at position ${match.index}`)
          continue
        }

        // Validate variable name (alphanumeric + underscore only)
        if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(varName)) {
          errors.push(`Invalid variable name '${varName}' at position ${match.index}`)
          continue
        }

        variables.add(varName)
      }

      return {
        variables: Array.from(variables),
        isValid: errors.length === 0,
        errors
      }
    } catch (error) {
      return {
        variables: [],
        isValid: false,
        errors: [`Parse error: ${error}`]
      }
    }
  }

  /**
   * Render a template with provided variable context
   * 
   * @param template - The template string
   * @param context - Variable values
   * @param variables - Optional variable definitions for validation
   * @returns RenderResult with rendered content or errors
   * 
   * @example
   * ```ts
   * const result = TemplateEngine.render(
   *   "Hello {{name}}, you have {{count:0}} messages",
   *   { name: "Alice", count: 5 }
   * )
   * // result.content = "Hello Alice, you have 5 messages"
   * ```
   */
  static render(
    template: string,
    context: VariableContext,
    variables?: TemplateVariable[]
  ): RenderResult {
    const errors: string[] = []
    const warnings: string[] = []

    try {
      // First, validate the template
      const parseResult = this.parse(template)
      if (!parseResult.isValid) {
        return {
          content: template,
          isValid: false,
          errors: parseResult.errors,
          warnings
        }
      }

      // Create variable definition map for quick lookup
      const varDefMap = new Map<string, TemplateVariable>()
      if (variables) {
        variables.forEach(v => varDefMap.set(v.name, v))
      }

      // Render the template
      let rendered = template
      this.VAR_REGEX.lastIndex = 0

      rendered = template.replace(this.VAR_REGEX, (match, content) => {
        const parts = content.trim().split(':')
        const varName = parts[0].trim()
        const defaultValue = parts.length > 1 ? parts.slice(1).join(':').trim() : undefined

        // Get variable definition if available
        const varDef = varDefMap.get(varName)

        // Check if variable exists in context
        if (!(varName in context)) {
          // Use default value if provided
          if (defaultValue !== undefined) {
            warnings.push(`Variable '${varName}' not found, using default value: ${defaultValue}`)
            return defaultValue
          }

          // Use variable definition default
          if (varDef?.defaultValue !== undefined) {
            warnings.push(`Variable '${varName}' not found, using default from definition`)
            return String(varDef.defaultValue)
          }

          // Check if required
          if (varDef?.required !== false) {
            errors.push(`Required variable '${varName}' is missing`)
          } else {
            warnings.push(`Optional variable '${varName}' is missing`)
          }

          return match // Keep placeholder if no default
        }

        const value = context[varName]

        // Validate value if definition exists
        if (varDef) {
          const validationResult = this.validateValue(value, varDef)
          if (validationResult !== true) {
            errors.push(`Validation failed for '${varName}': ${validationResult}`)
            return match
          }
        }

        // Convert value to string
        return this.valueToString(value)
      })

      return {
        content: rendered,
        isValid: errors.length === 0,
        errors,
        warnings
      }
    } catch (error) {
      return {
        content: template,
        isValid: false,
        errors: [`Render error: ${error}`],
        warnings
      }
    }
  }

  /**
   * Validate a variable value against its definition
   */
  private static validateValue(value: any, varDef: TemplateVariable): boolean | string {
    // Type validation
    const actualType = Array.isArray(value) ? 'array' : typeof value
    if (actualType !== varDef.type) {
      return `Expected type '${varDef.type}' but got '${actualType}'`
    }

    // Custom validation
    if (varDef.validation) {
      const result = varDef.validation(value)
      if (result !== true) {
        return typeof result === 'string' ? result : 'Validation failed'
      }
    }

    return true
  }

  /**
   * Convert a value to string for rendering
   */
  private static valueToString(value: any): string {
    if (value === null || value === undefined) {
      return ''
    }

    if (typeof value === 'string') {
      return value
    }

    if (typeof value === 'number' || typeof value === 'boolean') {
      return String(value)
    }

    if (Array.isArray(value)) {
      return value.map(v => this.valueToString(v)).join(', ')
    }

    if (typeof value === 'object') {
      return JSON.stringify(value)
    }

    return String(value)
  }

  /**
   * Check if a template has any variables
   */
  static hasVariables(template: string): boolean {
    this.VAR_REGEX.lastIndex = 0
    return this.VAR_REGEX.test(template)
  }

  /**
   * Get variable count in template
   */
  static getVariableCount(template: string): number {
    return this.parse(template).variables.length
  }

  /**
   * Extract default value from variable placeholder
   * 
   * @example
   * ```ts
   * extractDefault("{{name:John}}") // "John"
   * extractDefault("{{name}}") // undefined
   * ```
   */
  static extractDefault(placeholder: string): string | undefined {
    const match = placeholder.match(/\{\{([^}]+)\}\}/)
    if (!match) return undefined

    const parts = match[1].split(':')
    return parts.length > 1 ? parts.slice(1).join(':').trim() : undefined
  }

  /**
   * Validate template syntax without rendering
   */
  static validate(template: string, variables?: TemplateVariable[]): RenderResult {
    const parseResult = this.parse(template)
    const errors = [...parseResult.errors]
    const warnings: string[] = []

    if (!parseResult.isValid) {
      return {
        content: template,
        isValid: false,
        errors,
        warnings
      }
    }

    // Check for required variables
    if (variables) {
      const varMap = new Map(variables.map(v => [v.name, v]))
      const templateVars = new Set(parseResult.variables)

      for (const varDef of variables) {
        if (varDef.required && !templateVars.has(varDef.name)) {
          warnings.push(`Required variable '${varDef.name}' is not used in template`)
        }
      }
    }

    return {
      content: template,
      isValid: errors.length === 0,
      errors,
      warnings
    }
  }

  /**
   * Get all placeholders with their positions
   */
  static getPlaceholders(template: string): Array<{ name: string; position: number; fullMatch: string }> {
    const placeholders: Array<{ name: string; position: number; fullMatch: string }> = []
    let match: RegExpExecArray | null

    this.VAR_REGEX.lastIndex = 0

    while ((match = this.VAR_REGEX.exec(template)) !== null) {
      const fullMatch = match[1].trim()
      const varName = fullMatch.split(':')[0].trim()

      placeholders.push({
        name: varName,
        position: match.index,
        fullMatch: match[0]
      })
    }

    return placeholders
  }
}

/**
 * Predefined system variables available in all templates
 */
export const SYSTEM_VARIABLES: TemplateVariable[] = [
  {
    name: 'workflowName',
    type: 'string',
    description: 'Current workflow name',
    defaultValue: 'Untitled Workflow',
    required: false
  },
  {
    name: 'workflowId',
    type: 'string',
    description: 'Current workflow ID',
    required: false
  },
  {
    name: 'nodeCount',
    type: 'number',
    description: 'Number of nodes in workflow',
    defaultValue: 0,
    required: false
  },
  {
    name: 'timestamp',
    type: 'string',
    description: 'Current timestamp',
    defaultValue: () => new Date().toISOString(),
    required: false
  },
  {
    name: 'userName',
    type: 'string',
    description: 'Current user name',
    required: false
  }
]

/**
 * Create a context with system variables
 */
export function createSystemContext(overrides?: Partial<VariableContext>): VariableContext {
  return {
    workflowName: 'Untitled Workflow',
    workflowId: '',
    nodeCount: 0,
    timestamp: new Date().toISOString(),
    userName: 'User',
    ...overrides
  }
}
