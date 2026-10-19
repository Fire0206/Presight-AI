import assert from 'node:assert/strict'
import test from 'node:test'
import { parseAnswerMarkdown, parseInlineMarkdown } from '../demo/frontend/src/lib/answer-markdown.mjs'

test('parses common structured answer blocks', () => {
  const blocks = parseAnswerMarkdown('## 结论\n\n先看 **数据时点**。\n\n- 净值\n- 估值\n\n| 项目 | 数值 |\n| --- | ---: |\n| 基金 | 1.2 |\n\n> 示例资料\n\n```text\nhello\n```\n\n---')

  assert.deepEqual(blocks.map((block) => block.type), ['heading', 'paragraph', 'list', 'table', 'quote', 'code-block', 'rule'])
  assert.equal(blocks[1].text, '先看 **数据时点**。')
  assert.deepEqual(blocks[2].items, ['净值', '估值'])
  assert.deepEqual(blocks[3].headers, ['项目', '数值'])
  assert.deepEqual(blocks[3].rows, [['基金', '1.2']])
  assert.equal(blocks[5].text, 'hello')
})

test('keeps raw HTML as text and only allows absolute http(s) links', () => {
  const inline = parseInlineMarkdown('<script>alert(1)</script> [安全链接](https://example.com/a) [危险链接](javascript:alert(1))')
  const safeLink = inline.find((token) => token.type === 'link')

  assert.ok(inline.some((token) => token.type === 'text' && token.text.includes('<script>')))
  assert.equal(safeLink?.href, 'https://example.com/a')
  assert.ok(inline.some((token) => token.type === 'text' && token.text.includes('[危险链接]')))
})
