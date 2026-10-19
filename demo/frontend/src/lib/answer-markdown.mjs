const headingPattern = /^\s{0,3}(#{1,4})\s+(.+?)\s*#*\s*$/
const listPattern = /^\s*(?:([-*+])\s+|(\d+)[.)]\s+)(.+)$/
const rulePattern = /^\s*(?:-{3,}|\*{3,}|_{3,})\s*$/

function cells(line) {
  return line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((cell) => cell.trim())
}

function isTableSeparator(line) {
  return /^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line)
}

function startsBlock(lines, index) {
  const line = lines[index] ?? ''
  return headingPattern.test(line) || listPattern.test(line) || /^\s*>/.test(line) || rulePattern.test(line) || /^\s*```/.test(line)
    || (index + 1 < lines.length && line.includes('|') && isTableSeparator(lines[index + 1]))
}

export function parseInlineMarkdown(input) {
  const text = String(input ?? '')
  const tokenPattern = /(\*\*[^*]+\*\*|__[^_]+__|`[^`]+`|\*[^*]+\*|_[^_]+_|\[[^\]]+\]\([^)]+\))/g
  const tokens = []
  let cursor = 0

  for (const match of text.matchAll(tokenPattern)) {
    const index = match.index ?? 0
    if (index > cursor) tokens.push({ type: 'text', text: text.slice(cursor, index) })
    const token = match[0]
    if (token.startsWith('**') || token.startsWith('__')) {
      tokens.push({ type: 'strong', text: token.slice(2, -2) })
    } else if (token.startsWith('`')) {
      tokens.push({ type: 'code', text: token.slice(1, -1) })
    } else if (token.startsWith('*') || token.startsWith('_')) {
      tokens.push({ type: 'em', text: token.slice(1, -1) })
    } else {
      const link = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(token)
      let safeUrl = ''
      try {
        const parsed = new URL(link?.[2] ?? '')
        if (parsed.protocol === 'https:' || parsed.protocol === 'http:') safeUrl = parsed.href
      } catch {
        // Invalid or relative links stay plain text.
      }
      if (link && safeUrl) tokens.push({ type: 'link', text: link[1], href: safeUrl })
      else tokens.push({ type: 'text', text: token })
    }
    cursor = index + token.length
  }
  if (cursor < text.length) tokens.push({ type: 'text', text: text.slice(cursor) })
  return tokens
}

export function parseAnswerMarkdown(markdown) {
  const lines = String(markdown ?? '').replace(/\r\n?/g, '\n').split('\n')
  const blocks = []
  let index = 0

  while (index < lines.length) {
    const line = lines[index]
    if (!line.trim()) {
      index += 1
      continue
    }

    const fence = /^\s*```\s*([\w+-]*)/.exec(line)
    if (fence) {
      const code = []
      index += 1
      while (index < lines.length && !/^\s*```\s*$/.test(lines[index])) code.push(lines[index++])
      if (index < lines.length) index += 1
      blocks.push({ type: 'code-block', language: fence[1] ?? '', text: code.join('\n') })
      continue
    }

    const heading = headingPattern.exec(line)
    if (heading) {
      blocks.push({ type: 'heading', level: heading[1].length, text: heading[2] })
      index += 1
      continue
    }

    if (rulePattern.test(line)) {
      blocks.push({ type: 'rule' })
      index += 1
      continue
    }

    if (index + 1 < lines.length && line.includes('|') && isTableSeparator(lines[index + 1])) {
      const headers = cells(line)
      index += 2
      const rows = []
      while (index < lines.length && lines[index].includes('|') && lines[index].trim()) rows.push(cells(lines[index++]))
      blocks.push({ type: 'table', headers, rows })
      continue
    }

    const listMatch = listPattern.exec(line)
    if (listMatch) {
      const ordered = Boolean(listMatch[2])
      const items = []
      while (index < lines.length) {
        const current = listPattern.exec(lines[index])
        if (!current || Boolean(current[2]) !== ordered) break
        items.push(current[3])
        index += 1
      }
      blocks.push({ type: 'list', ordered, items })
      continue
    }

    if (/^\s*>/.test(line)) {
      const quote = []
      while (index < lines.length && /^\s*>/.test(lines[index])) quote.push(lines[index++].replace(/^\s*>\s?/, ''))
      blocks.push({ type: 'quote', text: quote.join(' ') })
      continue
    }

    const paragraph = [line.trim()]
    index += 1
    while (index < lines.length && lines[index].trim() && !startsBlock(lines, index)) paragraph.push(lines[index++].trim())
    blocks.push({ type: 'paragraph', text: paragraph.join(' ') })
  }

  return blocks
}
