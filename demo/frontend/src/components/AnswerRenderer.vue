<script lang="ts">
import { defineComponent, h } from 'vue'
import { parseAnswerMarkdown, parseInlineMarkdown } from '../lib/answer-markdown.mjs'

function renderInline(text: string) {
  return parseInlineMarkdown(text).map((token, index) => {
    const key = `${token.type}-${index}`
    if (token.type === 'strong') return h('strong', { key }, token.text)
    if (token.type === 'em') return h('em', { key }, token.text)
    if (token.type === 'code') return h('code', { key }, token.text)
    if (token.type === 'link') return h('a', { key, href: token.href, target: '_blank', rel: 'noopener noreferrer' }, token.text)
    return h('span', { key }, token.text)
  })
}

export default defineComponent({
  name: 'AnswerRenderer',
  props: { content: { type: String, required: true } },
  setup(props) {
    return () => h('div', { class: 'answer-renderer' }, parseAnswerMarkdown(props.content).map((block, index) => {
      const key = `${block.type}-${index}`
      if (block.type === 'heading') return h(`h${block.level}`, { key }, renderInline(block.text))
      if (block.type === 'paragraph') return h('p', { key }, renderInline(block.text))
      if (block.type === 'quote') return h('blockquote', { key }, [h('p', renderInline(block.text))])
      if (block.type === 'rule') return h('hr', { key })
      if (block.type === 'code-block') return h('pre', { key }, [h('code', block.text)])
      if (block.type === 'list') {
        return h(block.ordered ? 'ol' : 'ul', { key }, block.items.map((item, itemIndex) => h('li', { key: `${key}-${itemIndex}` }, renderInline(item))))
      }
      if (block.type === 'table') {
        return h('div', { key, class: 'answer-table-wrap', role: 'region', 'aria-label': '回答中的表格', tabindex: 0 }, [
          h('table', [
            h('thead', [h('tr', block.headers.map((cell, cellIndex) => h('th', { key: `h-${cellIndex}`, scope: 'col' }, renderInline(cell))))]),
            h('tbody', block.rows.map((row, rowIndex) => h('tr', { key: `r-${rowIndex}` }, block.headers.map((_, cellIndex) => h('td', { key: `c-${cellIndex}` }, renderInline(row[cellIndex] ?? '')))))),
          ]),
        ])
      }
      return h('p', { key }, renderInline(''))
    }))
  },
})
</script>

<style scoped>
.answer-renderer { min-width: 0; color: inherit; font-size: 13px; line-height: 1.7; overflow-wrap: anywhere; }
.answer-renderer :deep(h1), .answer-renderer :deep(h2), .answer-renderer :deep(h3), .answer-renderer :deep(h4) { margin: 1.05em 0 .4em; color: inherit; font-size: 1.08em; font-weight: 750; line-height: 1.4; }
.answer-renderer :deep(h1:first-child), .answer-renderer :deep(h2:first-child), .answer-renderer :deep(h3:first-child), .answer-renderer :deep(h4:first-child) { margin-top: 0; }
.answer-renderer :deep(p) { margin: .3em 0 .75em; white-space: pre-wrap; }
.answer-renderer :deep(ul), .answer-renderer :deep(ol) { display: grid; gap: .35em; margin: .35em 0 .85em; padding-left: 1.35em; }
.answer-renderer :deep(li) { padding-left: .15em; }
.answer-renderer :deep(blockquote) { margin: .65em 0; padding: .45em .8em; color: #56627b; background: #f5f7fc; border-left: 3px solid #7180f7; border-radius: 0 8px 8px 0; }
.answer-renderer :deep(blockquote p) { margin: 0; }
.answer-renderer :deep(code) { padding: .1em .35em; color: #4e5acb; background: #f0f2ff; border-radius: 5px; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: .92em; }
.answer-renderer :deep(pre) { max-width: 100%; overflow: auto; margin: .65em 0; padding: 11px 12px; color: #29344a; background: #f4f6fa; border: 1px solid #e8ebf2; border-radius: 9px; font-size: 12px; line-height: 1.55; white-space: pre; }
.answer-renderer :deep(pre code) { padding: 0; color: inherit; background: transparent; }
.answer-renderer :deep(a) { color: #4d5fe0; text-decoration: underline; text-underline-offset: 2px; }
.answer-renderer :deep(hr) { margin: .8em 0; border: 0; border-top: 1px solid #e5e9f2; }
.answer-table-wrap { max-width: 100%; overflow-x: auto; margin: .65em 0; border: 1px solid #e7eaf2; border-radius: 9px; overscroll-behavior-x: contain; }
.answer-renderer :deep(table) { width: 100%; min-width: 320px; border-collapse: collapse; font-size: 12px; }
.answer-renderer :deep(th), .answer-renderer :deep(td) { padding: 8px 10px; border-bottom: 1px solid #eceef4; text-align: left; vertical-align: top; }
.answer-renderer :deep(th) { color: #485570; background: #f7f8fc; font-weight: 750; }
.answer-renderer :deep(tr:last-child td) { border-bottom: 0; }
@media (max-width: 760px) {
  .answer-renderer { font-size: 13px; }
  .answer-renderer :deep(th), .answer-renderer :deep(td) { padding: 7px 8px; }
}
@media (prefers-reduced-motion: reduce) {
  .answer-table-wrap { scroll-behavior: auto; }
}
</style>
