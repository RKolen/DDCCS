/**
 * Sanitises CKEditor/WYSIWYG HTML before rendering with dangerouslySetInnerHTML.
 *
 * CKEditor 5 in Drupal inserts <br> tags for EVERY soft line-wrap inside the
 * editor, plus &nbsp; characters immediately before each <br> as padding.
 * Neither is semantically meaningful — they are display artefacts that must be
 * stripped and joined as plain text.
 *
 * Pipeline (order matters):
 *  1. Split paragraphs on double <br> (intentional paragraph breaks)
 *  2. Strip leading / trailing <br> from every <p>
 *  3. Replace remaining single <br> inside <p> with a regular space
 *  4. Remove &nbsp; that appear immediately before or after a space (padding)
 *  5. Collapse multiple internal spaces to one
 *  6. Remove paragraphs that are now empty or whitespace-only
 */

export function cleanHtml(raw: string | null | undefined): string {
  if (!raw) return '';
  if (typeof document === 'undefined') return cleanHtmlRegex(raw);
  return cleanHtmlDom(raw);
}

// ── DOM-based (browser) ───────────────────────────────────────────────────────

function cleanHtmlDom(raw: string): string {
  const doc  = new DOMParser().parseFromString(raw, 'text/html');
  const body = doc.body;

  // 1. Split paragraphs that contain two consecutive <br> elements.
  body.querySelectorAll('p').forEach(p => splitOnDoubleBr(p, doc));

  // 2. Strip leading / trailing <br> from every paragraph.
  body.querySelectorAll('p').forEach(p => trimBrEdges(p));

  // 3. Replace every remaining <br> inside <p> with a regular space.
  body.querySelectorAll('p br').forEach(br => {
    br.replaceWith(doc.createTextNode(' '));
  });

  // 3b. Trim leading/trailing <br> from headings and replace inner ones with space.
  body.querySelectorAll('h1,h2,h3,h4,h5,h6').forEach(h => {
    while (h.firstChild && isBr(h.firstChild)) h.firstChild.remove();
    while (h.lastChild  && isBr(h.lastChild))  h.lastChild.remove();
    h.querySelectorAll('br').forEach(br => {
      br.replaceWith(doc.createTextNode(' '));
    });
  });

  // 4. Walk all text nodes inside the body and clean up &nbsp; padding.
  walkTextNodes(body, node => {
    // Non-breaking space (U+00A0) used as padding → regular space.
    // Then collapse runs of whitespace to a single space.
    node.textContent = (node.textContent ?? '')
      .replace(/ /g, ' ')
      .replace(/[ \t]{2,}/g, ' ');
  });

  // 5. Remove paragraphs that are now empty or whitespace-only.
  body.querySelectorAll('p').forEach(p => {
    if ((p.textContent ?? '').trim() === '') p.remove();
  });

  return body.innerHTML;
}

function walkTextNodes(root: Element, fn: (node: Text) => void): void {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node = walker.nextNode();
  while (node !== null) {
    fn(node as Text);
    node = walker.nextNode();
  }
}

function splitOnDoubleBr(p: Element, doc: Document): void {
  const children = Array.from(p.childNodes);

  // Find the first occurrence of two consecutive <br> elements.
  for (let i = 0; i < children.length - 1; i++) {
    const cur  = children[i];
    const next = children[i + 1];
    if (!isBr(cur)) continue;

    const isDouble = isBr(next)
      || (isWhitespace(next) && isBr(children[i + 2]));

    if (!isDouble) continue;

    const skipCount = isWhitespace(next) ? 3 : 2;
    const before    = children.slice(0, i);
    const after     = children.slice(i + skipCount);

    const pBefore = doc.createElement('p');
    before.forEach(n => pBefore.appendChild(n.cloneNode(true)));

    const pAfter = doc.createElement('p');
    after.forEach(n => pAfter.appendChild(n.cloneNode(true)));

    const parent = p.parentNode;
    if (!parent) return;

    parent.insertBefore(pBefore, p);
    parent.insertBefore(pAfter, p);
    parent.removeChild(p);

    // Recurse — more double-br may remain.
    splitOnDoubleBr(pBefore, doc);
    splitOnDoubleBr(pAfter, doc);
    return;
  }
}

function trimBrEdges(p: Element): void {
  while (p.firstChild && isBr(p.firstChild)) p.firstChild.remove();
  while (p.lastChild  && isBr(p.lastChild))  p.lastChild.remove();
  while (p.firstChild && isWhitespace(p.firstChild)) p.firstChild.remove();
  while (p.lastChild  && isWhitespace(p.lastChild))  p.lastChild.remove();
}

function isBr(node: ChildNode | undefined): boolean {
  return node?.nodeName === 'BR';
}

function isWhitespace(node: ChildNode | undefined): boolean {
  return node?.nodeType === Node.TEXT_NODE
    && (node.textContent ?? '').trim() === '';
}

// ── Regex-based (SSR / Gatsby build) ─────────────────────────────────────────

function cleanHtmlRegex(html: string): string {
  return html
    // Replace &nbsp; used as padding before <br> with nothing.
    .replace(/(&nbsp;| )\s*(<br\s*\/?>)/gi, '$2')
    // Replace &nbsp; used as padding after <br> with nothing.
    .replace(/(<br\s*\/?>)\s*(&nbsp;| )/gi, '$1')
    // Split double <br> into paragraph breaks.
    .replace(/(<br\s*\/?>\s*){2,}/gi, '</p><p>')
    // Remove empty paragraphs.
    .replace(/<p>(\s|&nbsp;| |<br\s*\/?>)*<\/p>/gi, '')
    // Strip leading <br> from paragraphs.
    .replace(/<p>\s*(<br\s*\/?>\s*)+/gi, '<p>')
    // Strip trailing <br> from paragraphs.
    .replace(/(\s*<br\s*\/?>\s*)+<\/p>/gi, '</p>')
    // Replace remaining single <br> inside paragraphs with a space.
    // (Two-pass: first mark them, then replace.)
    .replace(/<br\s*\/?>/gi, ' ')
    // Replace &nbsp; used as line-wrap padding with regular space.
    .replace(/&nbsp;/g, ' ')
    // Collapse runs of multiple spaces to one.
    .replace(/ {2,}/g, ' ');
}
