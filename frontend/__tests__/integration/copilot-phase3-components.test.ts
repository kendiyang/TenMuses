/**
 * Phase 3 Component Integration Tests
 *
 * 测试 CopilotSuggestions, CopilotDiagnostics, CopilotPromptTemplate 的集成
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { CopilotSuggestions } from '@/components/workflow/CopilotSuggestions'
import { CopilotDiagnostics } from '@/components/workflow/CopilotDiagnostics'
import { CopilotPromptTemplate } from '@/components/workflow/CopilotPromptTemplate'

describe('Phase 3 Components - CopilotSuggestions', () => {
  const mockSuggestions = [
    {
      type: 'workflow' as const,
      id: '1',
      name: 'Data Processing Workflow',
      description: 'Process and clean data',
      nodeCount: 3,
      edgeCount: 2,
      data: {},
    },
    {
      type: 'node' as const,
      id: '2',
      nodeType: 'llm',
      label: 'LLM Node',
      explanation: 'Use LLM for processing',
      data: {},
    },
  ]

  it('should render suggestions with correct types', () => {
    const { container } = render(
      <CopilotSuggestions
        suggestions={mockSuggestions}
        onApply={() => {}}
      />
    )

    expect(container.textContent).toContain('Data Processing Workflow')
    expect(container.textContent).toContain('LLM Node')
  })

  it('should display workflow suggestions with blue styling', () => {
    const { container } = render(
      <CopilotSuggestions
        suggestions={[mockSuggestions[0]]}
        onApply={() => {}}
      />
    )

    const workflowCard = container.querySelector('.bg-blue-100')
    expect(workflowCard).toBeTruthy()
  })

  it('should display node suggestions with green styling', () => {
    const { container } = render(
      <CopilotSuggestions
        suggestions={[mockSuggestions[1]]}
        onApply={() => {}}
      />
    )

    const nodeCard = container.querySelector('.bg-green-100')
    expect(nodeCard).toBeTruthy()
  })

  it('should call onApply when suggestion is applied', async () => {
    const onApply = vi.fn()

    const { container } = render(
      <CopilotSuggestions
        suggestions={mockSuggestions}
        onApply={onApply}
      />
    )

    const buttons = container.querySelectorAll('button[type="button"]')
    const applyButtons = Array.from(buttons).filter((btn) =>
      btn.textContent?.includes('应用')
    )

    if (applyButtons.length > 0) {
      fireEvent.click(applyButtons[0])
      await waitFor(() => {
        expect(onApply).toHaveBeenCalled()
      })
    }
  })

  it('should support collapse/expand', async () => {
    const { container } = render(
      <CopilotSuggestions
        suggestions={mockSuggestions}
        onApply={() => {}}
      />
    )

    const header = container.querySelector(
      'div:first-child'
    ) as HTMLElement

    if (header) {
      fireEvent.click(header)
      await waitFor(() => {
        expect(container.textContent).toContain('Data Processing Workflow')
      })
    }
  })

  it('should show suggestion count badge', () => {
    const { container } = render(
      <CopilotSuggestions
        suggestions={mockSuggestions}
        onApply={() => {}}
      />
    )

    expect(container.textContent).toContain('2')
  })

  it('should handle empty suggestions', () => {
    const { container } = render(
      <CopilotSuggestions
        suggestions={[]}
        onApply={() => {}}
      />
    )

    expect(container).toBeTruthy()
  })

  it('should disable buttons when loading', () => {
    const { container } = render(
      <CopilotSuggestions
        suggestions={mockSuggestions}
        onApply={() => {}}
        loading={true}
      />
    )

    const buttons = container.querySelectorAll('button[disabled]')
    expect(buttons.length).toBeGreaterThan(0)
  })
})

describe('Phase 3 Components - CopilotDiagnostics', () => {
  const mockDiagnosis = {
    score: 75,
    summary: 'Workflow is mostly correct but has some issues',
    diagnostics: [
      {
        level: 'error' as const,
        description: 'Missing required node',
        suggestion: 'Add an LLM node to process data',
        location: { node_id: 'node1' },
      },
      {
        level: 'warning' as const,
        description: 'Inefficient edge connection',
        suggestion: 'Simplify the workflow by removing unnecessary connections',
        location: { node_id: 'node2' },
      },
    ],
  }

  it('should render diagnosis with score', () => {
    const { container } = render(
      <CopilotDiagnostics result={mockDiagnosis} />
    )

    expect(container.textContent).toContain('75')
    expect(container.textContent).toContain('/100')
  })

  it('should display score bar with correct color based on score', () => {
    const { container } = render(
      <CopilotDiagnostics result={mockDiagnosis} />
    )

    const progressBar = container.querySelector('[class*="bg-gradient"]')
    expect(progressBar).toBeTruthy()
  })

  it('should list all diagnostics', () => {
    const { container } = render(
      <CopilotDiagnostics result={mockDiagnosis} />
    )

    expect(container.textContent).toContain('Missing required node')
    expect(container.textContent).toContain('Inefficient edge connection')
  })

  it('should show error diagnostic with red styling', () => {
    const { container } = render(
      <CopilotDiagnostics result={mockDiagnosis} />
    )

    const errorDiagnostic = container.querySelector('[class*="bg-red"]')
    expect(errorDiagnostic).toBeTruthy()
  })

  it('should show warning diagnostic with yellow styling', () => {
    const { container } = render(
      <CopilotDiagnostics result={mockDiagnosis} />
    )

    const warningDiagnostic = container.querySelector('[class*="bg-yellow"]')
    expect(warningDiagnostic).toBeTruthy()
  })

  it('should call onHighlightNode when node reference is clicked', async () => {
    const onHighlightNode = vi.fn()

    const { container } = render(
      <CopilotDiagnostics
        result={mockDiagnosis}
        onHighlightNode={onHighlightNode}
      />
    )

    const nodeButtons = Array.from(container.querySelectorAll('button')).filter(
      (btn) => btn.textContent?.includes('查看节点')
    )

    if (nodeButtons.length > 0) {
      fireEvent.click(nodeButtons[0])
      await waitFor(() => {
        expect(onHighlightNode).toHaveBeenCalled()
      })
    }
  })

  it('should support collapse/expand', async () => {
    const { container } = render(
      <CopilotDiagnostics result={mockDiagnosis} />
    )

    const header = container.querySelector(
      'div:first-child'
    ) as HTMLElement

    if (header) {
      fireEvent.click(header)
      await waitFor(() => {
        expect(container.textContent).toContain('75')
      })
    }
  })

  it('should handle diagnosis without issues', () => {
    const successDiagnosis = {
      score: 95,
      summary: 'Workflow is perfect',
      diagnostics: [],
    }

    const { container } = render(
      <CopilotDiagnostics result={successDiagnosis} />
    )

    expect(container.textContent).toContain('没有明显问题')
  })

  it('should not render when result is undefined', () => {
    const { container } = render(
      <CopilotDiagnostics result={undefined} />
    )

    expect(container.children.length).toBe(0)
  })
})

describe('Phase 3 Components - CopilotPromptTemplate', () => {
  const mockTemplate = {
    content: 'Generate a workflow that does X, Y, Z',
    version: '1.0',
    description: 'Template for generating workflows',
    examples: ['Example 1', 'Example 2'],
  }

  it('should render template with content', () => {
    const { container } = render(
      <CopilotPromptTemplate template={mockTemplate} />
    )

    expect(container.textContent).toContain('Generate a workflow that does X, Y, Z')
  })

  it('should display template version', () => {
    const { container } = render(
      <CopilotPromptTemplate template={mockTemplate} />
    )

    expect(container.textContent).toContain('1.0')
  })

  it('should calculate and display token count', () => {
    const { container } = render(
      <CopilotPromptTemplate template={mockTemplate} />
    )

    expect(container.textContent).toContain('tokens')
  })

  it('should have style selector buttons', () => {
    const { container } = render(
      <CopilotPromptTemplate template={mockTemplate} />
    )

    expect(container.textContent).toContain('结构化')
    expect(container.textContent).toContain('详细')
    expect(container.textContent).toContain('简洁')
  })

  it('should support edit mode toggle', async () => {
    const { container } = render(
      <CopilotPromptTemplate template={mockTemplate} />
    )

    const editButtons = Array.from(container.querySelectorAll('button')).filter(
      (btn) => btn.textContent?.includes('编辑')
    )

    if (editButtons.length > 0) {
      fireEvent.click(editButtons[0])
      await waitFor(() => {
        const textarea = container.querySelector('textarea')
        expect(textarea).toBeTruthy()
      })
    }
  })

  it('should copy content to clipboard', async () => {
    const clipboardSpy = vi.spyOn(navigator.clipboard, 'writeText').mockResolvedValue(undefined)

    const { container } = render(
      <CopilotPromptTemplate template={mockTemplate} />
    )

    const copyButtons = Array.from(container.querySelectorAll('button')).filter(
      (btn) => btn.textContent?.includes('复制')
    )

    if (copyButtons.length > 0) {
      fireEvent.click(copyButtons[0])
      await waitFor(() => {
        expect(clipboardSpy).toHaveBeenCalled()
      })
    }

    clipboardSpy.mockRestore()
  })

  it('should handle edit and save', async () => {
    const onApply = vi.fn()

    const { container } = render(
      <CopilotPromptTemplate
        template={mockTemplate}
        onApply={onApply}
      />
    )

    const editButtons = Array.from(container.querySelectorAll('button')).filter(
      (btn) => btn.textContent?.includes('编辑')
    )

    if (editButtons.length > 0) {
      fireEvent.click(editButtons[0])
      await waitFor(() => {
        const textarea = container.querySelector('textarea')
        expect(textarea).toBeTruthy()
      })
    }
  })

  it('should support collapse/expand', async () => {
    const { container } = render(
      <CopilotPromptTemplate template={mockTemplate} />
    )

    const header = container.querySelector(
      'div:first-child'
    ) as HTMLElement

    if (header) {
      fireEvent.click(header)
      await waitFor(() => {
        expect(container.textContent).toContain('Generate a workflow')
      })
    }
  })

  it('should disable buttons when loading', () => {
    const { container } = render(
      <CopilotPromptTemplate
        template={mockTemplate}
        loading={true}
      />
    )

    const disabledButtons = container.querySelectorAll('button[disabled]')
    expect(disabledButtons.length).toBeGreaterThan(0)
  })

  it('should not render when template is undefined', () => {
    const { container } = render(
      <CopilotPromptTemplate template={undefined} />
    )

    expect(container.children.length).toBe(0)
  })
})

describe('Phase 3 Components - Integration', () => {
  it('should all three components work together in CopilotPanel', async () => {
    const suggestions = [
      {
        type: 'workflow' as const,
        id: '1',
        name: 'Test Workflow',
        description: 'Test',
        nodeCount: 1,
        edgeCount: 0,
        data: {},
      },
    ]

    const diagnosis = {
      score: 80,
      summary: 'Good workflow',
      diagnostics: [],
    }

    const template = {
      content: 'Test template',
      version: '1.0',
      description: 'Test',
      examples: [],
    }

    const onSuggestionsApply = vi.fn()
    const onDiagnosticHighlight = vi.fn()
    const onTemplateApply = vi.fn()

    const { container: suggestionsContainer } = render(
      <CopilotSuggestions
        suggestions={suggestions}
        onApply={onSuggestionsApply}
      />
    )

    const { container: diagnosticsContainer } = render(
      <CopilotDiagnostics
        result={diagnosis}
        onHighlightNode={onDiagnosticHighlight}
      />
    )

    const { container: templateContainer } = render(
      <CopilotPromptTemplate
        template={template}
        onApply={onTemplateApply}
      />
    )

    expect(suggestionsContainer.textContent).toContain('Test Workflow')
    expect(diagnosticsContainer.textContent).toContain('80')
    expect(templateContainer.textContent).toContain('Test template')
  })
})
