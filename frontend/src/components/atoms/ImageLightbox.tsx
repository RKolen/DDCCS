import * as React from 'react';
import { createPortal } from 'react-dom';

interface ImageLightboxProps {
  src:     string;
  alt:     string;
  onClose: () => void;
}

/** Zoom limits and steps. Past native size nothing new appears, but small
 *  details - a face in a crowd scene - are far easier to judge magnified. */
const MIN_ZOOM = 1;
const MAX_ZOOM = 8;
const WHEEL_STEP = 1.2;
const DOUBLE_CLICK_ZOOM = 3;

interface View {
  zoom: number;
  x:    number;
  y:    number;
}

const FIT: View = { zoom: 1, x: 0, y: 0 };

/**
 * Full-screen image viewer. Scroll zooms about the cursor, dragging pans,
 * double-click toggles between fit and 3x, `0` resets, Escape closes.
 *
 * Portalled to <body>: a transformed ancestor becomes the containing block
 * for `position: fixed`, and the story image dialog is centred with one, so
 * rendered in place the backdrop shrank to the 420px dialog and clipped the
 * zoomed image.
 */
export function ImageLightbox({ src, alt, onClose }: ImageLightboxProps): React.ReactElement {
  const [view, setView] = React.useState<View>(FIT);
  const image = React.useRef<HTMLImageElement | null>(null);
  const backdrop = React.useRef<HTMLDivElement | null>(null);
  const pan = React.useRef<{ x: number; y: number } | null>(null);
  // Set once a press has moved, so releasing it is a pan and not a click.
  const dragged = React.useRef(false);

  /* Keep the image point under (clientX, clientY) fixed while the zoom
     changes. The transform origin is the image's top-left, so its laid-out
     position is the current box minus the translation. */
  const zoomAt = React.useCallback((next: number, clientX: number, clientY: number) => {
    const box = image.current?.getBoundingClientRect();
    if (box == null) return;
    setView(current => {
      const zoom = Math.min(Math.max(next, MIN_ZOOM), MAX_ZOOM);
      if (zoom === MIN_ZOOM) return FIT;
      const left = box.left - current.x;
      const top = box.top - current.y;
      const u = (clientX - box.left) / current.zoom;
      const v = (clientY - box.top) / current.zoom;
      return { zoom, x: clientX - left - zoom * u, y: clientY - top - zoom * v };
    });
  }, []);

  React.useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === '0') setView(FIT);
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  /* Native and non-passive: React's onWheel is passive, so it cannot stop
     the page behind the backdrop scrolling along with the zoom. */
  React.useEffect(() => {
    const node = backdrop.current;
    if (node == null) return undefined;
    const handler = (e: WheelEvent) => {
      e.preventDefault();
      const zoom = view.zoom * (e.deltaY < 0 ? WHEEL_STEP : 1 / WHEEL_STEP);
      zoomAt(zoom, e.clientX, e.clientY);
    };
    node.addEventListener('wheel', handler, { passive: false });
    return () => node.removeEventListener('wheel', handler);
  }, [view.zoom, zoomAt]);

  const zoomed = view.zoom > MIN_ZOOM;

  return createPortal(
    /* Zoomed, the image no longer covers the backdrop, so a pan that started
       on empty space used to land as a click and close the viewer. Panning
       works from anywhere then, and only Close or Escape ends it. */
    <div
      ref={backdrop}
      className={`lightbox-backdrop${zoomed ? ' lightbox-backdrop--zoomed' : ''}`}
      onClick={() => {
        if (dragged.current) { dragged.current = false; return; }
        if (!zoomed) onClose();
      }}
      onPointerDown={e => {
        if (!zoomed) return;
        e.currentTarget.setPointerCapture(e.pointerId);
        dragged.current = false;
        pan.current = { x: e.clientX - view.x, y: e.clientY - view.y };
      }}
      onPointerMove={e => {
        const from = pan.current;
        if (from == null) return;
        dragged.current = true;
        setView(current => ({ ...current, x: e.clientX - from.x, y: e.clientY - from.y }));
      }}
      onPointerUp={() => { pan.current = null; }}
    >
      <img
        ref={image}
        className={`lightbox-img${zoomed ? ' lightbox-img--zoomed' : ''}`}
        src={src}
        alt={alt}
        draggable={false}
        style={zoomed
          ? { transform: `translate(${view.x}px, ${view.y}px) scale(${view.zoom})` }
          : undefined}
        onClick={e => { if (!zoomed) e.stopPropagation(); }}
        onDoubleClick={e => {
          if (zoomed) setView(FIT);
          else zoomAt(DOUBLE_CLICK_ZOOM, e.clientX, e.clientY);
        }}
      />
      <button
        type="button"
        className="lightbox-close"
        onPointerDown={e => e.stopPropagation()}
        onClick={e => { e.stopPropagation(); onClose(); }}
      >
        Close
      </button>
      <p className="lightbox-hint">
        {zoomed
          ? `${view.zoom.toFixed(1)}x - drag anywhere to pan, 0 to reset, Esc or Close to exit`
          : 'Scroll or double-click to zoom, Esc to close'}
      </p>
    </div>,
    document.body,
  );
}
