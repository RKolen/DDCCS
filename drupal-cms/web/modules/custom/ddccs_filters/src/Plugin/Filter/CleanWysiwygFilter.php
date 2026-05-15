<?php

declare(strict_types=1);

namespace Drupal\ddccs_filters\Plugin\Filter;

use Drupal\filter\FilterProcessResult;
use Drupal\filter\Plugin\FilterBase;

/**
 * Cleans CKEditor line-wrap br artefacts from WYSIWYG body output.
 *
 * CKEditor inserts a <br> for every soft line-wrap inside the editor, plus
 * a &nbsp; immediately before each one as padding. These are visual artefacts
 * with no semantic meaning and must be stripped before serving HTML.
 *
 * Pipeline:
 *  1. Split paragraphs on double <br> (intentional paragraph breaks)
 *  2. Strip leading / trailing <br> from every <p>
 *  3. Replace remaining single <br> with a regular space
 *  4. Replace &nbsp; padding with a regular space
 *  5. Collapse runs of whitespace to one space
 *  6. Remove paragraphs that are now empty or whitespace-only
 *
 * @Filter(
 *   id = "ddccs_clean_wysiwyg",
 *   title = @Translation("Clean WYSIWYG br artefacts"),
 *   description = @Translation("Strips CKEditor line-wrap br and nbsp artefacts from body fields."),
 *   type = Drupal\filter\Plugin\FilterInterface::TYPE_TRANSFORM_IRREVERSIBLE,
 *   weight = 10,
 * )
 */
class CleanWysiwygFilter extends FilterBase {

  /**
   * {@inheritdoc}
   */
  public function process($text, $langcode) {
    return new FilterProcessResult($this->clean((string) $text));
  }

  /**
   * Runs the full cleanup pipeline on raw HTML.
   */
  protected function clean(string $html): string {
    if (trim($html) === '') {
      return $html;
    }

    $doc = new \DOMDocument('1.0', 'UTF-8');
    @$doc->loadHTML(
      '<html><head><meta charset="UTF-8"/></head><body>' . $html . '</body></html>',
      LIBXML_HTML_NOIMPLIED | LIBXML_HTML_NODEFDTD,
    );

    $body = $doc->getElementsByTagName('body')->item(0);
    if (!$body instanceof \DOMElement) {
      return $html;
    }

    // 1. Split on double <br>.
    $this->splitDoubleBr($doc, $body);

    // 2. Trim leading / trailing <br> from each <p> and heading.
    $this->trimBrEdges($body);

    // 3. Replace remaining <br> inside <p> and headings with a space.
    $this->replaceSingleBr($doc, $body);

    // 4 & 5. Replace &nbsp; padding and collapse whitespace in text nodes.
    $this->cleanTextNodes($doc, $body);

    // 6. Remove empty paragraphs.
    $this->removeEmptyParagraphs($body);

    $output = '';
    foreach ($body->childNodes as $child) {
      $output .= $doc->saveHTML($child);
    }

    return $output;
  }

  /**
   * Splits paragraphs containing double <br> into two separate <p> elements.
   */
  protected function splitDoubleBr(\DOMDocument $doc, \DOMElement $parent): void {
    $paragraphs = iterator_to_array($parent->getElementsByTagName('p'));
    foreach ($paragraphs as $p) {
      $children = iterator_to_array($p->childNodes);
      for ($i = 0; $i < count($children) - 1; $i++) {
        $cur  = $children[$i];
        $next = $children[$i + 1];

        if (!$this->isBr($cur)) {
          continue;
        }

        if ($this->isBr($next)) {
          $skip = 2;
        }
        elseif ($this->isWhitespace($next) && isset($children[$i + 2]) && $this->isBr($children[$i + 2])) {
          $skip = 3;
        }
        else {
          continue;
        }

        $pBefore = $doc->createElement('p');
        foreach (array_slice($children, 0, $i) as $node) {
          $pBefore->appendChild($node->cloneNode(TRUE));
        }

        $pAfter = $doc->createElement('p');
        foreach (array_slice($children, $i + $skip) as $node) {
          $pAfter->appendChild($node->cloneNode(TRUE));
        }

        $parentNode = $p->parentNode;
        if ($parentNode !== NULL) {
          $parentNode->insertBefore($pBefore, $p);
          $parentNode->insertBefore($pAfter, $p);
          $parentNode->removeChild($p);
        }

        $this->splitDoubleBr($doc, $pBefore);
        $this->splitDoubleBr($doc, $pAfter);
        break;
      }
    }
  }

  /**
   * Removes leading and trailing <br> elements from <p> and heading elements.
   */
  protected function trimBrEdges(\DOMElement $parent): void {
    $tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'];
    foreach ($tags as $tag) {
      foreach (iterator_to_array($parent->getElementsByTagName($tag)) as $el) {
        while ($el->firstChild instanceof \DOMNode && $this->isBr($el->firstChild)) {
          $el->removeChild($el->firstChild);
        }
        while ($el->lastChild instanceof \DOMNode && $this->isBr($el->lastChild)) {
          $el->removeChild($el->lastChild);
        }
      }
    }
  }

  /**
   * Replaces remaining single <br> inside <p> and headings with a space.
   */
  protected function replaceSingleBr(\DOMDocument $doc, \DOMElement $parent): void {
    $tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'];
    foreach ($tags as $tag) {
      foreach (iterator_to_array($parent->getElementsByTagName($tag)) as $el) {
        foreach (iterator_to_array($el->getElementsByTagName('br')) as $br) {
          $br->parentNode?->replaceChild($doc->createTextNode(' '), $br);
        }
      }
    }
  }

  /**
   * Replaces &nbsp; used as line-wrap padding and collapses whitespace runs.
   */
  protected function cleanTextNodes(\DOMDocument $doc, \DOMElement $parent): void {
    $xpath = new \DOMXPath($doc);
    foreach (iterator_to_array($xpath->query('//p//text()', $parent)) as $textNode) {
      $text = $textNode->nodeValue ?? '';
      // Non-breaking space → regular space.
      $text = str_replace("\u{00A0}", ' ', $text);
      // Collapse multiple spaces to one.
      $text = preg_replace('/ {2,}/', ' ', $text) ?? $text;
      $textNode->nodeValue = $text;
    }
  }

  /**
   * Removes paragraphs whose text content is empty or whitespace only.
   */
  protected function removeEmptyParagraphs(\DOMElement $parent): void {
    foreach (iterator_to_array($parent->getElementsByTagName('p')) as $p) {
      $text = str_replace("\u{00A0}", '', trim($p->textContent ?? ''));
      if ($text === '') {
        $p->parentNode?->removeChild($p);
      }
    }
  }

  /**
   * Returns TRUE if the node is a <br> element.
   */
  protected function isBr(\DOMNode $node): bool {
    return $node->nodeType === XML_ELEMENT_NODE
      && strtolower($node->nodeName) === 'br';
  }

  /**
   * Returns TRUE if the node is a text node containing only whitespace.
   */
  protected function isWhitespace(\DOMNode $node): bool {
    return $node->nodeType === XML_TEXT_NODE
      && trim($node->nodeValue ?? '') === '';
  }

}
